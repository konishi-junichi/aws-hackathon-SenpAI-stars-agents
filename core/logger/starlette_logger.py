"""
Starlette-specific logging utilities and middleware.
"""

import logging
import time
import uuid
from typing import Callable, Optional
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .logger_config import get_contextual_logger, get_logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to add request logging to Starlette applications."""
    
    def __init__(self, app: ASGIApp, logger_name: str = "senpai.http"):
        super().__init__(app)
        self.logger = get_logger(logger_name)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add logging."""
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Extract user/session info from request if available
        user_id = None
        session_id = None
        
        # Try to get user_id and session_id from various sources
        if hasattr(request, "path_params"):
            user_id = request.path_params.get("user_id")
            session_id = request.path_params.get("session_id")
        
        # Try query parameters
        if not user_id:
            user_id = request.query_params.get("user_id")
        if not session_id:
            session_id = request.query_params.get("session_id")
        
        # Try to get from request body if it's JSON
        if not user_id or not session_id:
            try:
                if request.headers.get("content-type", "").startswith("application/json"):
                    body = await request.body()
                    if body:
                        import json
                        data = json.loads(body)
                        if not user_id:
                            user_id = data.get("user_id")
                        if not session_id:
                            session_id = data.get("session_id")
                        
                        # Create new request with body preserved
                        from starlette.requests import Request
                        scope = request.scope.copy()
                        receive = lambda: {"type": "http.request", "body": body}
                        request = Request(scope, receive)
            except Exception:
                pass  # Ignore JSON parsing errors
        
        # Create contextual logger
        contextual_logger = get_contextual_logger(
            "senpai.http",
            request_id=request_id,
            user_id=user_id,
            session_id=session_id
        )
        
        # Store context in request state for use in handlers
        if not hasattr(request.state, "logging_context"):
            request.state.logging_context = {}
        
        request.state.logging_context.update({
            "request_id": request_id,
            "user_id": user_id,
            "session_id": session_id,
            "logger": contextual_logger
        })
        
        # Log request start
        start_time = time.time()
        contextual_logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Log successful response
            duration = time.time() - start_time
            contextual_logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                }
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as exc:
            # Log error
            duration = time.time() - start_time
            contextual_logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration * 1000, 2),
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                },
                exc_info=True
            )
            raise


def get_request_logger(request: Request) -> Optional[logging.LoggerAdapter]:
    """
    Get the contextual logger from a Starlette request.
    
    Args:
        request: Starlette request object
    
    Returns:
        Contextual logger if available, None otherwise
    """
    if hasattr(request.state, "logging_context"):
        return request.state.logging_context.get("logger")
    return None


def get_request_context(request: Request) -> dict:
    """
    Get the logging context from a Starlette request.
    
    Args:
        request: Starlette request object
    
    Returns:
        Dictionary with logging context (request_id, user_id, session_id)
    """
    if hasattr(request.state, "logging_context"):
        context = request.state.logging_context.copy()
        context.pop("logger", None)  # Remove logger object
        return context
    return {}


def setup_starlette_logging(app: Starlette, logger_name: str = "senpai") -> None:
    """
    Set up logging for a Starlette application.
    
    Args:
        app: Starlette application instance
        logger_name: Base logger name
    """
    # Add logging middleware
    app.add_middleware(LoggingMiddleware, logger_name=f"{logger_name}.http")
    
    # Set up exception handler
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger = get_request_logger(request) or get_logger(f"{logger_name}.error")
        
        logger.error(
            f"Unhandled exception: {type(exc).__name__}",
            extra={
                "error": str(exc),
                "error_type": type(exc).__name__,
                "path": request.url.path,
                "method": request.method,
            },
            exc_info=True
        )
        
        from starlette.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "request_id": getattr(request.state, "logging_context", {}).get("request_id")
            }
        )