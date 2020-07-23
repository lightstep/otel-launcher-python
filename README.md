![build status](https://github.com/lightstep/otel-launcher-python/workflows/Python%20package/badge.svg) [![PyPI version](https://badge.fury.io/py/opentelemetry-launcher.svg)](https://badge.fury.io/py/opentelemetry-launcher)

# Launcher, an OpenTelemetry Configuration Layer for Python 🚀

*NOTE: the code in this repo is currently in alpha and will likely change*

This is the launcher package for configuring OpenTelemetry

### Install

```bash
pip install opentelemetry-launcher
```

### Configure

Minimal setup

```python
from opentelemetry.launcher import configure_opentelemetry

configure_opentelemetry(
    service_name="service-123",
    access_token="my-token",  # optional
)

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("foo") as span:
    span.set_attribute("attr1", "valu1")
    with tracer.start_as_current_span("bar"):
        with tracer.start_as_current_span("baz"):
            print("Hello world from OpenTelemetry Python!")

```

Additional tracer options

```python
configure_opentelemetry(
    service_name="service-123",
    service_version="1.2.3",
    access_token="my-token",
    span_endpoint="ingest.lightstep.com:443",
    metric_endpoint="ingest.lightstep.com:443/metrics",
    log_level=debug,
    span_exporter_endpoint_insecure=False,
    metric_exporter_endpoint_insecure=False,
)

```

### Configuration Options

|Config|Env Variable|Required|Default|
|------|------------|--------|-------|
|service_name                     |LS_SERVICE_NAME|y|-|
|service_version                  |LS_SERVICE_VERSION|n|unknown|
|access_token                     |LS_ACCESS_TOKEN|n|-|
|span_endpoint                    |OTEL_EXPORTER_OTLP_SPAN_ENDPOINT|n|ingest.lightstep.com:443|
|span_exporter_endpoint_insecure  |OTEL_EXPORTER_OTLP_SPAN_INSECURE|n|False|
|metric_endpoint                  |OTEL_EXPORTER_OTLP_METRIC_ENDPOINT|n|ingest.lightstep.com:443/metrics|
|metric_exporter_endpoint_insecure|OTEL_EXPORTER_OTLP_METRIC_INSECURE|n|False|
|propagator                       |OTEL_PROPAGATORS|n|b3|
|resource_labels                  |OTEL_RESOURCE_LABELS|n|-|
|log_level                        |OTEL_LOG_LEVEL|n|error|

