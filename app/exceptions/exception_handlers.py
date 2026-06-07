from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.exceptions.custom_exceptions import RetroException
from app.exceptions.errors import ErrorCode
from app.observability.logging import get_logger
from app.schemas.error_response import ErrorDetail, ErrorResponse

logger = get_logger(__name__)


def build_response(
    message: str, status_code: int, path: str, details: list[ErrorDetail] | None = None
) -> JSONResponse:
    error_response = ErrorResponse(
        message=message,
        status_code=status_code,
        path=path,
        details=details,
    )
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(exclude_none=True),
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RetroException)
    async def retro_exception_handler(
        request: Request, exc: RetroException
    ) -> JSONResponse:
        return build_response(
            message=exc.message,
            status_code=exc.status_code,
            path=request.url.path,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details: list[ErrorDetail] = [
            ErrorDetail(
                # field=" → ".join(str(p) for p in error.get("loc", [])) or None,
                message=error.get("msg", "Invalid value"),
                # code=error.get("type"),
            )
            for error in exc.errors()
        ]
        return build_response(
            message="Request validation failed. Check the 'details' field for specifics.",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            path=request.url.path,
            details=details,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        response = build_response(
            message=str(exc.detail) if settings.DEBUG else "HTTP error occurred",
            status_code=exc.status_code,
            path=request.url.path,
        )
        if exc.headers:
            response.headers.update(exc.headers)
        return response

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        return build_response(
            message=ErrorCode.INTERNAL_SERVER_ERROR.message,
            status_code=ErrorCode.INTERNAL_SERVER_ERROR.status_code,
            path=request.url.path,
        )
