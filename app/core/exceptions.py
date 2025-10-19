"""
exceptions.py - global exception handlers
makes error responses consistent and user-friendly
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger("error_handler")


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """handle pydantic validation errors"""
    errors = []
    for error in exc.errors():
        field = error.get("loc", ["unknown"])[-1]
        msg = error.get("msg", "Invalid value")
        
        # clean up pydantic messages
        if "Value error," in msg:
            msg = msg.replace("Value error, ", "")
        
        errors.append({"field": field, "message": msg})
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Validation failed", "details": errors}
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """handle http exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )


async def general_exception_handler(request: Request, exc: Exception):
    """handle unexpected errors"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Something went wrong. Please try again.", "status_code": 500}
    )
