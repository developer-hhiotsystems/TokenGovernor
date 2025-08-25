"""Token management API routes"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
import logging

from ...core.models import TokenUsage
from ...registry.repository import TokenUsageRepository, ProjectRepository
from ..schemas import TokenUsageCreate, TokenUsageResponse, BudgetStatusResponse

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_token_repository():
    return TokenUsageRepository()

async def get_project_repository():
    return ProjectRepository()


@router.post("/usage", response_model=TokenUsageResponse)
async def record_token_usage(
    usage_data: TokenUsageCreate,
    repo: TokenUsageRepository = Depends(get_token_repository)
):
    """Record token usage"""
    try:
        usage = TokenUsage(
            project_id=usage_data.project_id,
            task_id=usage_data.task_id,
            agent_id=usage_data.agent_id,
            tokens_used=usage_data.tokens_used,
            operation_type=usage_data.operation_type,
            metadata=usage_data.metadata
        )
        
        created_usage = await repo.create(usage)
        logger.info(f"Recorded {usage_data.tokens_used} tokens for project {usage_data.project_id}")
        
        return TokenUsageResponse(**created_usage.dict())
        
    except Exception as e:
        logger.error(f"Failed to record token usage: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/usage/{project_id}", response_model=List[TokenUsageResponse])
async def get_token_usage_history(
    project_id: str,
    limit: int = 100,
    repo: TokenUsageRepository = Depends(get_token_repository)
):
    """Get token usage history for a project"""
    usage_history = await repo.get_usage_history(project_id, limit)
    return [TokenUsageResponse(**usage.dict()) for usage in usage_history]


@router.get("/budget/{project_id}", response_model=BudgetStatusResponse)
async def get_budget_status(
    project_id: str,
    token_repo: TokenUsageRepository = Depends(get_token_repository),
    project_repo: ProjectRepository = Depends(get_project_repository)
):
    """Get budget status for a project"""
    # Get project details
    project = await project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Calculate usage
    used_tokens = await token_repo.get_project_usage(project_id)
    remaining_tokens = max(0, project.token_budget - used_tokens)
    usage_percentage = (used_tokens / project.token_budget) * 100
    
    # Determine alert level
    alert_level = None
    if usage_percentage >= 95:
        alert_level = "critical"
    elif usage_percentage >= 80:
        alert_level = "warning"
    
    return BudgetStatusResponse(
        project_id=project_id,
        total_budget=project.token_budget,
        used_tokens=used_tokens,
        remaining_tokens=remaining_tokens,
        usage_percentage=usage_percentage,
        alert_level=alert_level
    )