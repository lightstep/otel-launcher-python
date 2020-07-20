from opentelemetry import trace
from opentelemetry.launcher import configure_opentelemetry

configure_opentelemetry()

tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("first") as span:
    print("hello")
