from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware

from app.logging_context import bind_log_context, reset_log_context


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        token = bind_log_context(correlation_id=correlation_id)
        try:
            response = await call_next(request)
        finally:
            reset_log_context(token)
        response.headers["X-Correlation-ID"] = correlation_id
        return response
