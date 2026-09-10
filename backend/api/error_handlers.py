"""
ARIS Canonical Error Handlers.
Intercepts all API exceptions and maps them to the canonical Error Schema:
{
    "error_code": "ARIS_SERIAL_DISCONNECTED",
    "message": "Arduino serial connection was lost.",
    "details": {},
    "recoverable": true
}
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.telemetry.telemetry_schema import ArisException, ArisErrorResponse


async def aris_exception_handler(request: Request, exc: ArisException) -> JSONResponse:
    """Handles domain-level ArisException instances with exact schema."""
    error_payload = exc.to_error_response().model_dump()
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handles FastAPI Pydantic payload validation errors."""
    error_resp = ArisErrorResponse(
        error_code="ARIS_TELEMETRY_INVALID",
        message="Request validation failed against canonical schema.",
        details={"errors": exc.errors()},
        recoverable=True
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_resp.model_dump()
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handles standard HTTPExceptions."""
    code = "ARIS_BACKEND_UNAVAILABLE" if exc.status_code >= 500 else "ARIS_BOARD_NOT_FOUND" if exc.status_code == 404 else "ARIS_TELEMETRY_INVALID"
    error_resp = ArisErrorResponse(
        error_code=code,
        message=str(exc.detail),
        details={"status_code": exc.status_code},
        recoverable=True
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_resp.model_dump()
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Fallback handler for uncaught server exceptions."""
    error_resp = ArisErrorResponse(
        error_code="ARIS_BACKEND_UNAVAILABLE",
        message=f"Internal server error: {str(exc)}",
        details={},
        recoverable=False
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_resp.model_dump()
    )
