"""Global exception handlers for the FastAPI application."""
from fastapi import Request
from fastapi.responses import JSONResponse
from app.logger import logger

async def oracle_error_handler(request: Request, exc: Exception):
    """Handle Oracle Database related errors globally."""
    logger.error(f"Oracle Error: {str(exc)}")
    return JSONResponse(
        status_code=503,
        content={
            "error": "database_error",
            "message": "An error occurred with the Oracle Database.",
            "detail": str(exc),
        }
    )

async def agent_error_handler(request: Request, exc: Exception):
    """Handle Agent pipeline related errors globally."""
    logger.error(f"Agent Error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "agent_error",
            "message": "An error occurred within the Agent pipeline.",
            "detail": str(exc),
        }
    )
