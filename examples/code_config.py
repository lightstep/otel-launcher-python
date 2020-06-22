from client import App
from opentelemetry import trace
from opentelemetry.lightstep import configure_opentelemetry

configure_opentelemetry(
    service_name="service-123",
    service_version="1.2.3",  # optional
    satellite_url="ingest.lightstep.com:443",  # optional
    debug=True,  # optional
)

app = App(trace.get_tracer(__name__))
app.send_requests()
