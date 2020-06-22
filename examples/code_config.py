from client import App
from opentelemetry.lightstep import get_tracer

tracer = get_tracer(
    service_name="service-123",
    service_version="1.2.3",  # optional
    token="my-token",  # optional
    satellite_url="ingest.lightstep.com:443",  # optional
    debug=False,  # optional
)

app = App(tracer)
app.send_requests()
