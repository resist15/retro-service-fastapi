from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.sdk.resources import (
    DEPLOYMENT_ENVIRONMENT,
    SERVICE_NAME,
    SERVICE_NAMESPACE,
    SERVICE_VERSION,
    Resource,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.config import Settings


def configure_tracing(settings: Settings) -> TracerProvider:
    resource = Resource.create(
        {
            SERVICE_NAME: settings.APP_NAME,
            SERVICE_VERSION: settings.APP_VERSION,
            SERVICE_NAMESPACE: "default",
            DEPLOYMENT_ENVIRONMENT: settings.ENVIRONMENT,
        }
    )

    provider = TracerProvider(resource=resource)

    exporter = OTLPSpanExporter(
        endpoint=f"{settings.OTLP_ENDPOINT}/v1/traces",
    )

    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return provider
