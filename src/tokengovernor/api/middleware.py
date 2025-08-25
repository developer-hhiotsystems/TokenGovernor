"""API middleware for TokenGovernor"""
import time
import logging
from fastapi import Request, Response
from typing import Callable

logger = logging.getLogger(__name__)


async def token_tracking_middleware(request: Request, call_next: Callable) -> Response:
    """Middleware to track API token usage"""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log API usage (for future token estimation)
    logger.info(
        f"API Call: {request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Time: {process_time:.3f}s"
    )
    
    # Add processing time header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response