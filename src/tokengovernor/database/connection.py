"""Database connection and session management"""
import sqlite3
import asyncio
import aiosqlite
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
from pathlib import Path
import logging

from ..core.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and initialization"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.database.path
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize database and create tables if needed"""
        if self._initialized:
            return
        
        # Ensure database directory exists
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create tables
        async with aiosqlite.connect(self.db_path) as db:
            await self._create_tables(db)
            await self._create_indexes(db)
            await self._create_triggers(db)
            await db.commit()
        
        self._initialized = True
        logger.info(f"Database initialized at {self.db_path}")
    
    async def _create_tables(self, db: aiosqlite.Connection) -> None:
        """Create all required tables"""
        
        # Projects table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                token_budget INTEGER NOT NULL,
                priority_tier TEXT NOT NULL CHECK (priority_tier IN ('tier_1', 'tier_2')),
                owner TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
        """)
        
        # Agents table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                agent_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_active TEXT,
                FOREIGN KEY (project_id) REFERENCES projects (project_id)
            )
        """)
        
        # Tasks table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                parent_agent_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                complexity TEXT NOT NULL CHECK (complexity IN ('simple', 'complex', 'very_complex')),
                estimated_tokens INTEGER NOT NULL DEFAULT 0,
                actual_tokens INTEGER NOT NULL DEFAULT 0,
                subtask_ids TEXT, -- JSON array
                checkpoint_state TEXT NOT NULL DEFAULT 'none' CHECK (checkpoint_state IN ('none', 'requested', 'saved')),
                checkpoint_uri TEXT,
                status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'paused', 'completed', 'failed')),
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                error_message TEXT,
                FOREIGN KEY (parent_agent_id) REFERENCES agents (agent_id),
                FOREIGN KEY (project_id) REFERENCES projects (project_id)
            )
        """)
        
        # Task packages table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS task_packages (
                package_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                task_ids TEXT, -- JSON array
                estimated_tokens INTEGER NOT NULL DEFAULT 0,
                priority TEXT NOT NULL CHECK (priority IN ('tier_1', 'tier_2')),
                timeline TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects (project_id)
            )
        """)
        
        # Token usage table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS token_usage (
                usage_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                task_id TEXT,
                agent_id TEXT,
                tokens_used INTEGER NOT NULL DEFAULT 0,
                operation_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT, -- JSON object
                FOREIGN KEY (project_id) REFERENCES projects (project_id),
                FOREIGN KEY (task_id) REFERENCES tasks (task_id),
                FOREIGN KEY (agent_id) REFERENCES agents (agent_id)
            )
        """)
        
        # Checkpoints table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                checkpoint_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                checkpoint_uri TEXT NOT NULL,
                checkpoint_data TEXT, -- JSON object
                compression_used BOOLEAN NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                size_bytes INTEGER,
                FOREIGN KEY (task_id) REFERENCES tasks (task_id)
            )
        """)
        
        # Scheduler rules table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS scheduler_rules (
                rule_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                priority_tier TEXT NOT NULL CHECK (priority_tier IN ('tier_1', 'tier_2')),
                max_concurrent_tasks INTEGER NOT NULL DEFAULT 1,
                rate_limit_per_minute INTEGER NOT NULL DEFAULT 1,
                retry_attempts INTEGER NOT NULL DEFAULT 3,
                backoff_multiplier REAL NOT NULL DEFAULT 2.0,
                active BOOLEAN NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)
        
        # Workflow state table (for claude-flow coordination)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS workflow_state (
                workflow_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                agent_id TEXT,
                state_data TEXT, -- JSON object
                created_at TEXT NOT NULL,
                updated_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects (project_id),
                FOREIGN KEY (agent_id) REFERENCES agents (agent_id)
            )
        """)
    
    async def _create_indexes(self, db: aiosqlite.Connection) -> None:
        """Create performance indexes"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks (project_id)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks (created_at)",
            "CREATE INDEX IF NOT EXISTS idx_token_usage_project_id ON token_usage (project_id)",
            "CREATE INDEX IF NOT EXISTS idx_token_usage_timestamp ON token_usage (timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_agents_project_id ON agents (project_id)",
            "CREATE INDEX IF NOT EXISTS idx_agents_type ON agents (agent_type)",
            "CREATE INDEX IF NOT EXISTS idx_checkpoints_task_id ON checkpoints (task_id)",
        ]
        
        for index_sql in indexes:
            await db.execute(index_sql)
    
    async def _create_triggers(self, db: aiosqlite.Connection) -> None:
        """Create database triggers for data consistency"""
        
        # Update project updated_at timestamp
        await db.execute("""
            CREATE TRIGGER IF NOT EXISTS update_project_timestamp
            AFTER UPDATE ON projects
            FOR EACH ROW
            BEGIN
                UPDATE projects SET updated_at = datetime('now') WHERE project_id = NEW.project_id;
            END
        """)
        
        # Update workflow_state updated_at timestamp
        await db.execute("""
            CREATE TRIGGER IF NOT EXISTS update_workflow_state_timestamp
            AFTER UPDATE ON workflow_state
            FOR EACH ROW
            BEGIN
                UPDATE workflow_state SET updated_at = datetime('now') WHERE workflow_id = NEW.workflow_id;
            END
        """)
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Get a database connection"""
        if not self._initialized:
            await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            yield db


# Global database manager instance
db_manager = DatabaseManager()