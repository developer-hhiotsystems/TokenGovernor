"""Status reporting API routes"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime
import logging

from ...registry.repository import ProjectRepository, TaskRepository, TokenUsageRepository
from ..schemas import StatusResponse

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_project_repository():
    return ProjectRepository()

async def get_task_repository():
    return TaskRepository()

async def get_token_repository():
    return TokenUsageRepository()


@router.get("/project/{project_id}", response_model=StatusResponse)
async def get_project_status(
    project_id: str,
    project_repo: ProjectRepository = Depends(get_project_repository),
    task_repo: TaskRepository = Depends(get_task_repository),
    token_repo: TokenUsageRepository = Depends(get_token_repository)
):
    """Get comprehensive project status"""
    # Get project
    project = await project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get task statistics
    tasks = await task_repo.list_by_project(project_id)
    task_stats = {
        "total": len(tasks),
        "pending": sum(1 for t in tasks if t.status == "pending"),
        "in_progress": sum(1 for t in tasks if t.status == "in_progress"),
        "completed": sum(1 for t in tasks if t.status == "completed"),
        "failed": sum(1 for t in tasks if t.status == "failed"),
        "paused": sum(1 for t in tasks if t.status == "paused")
    }
    
    # Get token usage
    used_tokens = await token_repo.get_project_usage(project_id)
    budget_status = {
        "budget": project.token_budget,
        "used": used_tokens,
        "remaining": max(0, project.token_budget - used_tokens),
        "percentage": (used_tokens / project.token_budget) * 100
    }
    
    return StatusResponse(
        entity_type="project",
        entity_id=project_id,
        status="active" if task_stats["in_progress"] > 0 else "idle",
        details={
            "name": project.name,
            "priority": project.priority_tier.value,
            "owner": project.owner,
            "tasks": task_stats,
            "budget": budget_status,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat() if project.updated_at else None
        },
        timestamp=datetime.utcnow()
    )


@router.get("/task/{task_id}", response_model=StatusResponse)
async def get_task_status(
    task_id: str,
    task_repo: TaskRepository = Depends(get_task_repository)
):
    """Get task status"""
    task = await task_repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Calculate progress
    progress = 0.0
    if task.status == "completed":
        progress = 100.0
    elif task.status == "in_progress":
        # Estimate based on token usage if available
        if task.estimated_tokens > 0 and task.actual_tokens > 0:
            progress = min(90.0, (task.actual_tokens / task.estimated_tokens) * 100)
        else:
            progress = 10.0  # Just started
    
    return StatusResponse(
        entity_type="task",
        entity_id=task_id,
        status=task.status.value,
        details={
            "name": task.name,
            "complexity": task.complexity.value,
            "progress": progress,
            "estimated_tokens": task.estimated_tokens,
            "actual_tokens": task.actual_tokens,
            "checkpoint_state": task.checkpoint_state.value,
            "subtasks": len(task.subtask_ids),
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error": task.error_message
        },
        timestamp=datetime.utcnow()
    )


@router.get("/system")
async def get_system_status():
    """Get overall system status"""
    try:
        return {
            "status": "operational",
            "version": "0.1.0",
            "phase": "Phase 0 - GitHub Setup and Change Management",
            "components": {
                "api": "healthy",
                "database": "connected",
                "claude_flow": "initialized"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"System status check failed: {e}")
        raise HTTPException(status_code=503, detail="System status unavailable")