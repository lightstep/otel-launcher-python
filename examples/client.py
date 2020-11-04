from time import sleep

from requests import get

from opentelemetry.baggage import set_baggage, get_baggage
from opentelemetry.trace import get_tracer, get_current_span
from opentelemetry.launcher import configure_opentelemetry
from opentelemetry.instrumentation.requests import RequestsInstrumentor


def send_requests():

    RequestsInstrumentor().instrument()

    configure_opentelemetry(
        service_name="service-123",
        service_version="1.2.3",  # optional
        log_level="DEBUG",  # optional
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
        print("sending requests {}/{}".format(attempt + 1, attempts))
        print("current span: ", get_current_span())

        with tracer.start_as_current_span("foo"):
            print("current span: ", get_current_span())

            with tracer.start_as_current_span("add-attribute") as span:
                span.set_attribute("attr1", "valu1")

            print(
                "val: ",
                get_baggage("example", set_baggage("example", "value"))
            )

            with tracer.start_as_current_span("bar"):
                request("http://localhost:8000/hello")
                request("http://doesnotexist:8000")
                print("Hello world from OpenTelemetry Python!")

        sleep(1)


if __name__ == "__main__":
    send_requests()
