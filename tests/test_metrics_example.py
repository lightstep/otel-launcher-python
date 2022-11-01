from opentelemetry.metrics import (
    get_meter_provider,
)
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
histogram = meter.create_histogram("exponential_histogram")


def test_metrics_example():

    for i in range(100):

        histogram.record(
            i,
            attributes={
                "test_exponential_histogram_key":
                "test_exponential_histogram_value"
            }
        )
        sleep(5)
        print(i)
