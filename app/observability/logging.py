import logging
import sys
from typing import Any

import structlog
from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import (
    OTLPLogExporter,
)
from opentelemetry.sdk._logs import (
    LoggerProvider,
    LoggingHandler,
)
from opentelemetry.sdk._logs.export import (
    BatchLogRecordProcessor,
)
from opentelemetry.sdk.resources import (
    DEPLOYMENT_ENVIRONMENT,
    SERVICE_NAME,
    SERVICE_NAMESPACE,
    SERVICE_VERSION,
    Resource,
)
from structlog.contextvars import bind_contextvars, clear_contextvars

from app.core.config import Settings


def configure_logging(
    settings: Settings, log_level: str = "INFO", log_format: str = "json"
) -> None:

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        add_trace_context,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if log_format == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    otel_handler = configure_log_exporter(
        settings,
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.addHandler(otel_handler)
    root.setLevel(log_level)

    for name in ("uvicorn.access", "httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.WARNING)

    for name in ("sqlalchemy", "sqlalchemy.engine", "sqlalchemy.engine.Engine"):
        sa_log = logging.getLogger(name)
        sa_log.handlers.clear()
        sa_log.propagate = True
        sa_log.setLevel(logging.WARNING)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.WARNING)

    for name in (
        "urllib3",
        "urllib3.connectionpool",
        "opentelemetry",
    ):
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str = __name__) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)


def bind_request_context(**kwargs: Any) -> None:
    bind_contextvars(**kwargs)


def clear_request_context() -> None:
    clear_contextvars()


def add_trace_context(_, __, event_dict):
    span = trace.get_current_span()
    if span:
        ctx = span.get_span_context()
        if ctx.is_valid:
            event_dict["trace_id"] = format(
                ctx.trace_id,
                "032x",
            )
            event_dict["span_id"] = format(
                ctx.span_id,
                "016x",
            )

    return event_dict


def configure_log_exporter(settings) -> LoggingHandler:
    resource = Resource.create(
        {
            SERVICE_NAME: settings.APP_NAME,
            SERVICE_VERSION: settings.APP_VERSION,
            SERVICE_NAMESPACE: "default",
            DEPLOYMENT_ENVIRONMENT: settings.ENVIRONMENT,
        }
    )

    provider = LoggerProvider(
        resource=resource,
    )

    exporter = OTLPLogExporter(
        endpoint=f"{settings.OTLP_ENDPOINT}/v1/logs",
    )

    provider.add_log_record_processor(BatchLogRecordProcessor(exporter))

    set_logger_provider(provider)

    return LoggingHandler(
        logger_provider=provider,
    )
