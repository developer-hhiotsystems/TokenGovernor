"""Repository classes for data access"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import logging

from ..core.models import (
    Project, Agent, Task, TaskPackage, TokenUsage, 
    Checkpoint, SchedulerRule, PriorityTier, TaskStatus, TaskComplexity, CheckpointState
)
from ..database.connection import db_manager

logger = logging.getLogger(__name__)


class ProjectRepository:
    """Repository for project data operations"""
    
    async def create(self, project: Project) -> Project:
        """Create a new project"""
        async with db_manager.get_connection() as db:
            await db.execute("""
                INSERT INTO projects (
                    project_id, name, description, token_budget, 
                    priority_tier, owner, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                project.project_id,
                project.name,
                project.description,
                project.token_budget,
                project.priority_tier.value,
                project.owner,
                project.created_at.isoformat()
            ))
            await db.commit()
            logger.info(f"Created project {project.project_id}")
            return project
    
    async def get_by_id(self, project_id: str) -> Optional[Project]:
        """Get project by ID"""
        async with db_manager.get_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM projects WHERE project_id = ?",
                (project_id,)
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            return Project(
                project_id=row['project_id'],
                name=row['name'],
                description=row['description'],
                token_budget=row['token_budget'],
                priority_tier=PriorityTier(row['priority_tier']),
                owner=row['owner'],
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            )
    
    async def list_all(self) -> List[Project]:
        """List all projects"""
        async with db_manager.get_connection() as db:
            cursor = await db.execute("SELECT * FROM projects ORDER BY created_at DESC")
            rows = await cursor.fetchall()
            
            projects = []
            for row in rows:
                projects.append(Project(
                    project_id=row['project_id'],
                    name=row['name'],
                    description=row['description'],
                    token_budget=row['token_budget'],
                    priority_tier=PriorityTier(row['priority_tier']),
                    owner=row['owner'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
                ))
            
            return projects
    
    async def update(self, project: Project) -> Project:
        """Update an existing project"""
        project.updated_at = datetime.utcnow()
        
        async with db_manager.get_connection() as db:
            await db.execute("""
                UPDATE projects 
                SET name = ?, description = ?, token_budget = ?, 
                    priority_tier = ?, owner = ?, updated_at = ?
                WHERE project_id = ?
            """, (
                project.name,
                project.description,
                project.token_budget,
                project.priority_tier.value,
                project.owner,
                project.updated_at.isoformat(),
                project.project_id
            ))
            await db.commit()
            logger.info(f"Updated project {project.project_id}")
            return project
    
    async def delete(self, project_id: str) -> bool:
        """Delete a project"""
        async with db_manager.get_connection() as db:
            cursor = await db.execute(
                "DELETE FROM projects WHERE project_id = ?",
                (project_id,)
            )
            await db.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Deleted project {project_id}")
            return deleted


class TaskRepository:
    """Repository for task data operations"""
    
    async def create(self, task: Task) -> Task:
        """Create a new task"""
        async with db_manager.get_connection() as db:
            await db.execute("""
                INSERT INTO tasks (
                    task_id, parent_agent_id, project_id, name, description,
                    complexity, estimated_tokens, actual_tokens, subtask_ids,
                    checkpoint_state, checkpoint_uri, status, created_at,
                    started_at, completed_at, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.task_id,
                task.parent_agent_id,
                task.project_id,
                task.name,
                task.description,
                task.complexity.value,
                task.estimated_tokens,
                task.actual_tokens,
                json.dumps(task.subtask_ids),
                task.checkpoint_state.value,
                task.checkpoint_uri,
                task.status.value,
                task.created_at.isoformat(),
                task.started_at.isoformat() if task.started_at else None,
                task.completed_at.isoformat() if task.completed_at else None,
                task.error_message
            ))
            await db.commit()
            logger.info(f"Created task {task.task_id}")
            return task
    
    async def get_by_id(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        async with db_manager.get_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM tasks WHERE task_id = ?",
                (task_id,)
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_task(row)
    
    async def list_by_project(self, project_id: str) -> List[Task]:
        """List tasks by project ID"""
        async with db_manager.get_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM tasks WHERE project_id = ? ORDER BY created_at DESC",
                (project_id,)
            )
            rows = await cursor.fetchall()
            
            return [self._row_to_task(row) for row in rows]
    
    async def list_by_status(self, status: TaskStatus) -> List[Task]:
        """List tasks by status"""
        async with db_manager.get_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC",
                (status.value,)
            )
            rows = await cursor.fetchall()
            
            return [self._row_to_task(row) for row in rows]
    
    async def update(self, task: Task) -> Task:
        """Update an existing task"""
        async with db_manager.get_connection() as db:
            await db.execute("""
                UPDATE tasks 
                SET name = ?, description = ?, complexity = ?, estimated_tokens = ?,
                    actual_tokens = ?, subtask_ids = ?, checkpoint_state = ?,
                    checkpoint_uri = ?, status = ?, started_at = ?, 
                    completed_at = ?, error_message = ?
                WHERE task_id = ?
            """, (
                task.name,
                task.description,
                task.complexity.value,
                task.estimated_tokens,
                task.actual_tokens,
                json.dumps(task.subtask_ids),
                task.checkpoint_state.value,
                task.checkpoint_uri,
                task.status.value,
                task.started_at.isoformat() if task.started_at else None,
                task.completed_at.isoformat() if task.completed_at else None,
                task.error_message,
                task.task_id
            ))
            await db.commit()
            logger.info(f"Updated task {task.task_id}")
            return task
    
    def _row_to_task(self, row) -> Task:
        """Convert database row to Task object"""
        return Task(
            task_id=row['task_id'],
            parent_agent_id=row['parent_agent_id'],
            project_id=row['project_id'],
            name=row['name'],
            description=row['description'],
            complexity=TaskComplexity(row['complexity']),
            estimated_tokens=row['estimated_tokens'],
            actual_tokens=row['actual_tokens'],
            subtask_ids=json.loads(row['subtask_ids']) if row['subtask_ids'] else [],
            checkpoint_state=CheckpointState(row['checkpoint_state']),
            checkpoint_uri=row['checkpoint_uri'],
            status=TaskStatus(row['status']),
            created_at=datetime.fromisoformat(row['created_at']),
            started_at=datetime.fromisoformat(row['started_at']) if row['started_at'] else None,
            completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
            error_message=row['error_message']
        )


class TokenUsageRepository:
    """Repository for token usage tracking"""
    
    async def create(self, usage: TokenUsage) -> TokenUsage:
        """Record token usage"""
        async with db_manager.get_connection() as db:
            await db.execute("""
                INSERT INTO token_usage (
                    usage_id, project_id, task_id, agent_id, tokens_used,
                    operation_type, timestamp, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                usage.usage_id,
                usage.project_id,
                usage.task_id,
                usage.agent_id,
                usage.tokens_used,
                usage.operation_type,
                usage.timestamp.isoformat(),
                json.dumps(usage.metadata)
            ))
            await db.commit()
            return usage
    
    async def get_project_usage(self, project_id: str) -> int:
        """Get total token usage for a project"""
        async with db_manager.get_connection() as db:
            cursor = await db.execute(
                "SELECT COALESCE(SUM(tokens_used), 0) as total FROM token_usage WHERE project_id = ?",
                (project_id,)
            )
            row = await cursor.fetchone()
            return row['total'] if row else 0
    
    async def get_usage_history(self, project_id: str, limit: int = 100) -> List[TokenUsage]:
        """Get token usage history for a project"""
        async with db_manager.get_connection() as db:
            cursor = await db.execute("""
                SELECT * FROM token_usage 
                WHERE project_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (project_id, limit))
            rows = await cursor.fetchall()
            
            usage_list = []
            for row in rows:
                usage_list.append(TokenUsage(
                    usage_id=row['usage_id'],
                    project_id=row['project_id'],
                    task_id=row['task_id'],
                    agent_id=row['agent_id'],
                    tokens_used=row['tokens_used'],
                    operation_type=row['operation_type'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                ))
            
            return usage_list