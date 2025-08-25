"""TokenInspector/Governor Agent - Main governance logic"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from enum import Enum

from ..core.models import Project, Task, TaskStatus, PriorityTier
from ..core.config import settings
from ..registry.repository import ProjectRepository, TaskRepository, TokenUsageRepository
from .ccusage_integration import CCUsageTracker
from .rate_limiter import RateLimiter
from .checkpoint_manager import CheckpointManager

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class GovernorAgent:
    """Main TokenInspector/Governor Agent"""
    
    def __init__(self):
        self.project_repo = ProjectRepository()
        self.task_repo = TaskRepository()
        self.token_repo = TokenUsageRepository()
        self.ccusage_tracker = CCUsageTracker()
        self.rate_limiter = RateLimiter()
        self.checkpoint_manager = CheckpointManager()
        
        # Active monitoring state
        self.active_projects: Set[str] = set()
        self.paused_tasks: Set[str] = set()
        self.monitoring_active = False
        
        # Thresholds
        self.warning_threshold = settings.token_management.alert_thresholds["warning"]
        self.critical_threshold = settings.token_management.alert_thresholds["critical"]
    
    async def start_monitoring(self) -> None:
        """Start the governance monitoring system"""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        logger.info("Starting TokenGovernor monitoring system")
        
        # Start monitoring tasks
        monitoring_tasks = [
            asyncio.create_task(self._monitor_token_usage()),
            asyncio.create_task(self._monitor_task_progress()),
            asyncio.create_task(self._manage_checkpoints()),
            asyncio.create_task(self._enforce_rate_limits()),
        ]
        
        try:
            await asyncio.gather(*monitoring_tasks)
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            self.monitoring_active = False
    
    async def stop_monitoring(self) -> None:
        """Stop the monitoring system"""
        self.monitoring_active = False
        logger.info("Stopped TokenGovernor monitoring system")
    
    async def register_project(self, project: Project) -> Dict[str, Any]:
        """Register a project for monitoring"""
        try:
            # Track the registration operation
            tracking_info = await self.ccusage_tracker.track_operation(
                "project_registration",
                {
                    "project_id": project.project_id,
                    "complexity": "simple",
                    "budget": project.token_budget
                },
                estimated_tokens=500
            )
            
            # Register project
            registered_project = await self.project_repo.create(project)
            self.active_projects.add(project.project_id)
            
            # Complete tracking
            await self.ccusage_tracker.complete_operation(
                tracking_info,
                actual_tokens=350,  # Actual tokens used for registration
                success=True
            )
            
            logger.info(f"Registered project {project.project_id} for monitoring")
            
            return {
                "status": "registered",
                "project_id": project.project_id,
                "monitoring": "active",
                "token_budget": project.token_budget
            }
            
        except Exception as e:
            logger.error(f"Failed to register project: {e}")
            await self.ccusage_tracker.complete_operation(
                tracking_info,
                success=False,
                error=str(e)
            )
            raise
    
    async def track_task_execution(self, task: Task) -> Dict[str, Any]:
        """Track and govern task execution"""
        try:
            # Check budget before allowing execution
            budget_check = await self._check_project_budget(task.project_id, task.estimated_tokens)
            if not budget_check["allowed"]:
                return {
                    "status": "blocked",
                    "reason": budget_check["reason"],
                    "recommendation": budget_check["recommendation"]
                }
            
            # Apply rate limiting
            if not await self.rate_limiter.can_execute(task.project_id):
                # Pause the task
                task.status = TaskStatus.PAUSED
                await self.task_repo.update(task)
                self.paused_tasks.add(task.task_id)
                
                return {
                    "status": "rate_limited",
                    "reason": "Project rate limit exceeded",
                    "retry_after": await self.rate_limiter.get_retry_after(task.project_id)
                }
            
            # Check if checkpoint should be requested
            checkpoint_needed = await self._should_request_checkpoint(task)
            if checkpoint_needed:
                task.checkpoint_state = "requested"
                await self.task_repo.update(task)
                
                return {
                    "status": "checkpoint_requested",
                    "reason": "Adaptive threshold reached",
                    "checkpoint_uri": await self.checkpoint_manager.prepare_checkpoint(task)
                }
            
            # Allow execution
            return {
                "status": "approved",
                "estimated_tokens": task.estimated_tokens,
                "monitoring": "active"
            }
            
        except Exception as e:
            logger.error(f"Failed to track task execution: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def handle_task_completion(self, task_id: str, actual_tokens: int) -> Dict[str, Any]:
        """Handle task completion and update tracking"""
        try:
            task = await self.task_repo.get_by_id(task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")
            
            # Update task with actual token usage
            task.actual_tokens = actual_tokens
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            await self.task_repo.update(task)
            
            # Record token usage
            await self.token_repo.create({
                "project_id": task.project_id,
                "task_id": task_id,
                "tokens_used": actual_tokens,
                "operation_type": "task_completion",
                "metadata": {
                    "task_name": task.name,
                    "complexity": task.complexity.value,
                    "estimated_tokens": task.estimated_tokens
                }
            })
            
            # Check for budget alerts
            alerts = await self._check_budget_alerts(task.project_id)
            
            logger.info(f"Task {task_id} completed - used {actual_tokens} tokens")
            
            return {
                "status": "completed",
                "tokens_used": actual_tokens,
                "efficiency": task.estimated_tokens / actual_tokens if actual_tokens > 0 else 1.0,
                "alerts": alerts
            }
            
        except Exception as e:
            logger.error(f"Failed to handle task completion: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get comprehensive project status"""
        try:
            project = await self.project_repo.get_by_id(project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # Get token usage
            used_tokens = await self.token_repo.get_project_usage(project_id)
            usage_percentage = (used_tokens / project.token_budget) * 100
            
            # Get task statistics
            tasks = await self.task_repo.list_by_project(project_id)
            task_stats = {
                "total": len(tasks),
                "pending": len([t for t in tasks if t.status == TaskStatus.PENDING]),
                "in_progress": len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS]),
                "completed": len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
                "failed": len([t for t in tasks if t.status == TaskStatus.FAILED]),
                "paused": len([t for t in tasks if t.status == TaskStatus.PAUSED])
            }
            
            # Determine alert level
            alert_level = AlertLevel.INFO
            if usage_percentage >= self.critical_threshold * 100:
                alert_level = AlertLevel.CRITICAL
            elif usage_percentage >= self.warning_threshold * 100:
                alert_level = AlertLevel.WARNING
            
            # Get efficiency analysis
            efficiency = await self.ccusage_tracker.analyze_efficiency(project_id)
            
            return {
                "project_id": project_id,
                "name": project.name,
                "status": "active" if project_id in self.active_projects else "inactive",
                "budget": {
                    "total": project.token_budget,
                    "used": used_tokens,
                    "remaining": max(0, project.token_budget - used_tokens),
                    "percentage": usage_percentage,
                    "alert_level": alert_level.value
                },
                "tasks": task_stats,
                "efficiency": efficiency,
                "monitoring": {
                    "active": project_id in self.active_projects,
                    "paused_tasks": len([tid for tid in self.paused_tasks if tid in [t.task_id for t in tasks]]),
                    "rate_limited": await self.rate_limiter.is_rate_limited(project_id)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get project status: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _monitor_token_usage(self) -> None:
        """Monitor token usage across all active projects"""
        while self.monitoring_active:
            try:
                for project_id in self.active_projects:
                    await self._check_budget_alerts(project_id)
                
                await asyncio.sleep(settings.token_management.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Token monitoring error: {e}")
                await asyncio.sleep(60)  # Short delay on error
    
    async def _monitor_task_progress(self) -> None:
        """Monitor task progress and handle stalled tasks"""
        while self.monitoring_active:
            try:
                # Check for stalled tasks
                stalled_threshold = datetime.utcnow() - timedelta(hours=2)
                
                for project_id in self.active_projects:
                    tasks = await self.task_repo.list_by_status(TaskStatus.IN_PROGRESS)
                    project_tasks = [t for t in tasks if t.project_id == project_id]
                    
                    for task in project_tasks:
                        if task.started_at and task.started_at < stalled_threshold:
                            logger.warning(f"Task {task.task_id} may be stalled")
                            # Could implement automatic checkpoint request here
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Task monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _manage_checkpoints(self) -> None:
        """Manage checkpoint requests and storage"""
        while self.monitoring_active:
            try:
                # Process checkpoint requests
                tasks_needing_checkpoints = []
                for project_id in self.active_projects:
                    tasks = await self.task_repo.list_by_project(project_id)
                    requested_checkpoints = [t for t in tasks if t.checkpoint_state == "requested"]
                    tasks_needing_checkpoints.extend(requested_checkpoints)
                
                for task in tasks_needing_checkpoints:
                    await self.checkpoint_manager.create_checkpoint(task)
                
                await asyncio.sleep(180)  # Check every 3 minutes
                
            except Exception as e:
                logger.error(f"Checkpoint management error: {e}")
                await asyncio.sleep(60)
    
    async def _enforce_rate_limits(self) -> None:
        """Enforce rate limiting and resume paused tasks"""
        while self.monitoring_active:
            try:
                # Check if any paused tasks can be resumed
                resumed_tasks = []
                for task_id in list(self.paused_tasks):
                    task = await self.task_repo.get_by_id(task_id)
                    if task and await self.rate_limiter.can_execute(task.project_id):
                        task.status = TaskStatus.PENDING
                        await self.task_repo.update(task)
                        resumed_tasks.append(task_id)
                        self.paused_tasks.discard(task_id)
                
                if resumed_tasks:
                    logger.info(f"Resumed {len(resumed_tasks)} rate-limited tasks")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Rate limiting error: {e}")
                await asyncio.sleep(60)
    
    async def _check_project_budget(self, project_id: str, estimated_tokens: int) -> Dict[str, Any]:
        """Check if project has sufficient budget for operation"""
        try:
            project = await self.project_repo.get_by_id(project_id)
            if not project:
                return {"allowed": False, "reason": "Project not found"}
            
            used_tokens = await self.token_repo.get_project_usage(project_id)
            remaining_tokens = project.token_budget - used_tokens
            
            if estimated_tokens > remaining_tokens:
                return {
                    "allowed": False,
                    "reason": "Insufficient token budget",
                    "recommendation": "Increase budget or optimize token usage",
                    "required": estimated_tokens,
                    "available": remaining_tokens
                }
            
            return {"allowed": True}
            
        except Exception as e:
            logger.error(f"Budget check error: {e}")
            return {"allowed": False, "reason": f"Budget check failed: {e}"}
    
    async def _check_budget_alerts(self, project_id: str) -> List[Dict[str, Any]]:
        """Check and generate budget alerts"""
        try:
            project = await self.project_repo.get_by_id(project_id)
            if not project:
                return []
            
            used_tokens = await self.token_repo.get_project_usage(project_id)
            usage_percentage = (used_tokens / project.token_budget)
            
            alerts = []
            
            if usage_percentage >= self.critical_threshold:
                alerts.append({
                    "level": AlertLevel.CRITICAL,
                    "message": f"Critical: Project {project_id} has used {usage_percentage*100:.1f}% of token budget",
                    "recommendation": "Immediate action required - pause non-critical tasks"
                })
            elif usage_percentage >= self.warning_threshold:
                alerts.append({
                    "level": AlertLevel.WARNING,
                    "message": f"Warning: Project {project_id} has used {usage_percentage*100:.1f}% of token budget",
                    "recommendation": "Review token usage and optimize if needed"
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Alert check error: {e}")
            return []
    
    async def _should_request_checkpoint(self, task: Task) -> bool:
        """Determine if a checkpoint should be requested for a task"""
        try:
            # Adaptive threshold based on task complexity and progress
            base_threshold = 0.9  # 90% default
            
            if task.complexity == "very_complex":
                base_threshold = 0.7  # Lower threshold for complex tasks
            elif task.complexity == "simple":
                base_threshold = 0.95  # Higher threshold for simple tasks
            
            # Check if we're approaching the threshold
            if task.estimated_tokens > 0 and task.actual_tokens > 0:
                progress = task.actual_tokens / task.estimated_tokens
                return progress >= base_threshold
            
            return False
            
        except Exception as e:
            logger.error(f"Checkpoint decision error: {e}")
            return False