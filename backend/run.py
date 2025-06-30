#!/usr/bin/env python3
"""
AI Observability RCA Backend Application Runner
"""

import uvicorn
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

def main():
    """Main entry point for the application"""
    logger.info("Starting AI Observability RCA Backend...")
    
    try:
        uvicorn.run(
            "app.main:app",
            host=settings.API_HOST,
            port=settings.API_PORT,
            reload=settings.DEBUG,
            log_level="info" if settings.DEBUG else "warning",
            access_log=settings.DEBUG
        )
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
