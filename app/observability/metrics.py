from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import (
    DEPLOYMENT_ENVIRONMENT,
    SERVICE_NAME,
    SERVICE_NAMESPACE,
    SERVICE_VERSION,
    Resource,
)

from app.core.config import Settings


def configure_metrics(settings: Settings) -> MeterProvider:
    resource = Resource.create(
        {
            SERVICE_NAME: settings.APP_NAME,
            SERVICE_VERSION: settings.APP_VERSION,
            SERVICE_NAMESPACE: "default",
            DEPLOYMENT_ENVIRONMENT: settings.ENVIRONMENT,
        }
    )

    exporter = OTLPMetricExporter(
        endpoint=f"{settings.OTLP_ENDPOINT}/v1/metrics",
    )

    reader = PeriodicExportingMetricReader(
        exporter,
        export_interval_millis=10_000,
    )

    provider = MeterProvider(
        resource=resource,
        metric_readers=[reader],
    )

    metrics.set_meter_provider(provider)

    return provider
