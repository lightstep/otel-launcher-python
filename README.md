![build status](https://github.com/lightstep/otel-launcher-python/workflows/Python%20package/badge.svg) [![PyPI version](https://badge.fury.io/py/opentelemetry-launcher.svg)](https://badge.fury.io/py/opentelemetry-launcher) [![Downloads](https://pepy.tech/badge/opentelemetry-launcher)](https://pepy.tech/project/opentelemetry-launcher)

# Launcher, an OpenTelemetry Configuration Layer 🚀

*NOTE: the code in this repo is currently in alpha and will likely change*

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
    span_exporter_endpoint="ingest.lightstep.com:443",
    metric_exporter_endpoint="ingest.lightstep.com:443/metrics",
    log_level=debug,
    span_exporter_insecure=False,
    metric_exporter_insecure=False,
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
```

Set the environment variables:

```bash
export LS_SERVICE_NAME=auto-instrumentation-testing
export LS_ACCESS_TOKEN=<the access token>
```

Run the server:

```bash
cd ~
cd open-telemetry/opentelemetry-python/docs/examples/auto-instrumentation
opentelemetry-instrument python server_uninstrumented.py
```

Run the client in a separate console:

```bash
cd ~
cd open-telemetry/opentelemetry-python/docs/examples/auto-instrumentation
python client.py testing
```

This should produce spans that can be captured in the Lightstep Explorer Web UI.

### Configuration Options

|Config|Env Variable|Required|Default|
|------|------------|--------|-------|
|service_name                     |LS_SERVICE_NAME|y|-|
|service_version                  |LS_SERVICE_VERSION|n|unknown|
|access_token                     |LS_ACCESS_TOKEN|n|-|
|span_exporter_endpoint                    |OTEL_EXPORTER_OTLP_SPAN_ENDPOINT|n|ingest.lightstep.com:443|
|span_exporter_insecure  |OTEL_EXPORTER_OTLP_SPAN_INSECURE|n|False|
|metric_exporter_endpoint                  |OTEL_EXPORTER_OTLP_METRIC_ENDPOINT|n|ingest.lightstep.com:443/metrics|
|metric_exporter_insecure|OTEL_EXPORTER_OTLP_METRIC_INSECURE|n|False|
|propagator                       |OTEL_PROPAGATORS|n|b3|
|resource_attributes                  |OTEL_RESOURCE_ATTRIBUTES|n|-|
|log_level                        |OTEL_LOG_LEVEL|n|error|

### Principles behind Launcher

##### 100% interoperability with OpenTelemetry

One of the key principles behind putting together Launcher is to make lives of OpenTelemetry users easier, this means that there is no special configuration that **requires** users to install Launcher in order to use OpenTelemetry. It also means that any users of Launcher can leverage the flexibility of configuring OpenTelemetry as they need.

##### Opinionated configuration

Although we understand that not all languages use the same format for configuration, we find this annoying. We decided that Launcher would allow users to use the same configuration file across all languages. In this case, we settled for `YAML` as the format, which was inspired by the OpenTelemetry Collector.

##### Validation

Another decision we made with launcher is to provide end users with a layer of validation of their configuration. This provides us the ability to give feedback to our users faster, so they can start collecting telemetry sooner.

Start using it today in [Go](), [Java](https://github.com/lightstep/otel-launcher-java), [Javascript](https://github.com/lightstep/otel-launcher-node) and [Python](https://github.com/lightstep/otel-launcher-python) and let us know what you think!

------

*Made with* ![:heart:](https://a.slack-edge.com/production-standard-emoji-assets/10.2/apple-medium/2764-fe0f.png) *@ [Lightstep](http://lightstep.com/)*
