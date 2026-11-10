from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        return response
