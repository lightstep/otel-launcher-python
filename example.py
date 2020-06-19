import requests
from opentelemetry.lightstep import get_tracer

tracer = get_tracer(
    service_name="service-123",
    service_version="1.2.3",  # optional
    # token="my-token",  # optional
    # satellite_url="ingest.lightstep.com:443",  # optional
    # debug=False,  # optional
)


with tracer.start_as_current_span("foo") as span:
    span.set_attribute("attr1", "valu1")
    with tracer.start_as_current_span("bar"):
        with tracer.start_as_current_span("baz"):
            requests.get("http://localhost:8000")
            print("Hello world from OpenTelemetry Python!")
