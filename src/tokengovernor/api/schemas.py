"""API request/response schemas"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from ..core.models import PriorityTier, TaskComplexity, TaskStatus, CheckpointState, Project


class ProjectCreate(BaseModel):
    """Schema for creating a project"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    token_budget: int = Field(..., gt=0, le=1000000)
    priority_tier: PriorityTier
    owner: str = Field(..., min_length=1, max_length=100)


class ProjectUpdate(BaseModel):
    """Schema for updating a project"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    token_budget: Optional[int] = Field(None, gt=0, le=1000000)
    priority_tier: Optional[PriorityTier] = None
    owner: Optional[str] = Field(None, min_length=1, max_length=100)


class ProjectResponse(BaseModel):
    """Schema for project responses"""
    project_id: str
    name: str
    description: Optional[str]
    token_budget: int
    priority_tier: PriorityTier
    owner: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    @classmethod
    def from_project(cls, project: Project) -> "ProjectResponse":
        return cls(
            project_id=project.project_id,
            name=project.name,
            description=project.description,
            token_budget=project.token_budget,
            priority_tier=project.priority_tier,
            owner=project.owner,
            created_at=project.created_at,
            updated_at=project.updated_at
        )


class TaskCreate(BaseModel):
    """Schema for creating a task"""
    parent_agent_id: str
    project_id: str
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    complexity: TaskComplexity
    estimated_tokens: int = Field(..., ge=0)
    subtask_ids: List[str] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    complexity: Optional[TaskComplexity] = None
    estimated_tokens: Optional[int] = Field(None, ge=0)
    actual_tokens: Optional[int] = Field(None, ge=0)
    subtask_ids: Optional[List[str]] = None
    checkpoint_state: Optional[CheckpointState] = None
    checkpoint_uri: Optional[str] = None
    status: Optional[TaskStatus] = None
    error_message: Optional[str] = None


class TaskResponse(BaseModel):
    """Schema for task responses"""
    task_id: str
    parent_agent_id: str
    project_id: str
    name: str
    description: Optional[str]
    complexity: TaskComplexity
    estimated_tokens: int
    actual_tokens: int
    subtask_ids: List[str]
    checkpoint_state: CheckpointState
    checkpoint_uri: Optional[str]
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]


class TokenUsageCreate(BaseModel):
    """Schema for recording token usage"""
    project_id: str
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    tokens_used: int = Field(..., ge=0)
    operation_type: str
    metadata: dict = Field(default_factory=dict)


class TokenUsageResponse(BaseModel):
    """Schema for token usage responses"""
    usage_id: str
    project_id: str
    task_id: Optional[str]
    agent_id: Optional[str]
    tokens_used: int
    operation_type: str
    timestamp: datetime
    metadata: dict


class StatusResponse(BaseModel):
    """Schema for status responses"""
    entity_type: str  # project, agent, task
    entity_id: str
    status: str
    details: dict
    timestamp: datetime


class BudgetStatusResponse(BaseModel):
    """Schema for budget status responses"""
    project_id: str
    total_budget: int
    used_tokens: int
    remaining_tokens: int
    usage_percentage: float
    alert_level: Optional[str] = None  # warning, critical