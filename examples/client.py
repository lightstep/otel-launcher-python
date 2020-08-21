import logging
import requests

from opentelemetry import correlationcontext, trace
from opentelemetry.launcher import configure_opentelemetry
from opentelemetry.instrumentation.requests import RequestsInstrumentor

RequestsInstrumentor().instrument()


class App:
    def __init__(self, tracer):
        self._tracer = tracer

    def _request(self, url):
        with self._tracer.start_as_current_span(
            "request to {}".format(url)
        ) as span:
            try:
                requests.get(url)
            except Exception as e:
                span.set_attribute("error", "true")
                span.record_exception(e)

    def send_requests(self):
        self.get_current_span()
        with self._tracer.start_as_current_span("foo"):
            self.get_current_span()
            self.add_span_attribute()
            self.set_correlation()
            with self._tracer.start_as_current_span("bar"):
                self._request("http://localhost:8000/hello")
                self._request("http://doesnotexist:8000")
                print("Hello world from OpenTelemetry Python!")

    # example of adding an attribute to a span
    def add_span_attribute(self):
        with self._tracer.start_as_current_span("add-attribute") as span:
            span.set_attribute("attr1", "valu1")

    # example of getting the current span
    def get_current_span(self):
        span = trace.get_current_span()
        print("current span: ", span)

    # example of setting a correlation
    def set_correlation(self):
        ctx = correlationcontext.set_correlation("example", "value")
        print("val: ", correlationcontext.get_correlation("example", ctx))


configure_opentelemetry(
    service_name="service-123",
    service_version="1.2.3",  # optional
    log_level="DEBUG",  # optional
)

app = App(trace.get_tracer(__name__))
app.send_requests()
