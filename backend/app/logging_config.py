"""
MACSS — Structured Logging Setup
Every component calls get_logger(__name__) to get a structlog logger
that emits JSON-formatted log lines, perfect for log aggregation.
"""
import logging
import sys
import structlog


def configure_logging(level: str = "INFO") -> None:
    """Configure structlog for JSON output. Call once at startup."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.getLevelName(level),
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "macss"):
    """Return a bound structlog logger with the component name attached."""
    return structlog.get_logger(name)
