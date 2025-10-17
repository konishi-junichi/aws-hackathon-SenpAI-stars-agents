"""
Logger configuration for SenpAI Agent application.
Provides structured logging for Starlette/FastAPI applications.
"""

import logging
import logging.config
import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime
import json


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
            
        if hasattr(record, "session_id"):
            log_entry["session_id"] = record.session_id
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


class ColoredConsoleFormatter(logging.Formatter):
    """Colored console formatter for development."""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors for console output."""
        color = self.COLORS.get(record.levelname, self.RESET)
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Build the log message
        log_parts = [
            f"{color}[{record.levelname}]{self.RESET}",
            f"{timestamp}",
            f"{record.name}:{record.funcName}:{record.lineno}",
            f"- {record.getMessage()}"
        ]
        
        # Add context if available
        context_parts = []
        if hasattr(record, "request_id"):
            context_parts.append(f"req_id={record.request_id}")
        if hasattr(record, "user_id"):
            context_parts.append(f"user={record.user_id}")
        if hasattr(record, "session_id"):
            context_parts.append(f"session={record.session_id}")
        
        if context_parts:
            log_parts.insert(-1, f"[{', '.join(context_parts)}]")
        
        formatted_message = " ".join(log_parts)
        
        # Add exception info if present
        if record.exc_info:
            formatted_message += "\n" + self.formatException(record.exc_info)
        
        return formatted_message


def get_log_level() -> str:
    """Get log level from environment variable."""
    return os.getenv("LOG_LEVEL", "INFO").upper()


def get_log_format() -> str:
    """Get log format from environment variable."""
    return os.getenv("LOG_FORMAT", "console").lower()


def create_logging_config(
    level: str = "INFO",
    format_type: str = "console",
    log_file: Optional[str] = None
) -> Dict[str, Any]:
    """Create logging configuration dictionary."""
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JSONFormatter,
            },
            "console": {
                "()": ColoredConsoleFormatter,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": format_type,
                "stream": sys.stdout,
            },
        },
        "loggers": {
            "senpai": {
                "level": level,
                "handlers": ["console"],
                "propagate": False,
            },
            "bedrock_agentcore": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            "boto3": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            "botocore": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            "langchain": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "starlette": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {
            "level": level,
            "handlers": ["console"],
        },
    }
    
    # Add file handler if log file is specified
    if log_file:
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": level,
            "formatter": "json",
            "filename": log_file,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        }
        
        # Add file handler to all loggers
        for logger_config in config["loggers"].values():
            logger_config["handlers"].append("file")
        config["root"]["handlers"].append("file")
    
    return config


def setup_logger(
    name: str = "senpai",
    level: Optional[str] = None,
    format_type: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up and configure logger for the application.
    
    Args:
        name: Logger name (default: "senpai")
        level: Log level (default: from LOG_LEVEL env var or "INFO")
        format_type: Format type "console" or "json" (default: from LOG_FORMAT env var or "console")
        log_file: Optional log file path
    
    Returns:
        Configured logger instance
    """
    if level is None:
        level = get_log_level()
    
    if format_type is None:
        format_type = get_log_format()
    
    # Create and apply logging configuration
    config = create_logging_config(level, format_type, log_file)
    logging.config.dictConfig(config)
    
    # Get the logger
    logger = logging.getLogger(name)
    
    logger.info("Logger initialized", extra={
        "level": level,
        "format": format_type,
        "log_file": log_file,
    })
    
    return logger


def get_logger(name: str = "senpai") -> logging.Logger:
    """
    Get an existing logger instance.
    
    Args:
        name: Logger name (default: "senpai")
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that adds context information to log records."""
    
    def __init__(self, logger: logging.Logger, extra: Dict[str, Any]):
        super().__init__(logger, extra)
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process the log message and add extra context."""
        # Merge extra context
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        
        return msg, kwargs


def get_contextual_logger(
    name: str = "senpai",
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    **extra_context: Any
) -> LoggerAdapter:
    """
    Get a logger with contextual information.
    
    Args:
        name: Logger name
        request_id: Request ID for tracing
        user_id: User ID
        session_id: Session ID
        **extra_context: Additional context to include in logs
    
    Returns:
        Logger adapter with context
    """
    logger = get_logger(name)
    
    context = {}
    if request_id:
        context["request_id"] = request_id
    if user_id:
        context["user_id"] = user_id
    if session_id:
        context["session_id"] = session_id
    
    context.update(extra_context)
    
    return LoggerAdapter(logger, context)