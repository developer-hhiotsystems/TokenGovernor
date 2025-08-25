"""Rate limiting functionality for TokenGovernor"""
import asyncio
import time
from typing import Dict, Optional
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for controlling API calls and task execution"""
    
    def __init__(self, default_rate_limit: int = 5):
        """Initialize rate limiter
        
        Args:
            default_rate_limit: Default calls per minute
        """
        self.default_rate_limit = default_rate_limit
        self.call_history: Dict[str, deque] = defaultdict(deque)
        self.rate_limits: Dict[str, int] = {}
    
    async def can_execute(self, project_id: str) -> bool:
        """Check if project can execute another operation"""
        try:
            rate_limit = self.rate_limits.get(project_id, self.default_rate_limit)
            current_time = time.time()
            cutoff_time = current_time - 60  # 1 minute ago
            
            # Clean old entries
            history = self.call_history[project_id]
            while history and history[0] < cutoff_time:
                history.popleft()
            
            # Check if under rate limit
            can_proceed = len(history) < rate_limit
            
            if can_proceed:
                history.append(current_time)
            
            return can_proceed
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True  # Allow on error to avoid blocking
    
    async def get_retry_after(self, project_id: str) -> int:
        """Get seconds to wait before retrying"""
        try:
            history = self.call_history[project_id]
            if not history:
                return 0
            
            oldest_call = history[0]
            wait_time = max(0, 60 - (time.time() - oldest_call))
            return int(wait_time)
            
        except Exception as e:
            logger.error(f"Retry calculation error: {e}")
            return 60  # Default 1 minute wait
    
    async def is_rate_limited(self, project_id: str) -> bool:
        """Check if project is currently rate limited"""
        return not await self.can_execute(project_id)
    
    def set_rate_limit(self, project_id: str, rate_limit: int) -> None:
        """Set custom rate limit for a project"""
        self.rate_limits[project_id] = rate_limit
        logger.info(f"Set rate limit for {project_id}: {rate_limit} calls/minute")