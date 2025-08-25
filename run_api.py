#!/usr/bin/env python3
"""Startup script for TokenGovernor API"""
import uvicorn
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

if __name__ == "__main__":
    uvicorn.run(
        "tokengovernor.api.main:app",
        host="localhost",
        port=8000,
        reload=True,
        log_level="info"
    )