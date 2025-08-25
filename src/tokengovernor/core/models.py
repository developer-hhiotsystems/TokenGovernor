"""Data models for TokenGovernor system"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import uuid


class PriorityTier(str, Enum):
    """Project priority tiers"""
    TIER_1 = "tier_1"  # High priority
    TIER_2 = "tier_2"  # Low priority


class TaskComplexity(str, Enum):
    """Task complexity levels"""
    SIMPLE = "simple"          # <1k tokens
    COMPLEX = "complex"        # 1k-5k tokens
    VERY_COMPLEX = "very_complex"  # >5k tokens


class CheckpointState(str, Enum):
    """Checkpoint states"""
    NONE = "none"
    REQUESTED = "requested"
    SAVED = "saved"


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class Project(BaseModel):
    """Project model"""
    project_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    token_budget: int = Field(gt=0)
    priority_tier: PriorityTier
    owner: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class Agent(BaseModel):
    """Agent model (ephemeral)"""
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    agent_type: str  # setup, pr, simulation, monitor
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: Optional[datetime] = None


class Task(BaseModel):
    """Task model"""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_agent_id: str
    project_id: str
    name: str
    description: Optional[str] = None
    complexity: TaskComplexity
    estimated_tokens: int = Field(ge=0)
    actual_tokens: Optional[int] = Field(default=0, ge=0)
    subtask_ids: List[str] = Field(default_factory=list)
    checkpoint_state: CheckpointState = CheckpointState.NONE
    checkpoint_uri: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class TaskPackage(BaseModel):
    """Task package model (collection of related tasks)"""
    package_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    name: str
    description: Optional[str] = None
    task_ids: List[str] = Field(default_factory=list)
    estimated_tokens: int = Field(ge=0)
    priority: PriorityTier
    timeline: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class TokenUsage(BaseModel):
    """Token usage tracking model"""
    usage_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    tokens_used: int = Field(ge=0)
    operation_type: str  # creation, completion, checkpoint, etc.
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class Checkpoint(BaseModel):
    """Checkpoint model"""
    checkpoint_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    checkpoint_uri: str
    checkpoint_data: Dict[str, Any] = Field(default_factory=dict)
    compression_used: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    size_bytes: Optional[int] = None
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class SchedulerRule(BaseModel):
    """Scheduler rule model"""
    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    priority_tier: PriorityTier
    max_concurrent_tasks: int = Field(ge=1)
    rate_limit_per_minute: int = Field(ge=1)
    retry_attempts: int = Field(ge=0, le=10)
    backoff_multiplier: float = Field(ge=1.0)
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }