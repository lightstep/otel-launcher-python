#!/usr/bin/env python3

from time import sleep

from requests import get
from logging import basicConfig, debug, DEBUG

from opentelemetry.baggage import set_baggage, get_baggage
from opentelemetry.trace import get_tracer, get_current_span
from opentelemetry.launcher import configure_opentelemetry
from opentelemetry.instrumentation.requests import RequestsInstrumentor


basicConfig(format="\033[95mCLIENT:\033[0m %(message)s", level=DEBUG)


def send_requests():
    RequestsInstrumentor().instrument()

    configure_opentelemetry(
        service_name="client_service_name",
        service_version="client_version",  # optional
    )

    tracer = get_tracer(__name__)

    def request(url):
        with tracer.start_as_current_span("request to {}".format(url)) as span:
            try:
                get(url)
            except Exception as error:
                span.set_attribute("error", "true")
                span.record_exception(error)

    attempts = 10

    for attempt in range(attempts):
        debug("Sending requests %s/%s", attempt + 1, attempts)

        with tracer.start_as_current_span("foo"):
            debug("Current span: %s", get_current_span())

            with tracer.start_as_current_span("add-attribute") as span:
                span.set_attribute("attr1", "valu1")
                debug("Current span: %s", get_current_span())

            debug(
                "Baggage: %s",
                get_baggage("example", set_baggage("example", "value"))
            )

            with tracer.start_as_current_span("bar"):
                debug("Hello, server!")
                request("http://localhost:8000/hello")
                request("http://doesnotexist:8000")

        sleep(1)

    request("http://localhost:8000/shutdown")


if __name__ == "__main__":
    send_requests()
