import logging
import structlog
from core.config import settings


def configure_logging() -> None:
    """Configure structlog for the application."""

    log_level = logging.DEBUG if settings.debug else logging.INFO

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        level=log_level,
    )

    # Shared processors for all loggers
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.debug:
        # Pretty console output for development
        renderer = structlog.dev.ConsoleRenderer()
    else:
        # JSON output for production (easy to parse in log aggregators)
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__):
    """Get a structlog logger. Usage: logger = get_logger(__name__)"""
    return structlog.get_logger(name)
