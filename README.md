![build status](https://github.com/lightstep/otel-launcher-python/workflows/Python%20package/badge.svg) [![PyPI version](https://badge.fury.io/py/opentelemetry-launcher.svg)](https://badge.fury.io/py/opentelemetry-launcher) [![Downloads](https://pepy.tech/badge/opentelemetry-launcher)](https://pepy.tech/project/opentelemetry-launcher)

# Launcher, a Lightstep Distro for OpenTelemetry 🚀

### What is Launcher?

Launcher is a configuration layer that chooses default values for configuration options that many OpenTelemetry users want. It provides a single function in each language to simplify discovery of the options and components available to users. The goal of Launcher is to help users that aren't familiar with OpenTelemetry quickly ramp up on what they need to get going and instrument.

### Getting started

```bash
pip install opentelemetry-launcher
```

### Configure

Minimal setup

```python
from opentelemetry.launcher import configure_opentelemetry
from opentelemetry import trace

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
    span_exporter_endpoint="https://ingest.lightstep.com:443",
    log_level=debug,
    span_exporter_insecure=False,
)

```

### Usage with Auto Instrumentation

OpenTelemetry Python includes a command that allows the user to automatically instrument
certain third party libraries. Here is an example that shows how to use this launcher
with auto instrumentation.

First, create a new virtual environment:

```bash
cd ~
mkdir auto_instrumentation
virtualenv auto_instrumentation
source auto_instrumentation/bin/activate
pip install opentelemetry-launcher
pip install requests
pip install flask
opentelemetry-bootstrap -a install
```

Once that is done, clone the `opentelemetry-python` repo to get the example code:

```bash
git clone git@github.com:open-telemetry/opentelemetry-python.git
cd opentelemetry-python
git checkout v1.1.0
```

Set the environment variables:

```bash
export OTEL_SERVICE_NAME=auto-instrumentation-testing
export LS_ACCESS_TOKEN=<my-token>
```

Run the server:

```bash
cd docs/examples/auto-instrumentation
opentelemetry-instrument python server_uninstrumented.py
```

Run the client in a separate console:

```bash
cd docs/examples/auto-instrumentation
python client.py testing
```

This should produce spans that can be captured in the Lightstep Explorer.

### Configuration Options

|Config|Env Variable|Required|Default|
|------|------------|--------|-------|
|service_name|OTEL_SERVICE_NAME|y|-|
|service_version|LS_SERVICE_VERSION|n|`None`|
|access_token|LS_ACCESS_TOKEN|n|`None`|
|metrics_enabled|LS_METRICS_ENABLED|n|`False`|
|span_exporter_endpoint|OTEL_EXPORTER_OTLP_TRACES_ENDPOINT|n|`https://ingest.lightstep.com:443`|
|span_exporter_insecure|OTEL_EXPORTER_OTLP_TRACES_INSECURE|n|`False`|
|propagators|OTEL_PROPAGATORS|n|`b3`|
|resource_attributes|OTEL_RESOURCE_ATTRIBUTES|n|`telemetry.sdk.language=python,telemetry.sdk.version=0.12b0`|
|log_level|OTEL_LOG_LEVEL|n|`ERROR`|
|metrics_exporter_endpoint|OTLP_EXPORTER_METRICS_ENDPOINT|n|`https://ingest.lightstep.com:443`|
|metrics_exporter_temporality_preference|OTLP_EXPORTER_METRICS_TEMPORALITY_PREFERENCE|n|`cumulative`|

The configuration option for `propagators` accepts a comma-separated string that will be interpreted as a list. For example, `a,b,c,d` will be interpreted as `["a", "b", "c", "d"]`.
The configuration option for `resource_attributes` accepts a comma-separated string of `key=value` pairs that will be interpreted as a dictionary. For example, `a=1,b=2,c=3,d=4` will be interpreted as `{"a": 1, "b": 2, "c": 3, "d": 4}`.

#### Note about metrics

Metrics support is still **experimental**.

### Principles behind Launcher

##### 100% interoperability with OpenTelemetry

One of the key principles behind putting together Launcher is to make lives of OpenTelemetry users easier, this means that there is no special configuration that **requires** users to install Launcher in order to use OpenTelemetry. It also means that any users of Launcher can leverage the flexibility of configuring OpenTelemetry as they need.

##### Validation

Another decision we made with launcher is to provide end users with a layer of validation of their configuration. This provides us the ability to give feedback to our users faster, so they can start collecting telemetry sooner.

Start using it today in [Go](https://github.com/lightstep/otel-launcher-go), [Java](https://github.com/lightstep/otel-launcher-java), [Javascript](https://github.com/lightstep/otel-launcher-node) and [Python](https://github.com/lightstep/otel-launcher-python) and let us know what you think!

------

*Made with* ![:heart:](https://a.slack-edge.com/production-standard-emoji-assets/10.2/apple-medium/2764-fe0f.png) *@ [Lightstep](http://lightstep.com/)*
