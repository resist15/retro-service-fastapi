from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class HSTSHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "no-referrer"

        return response


class CSPHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # response.headers["Content-Security-Policy"] = (
        #     "default-src 'self'; "
        #     "script-src 'self'; "
        #     "style-src 'self' 'unsafe-inline'; "
        #     "img-src 'self' data:; "
        #     "font-src 'self'; "
        #     "object-src 'none'; "
        #     "frame-ancestors 'none'; "
        #     "base-uri 'self';"
        # )

        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https:; "
            "style-src 'self' 'unsafe-inline' https:; "
            "img-src 'self' data: https:; "
        )

        return response
