"""Project management API routes"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import logging

from ...core.models import Project, PriorityTier
from ...registry.repository import ProjectRepository
from ..schemas import ProjectCreate, ProjectUpdate, ProjectResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Dependency injection
async def get_project_repository():
    return ProjectRepository()


@router.post("/register", response_model=ProjectResponse)
async def register_project(
    project_data: ProjectCreate,
    repo: ProjectRepository = Depends(get_project_repository)
):
    """Register a new project"""
    try:
        # Create project instance
        project = Project(
            name=project_data.name,
            description=project_data.description,
            token_budget=project_data.token_budget,
            priority_tier=project_data.priority_tier,
            owner=project_data.owner
        )
        
        # Save to database
        created_project = await repo.create(project)
        
        logger.info(f"Registered project: {created_project.project_id}")
        return ProjectResponse.from_project(created_project)
        
    except Exception as e:
        logger.error(f"Failed to register project: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    repo: ProjectRepository = Depends(get_project_repository)
):
    """Get project by ID"""
    project = await repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return ProjectResponse.from_project(project)


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    repo: ProjectRepository = Depends(get_project_repository)
):
    """List all projects"""
    projects = await repo.list_all()
    return [ProjectResponse.from_project(p) for p in projects]


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    repo: ProjectRepository = Depends(get_project_repository)
):
    """Update an existing project"""
    # Get existing project
    existing_project = await repo.get_by_id(project_id)
    if not existing_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update fields
    update_data = project_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_project, field, value)
    
    # Save changes
    updated_project = await repo.update(existing_project)
    
    logger.info(f"Updated project: {project_id}")
    return ProjectResponse.from_project(updated_project)


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    repo: ProjectRepository = Depends(get_project_repository)
):
    """Delete a project"""
    deleted = await repo.delete(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    
    logger.info(f"Deleted project: {project_id}")
    return {"message": "Project deleted successfully"}


@router.get("/{project_id}/budget")
async def get_project_budget_status(
    project_id: str,
    repo: ProjectRepository = Depends(get_project_repository)
):
    """Get project budget status"""
    project = await repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # TODO: Calculate actual token usage
    # This will be implemented when TokenInspector is built
    
    return {
        "project_id": project_id,
        "total_budget": project.token_budget,
        "used_tokens": 0,  # Placeholder
        "remaining_tokens": project.token_budget,
        "usage_percentage": 0.0
    }