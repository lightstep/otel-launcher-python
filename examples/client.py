#!/usr/bin/env python3

from requests import get
from logging import basicConfig, debug, DEBUG
from sys import argv

from opentelemetry.baggage import set_baggage, get_baggage
from opentelemetry.trace import get_tracer, get_current_span
from opentelemetry.launcher import configure_opentelemetry
from opentelemetry.instrumentation.requests import RequestsInstrumentor


basicConfig(format="\033[95mCLIENT:\033[0m %(message)s", level=DEBUG)


def send_requests():
    RequestsInstrumentor().instrument()

    configure_opentelemetry(
        span_exporter_endpoint="https://ingest.lightstep.com:443",
        service_name="client_service_name",
        service_version="client_version",  # optional
    )

    tracer = get_tracer(__name__)

    identifier = argv[1]

    def request(url):
        with tracer.start_as_current_span("request to {}".format(url)) as span:
            try:
                get(url)
            except Exception as error:
                span.set_attribute("error", "true")
                span.record_exception(error)

    debug("Sending requests")

    with tracer.start_as_current_span("parent-{}".format(identifier)):
        debug("Current span: %s", get_current_span())

        with tracer.start_as_current_span(
            "child-0-{}".format(identifier)
        ) as span:
            span.set_attribute("attr1", "valu1")
            debug("Current span: %s", get_current_span())

        debug(
            "Baggage: %s",
            get_baggage("example", set_baggage("example", "value")),
        )

        with tracer.start_as_current_span("child-1-{}".format(identifier)):
            debug("Hello, server!")
            request("http://localhost:8000/hello")

        request("http://localhost:8000/shutdown")


if __name__ == "__main__":
    send_requests()
