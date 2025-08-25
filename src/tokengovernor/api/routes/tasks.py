"""Task management API routes"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
import logging

from ...core.models import Task
from ...registry.repository import TaskRepository
from ..schemas import TaskCreate, TaskUpdate, TaskResponse

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_task_repository():
    return TaskRepository()


@router.post("/register", response_model=TaskResponse)
async def register_task(
    task_data: TaskCreate,
    repo: TaskRepository = Depends(get_task_repository)
):
    """Register a new task"""
    try:
        task = Task(
            parent_agent_id=task_data.parent_agent_id,
            project_id=task_data.project_id,
            name=task_data.name,
            description=task_data.description,
            complexity=task_data.complexity,
            estimated_tokens=task_data.estimated_tokens,
            subtask_ids=task_data.subtask_ids
        )
        
        created_task = await repo.create(task)
        logger.info(f"Registered task: {created_task.task_id}")
        
        return TaskResponse(**created_task.dict())
        
    except Exception as e:
        logger.error(f"Failed to register task: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    repo: TaskRepository = Depends(get_task_repository)
):
    """Get task by ID"""
    task = await repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskResponse(**task.dict())


@router.get("/project/{project_id}", response_model=List[TaskResponse])
async def list_tasks_by_project(
    project_id: str,
    repo: TaskRepository = Depends(get_task_repository)
):
    """List tasks for a project"""
    tasks = await repo.list_by_project(project_id)
    return [TaskResponse(**task.dict()) for task in tasks]


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    repo: TaskRepository = Depends(get_task_repository)
):
    """Update a task"""
    existing_task = await repo.get_by_id(task_id)
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_task, field, value)
    
    updated_task = await repo.update(existing_task)
    logger.info(f"Updated task: {task_id}")
    
    return TaskResponse(**updated_task.dict())


@router.post("/{task_id}/pause")
async def pause_task(
    task_id: str,
    repo: TaskRepository = Depends(get_task_repository)
):
    """Pause a task"""
    task = await repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = "paused"
    await repo.update(task)
    
    logger.info(f"Paused task: {task_id}")
    return {"message": "Task paused successfully"}


@router.post("/{task_id}/resume")
async def resume_task(
    task_id: str,
    repo: TaskRepository = Depends(get_task_repository)
):
    """Resume a paused task"""
    task = await repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != "paused":
        raise HTTPException(status_code=400, detail="Task is not paused")
    
    task.status = "pending"
    await repo.update(task)
    
    logger.info(f"Resumed task: {task_id}")
    return {"message": "Task resumed successfully"}