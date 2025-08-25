"""Checkpoint management for TokenGovernor tasks"""
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from ..core.models import Task, Checkpoint

logger = logging.getLogger(__name__)


class CheckpointManager:
    """Manages task checkpoints for recovery and state preservation"""
    
    def __init__(self, storage_path: str = "checkpoints"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    async def prepare_checkpoint(self, task: Task) -> str:
        """Prepare checkpoint URI for a task"""
        checkpoint_id = f"{task.task_id}_{datetime.utcnow().timestamp()}"
        checkpoint_uri = f"file://{self.storage_path}/{checkpoint_id}.json"
        
        logger.info(f"Prepared checkpoint URI for task {task.task_id}: {checkpoint_uri}")
        return checkpoint_uri
    
    async def create_checkpoint(self, task: Task) -> Optional[Checkpoint]:
        """Create a checkpoint for a task"""
        try:
            checkpoint_uri = await self.prepare_checkpoint(task)
            
            # Create checkpoint data
            checkpoint_data = {
                "task_id": task.task_id,
                "status": task.status.value,
                "progress": {
                    "estimated_tokens": task.estimated_tokens,
                    "actual_tokens": task.actual_tokens,
                    "completion_percentage": (task.actual_tokens / task.estimated_tokens * 100) if task.estimated_tokens > 0 else 0
                },
                "context": {
                    "project_id": task.project_id,
                    "complexity": task.complexity.value,
                    "subtasks": task.subtask_ids
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Save checkpoint to file
            checkpoint_file = self.storage_path / f"{task.task_id}_{datetime.utcnow().timestamp()}.json"
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
            
            # Update task
            task.checkpoint_state = "saved"
            task.checkpoint_uri = str(checkpoint_file)
            
            checkpoint = Checkpoint(
                task_id=task.task_id,
                checkpoint_uri=str(checkpoint_file),
                checkpoint_data=checkpoint_data,
                size_bytes=checkpoint_file.stat().st_size
            )
            
            logger.info(f"Created checkpoint for task {task.task_id}")
            return checkpoint
            
        except Exception as e:
            logger.error(f"Failed to create checkpoint: {e}")
            return None
    
    async def load_checkpoint(self, checkpoint_uri: str) -> Optional[Dict[str, Any]]:
        """Load checkpoint data from URI"""
        try:
            checkpoint_path = Path(checkpoint_uri.replace("file://", ""))
            
            if not checkpoint_path.exists():
                logger.warning(f"Checkpoint file not found: {checkpoint_path}")
                return None
            
            with open(checkpoint_path, 'r') as f:
                checkpoint_data = json.load(f)
            
            logger.info(f"Loaded checkpoint from {checkpoint_uri}")
            return checkpoint_data
            
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None
    
    async def list_checkpoints(self, task_id: str) -> list:
        """List all checkpoints for a task"""
        try:
            checkpoints = []
            for checkpoint_file in self.storage_path.glob(f"{task_id}_*.json"):
                try:
                    with open(checkpoint_file, 'r') as f:
                        data = json.load(f)
                    
                    checkpoints.append({
                        "file": str(checkpoint_file),
                        "timestamp": data.get("timestamp"),
                        "size": checkpoint_file.stat().st_size
                    })
                except Exception as e:
                    logger.warning(f"Could not read checkpoint {checkpoint_file}: {e}")
            
            # Sort by timestamp (newest first)
            checkpoints.sort(key=lambda x: x["timestamp"], reverse=True)
            return checkpoints
            
        except Exception as e:
            logger.error(f"Failed to list checkpoints: {e}")
            return []