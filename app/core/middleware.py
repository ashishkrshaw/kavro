"""
middleware.py - custom middleware
"""

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response, status


class LimitUploadSize(BaseHTTPMiddleware):
    """limit request body size to prevent abuse"""
    
    def __init__(self, app, max_upload_size: int) -> None:
        super().__init__(app)
        self.max_upload_size = max_upload_size

    async def dispatch(self, request: Request, call_next):
        if request.method == 'POST':
            if 'content-length' in request.headers:
                content_length = int(request.headers['content-length'])
                if content_length > self.max_upload_size:
                    return Response("Request too large", 
                                  status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        return await call_next(request)
