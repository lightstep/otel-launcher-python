import requests


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
                span.record_error(e)

    def send_requests(self):
        with self._tracer.start_as_current_span("foo") as span:
            span.set_attribute("attr1", "valu1")
            with self._tracer.start_as_current_span("bar"):
                self._request("http://localhost:8000")
                self._request("http://doesnotexist:8000")
                print("Hello world from OpenTelemetry Python!")
