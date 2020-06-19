from opentelemetry.lightstep import get_tracer

tracer = get_tracer(service_name="ls-sdk", debug=False,)


with tracer.start_as_current_span("foo") as span:
    span.set_attribute("attr1", "valu1")
    with tracer.start_as_current_span("bar"):
        with tracer.start_as_current_span("baz"):
            print("Hello world from OpenTelemetry Python!")
