from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
    OTLPMetricExporter,
)
from opentelemetry.metrics import (
    get_meter_provider,
    set_meter_provider,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from time import sleep

from opentelemetry.launcher import configure_opentelemetry

# exporter = OTLPMetricExporter(insecure=True)
# reader = PeriodicExportingMetricReader(exporter)
# provider = MeterProvider(metric_readers=[reader])
# set_meter_provider(provider)


configure_opentelemetry(
    metrics_enabled=True,
    # metrics_exporter_endpoint="https://ingest.staging.lightstep.com",
    metrics_exporter_endpoint="ingest.staging.lightstep.com",
    service_name="metrics_test_23354",
    service_version="server_version",  # optional
)
meter = get_meter_provider().get_meter("getting-started", "0.1.2")

# Counter
counter = meter.create_counter("counter")


def test_metrics_example():
    counter.add(1)
    sleep(5)
