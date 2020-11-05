#!/usr/bin/env python3

import os

from flask import Flask, request

from opentelemetry.launcher import configure_opentelemetry
from opentelemetry.instrumentation.flask import FlaskInstrumentor


def receive_requests(environ_kwargs=None):
    if environ_kwargs is not None:
        os.environ = environ_kwargs

    configure_opentelemetry(
        service_name="server-456",
        service_version="4.5.6",
        log_level="DEBUG",  # optional
    )

    app = Flask(__name__)
    FlaskInstrumentor().instrument_app(app)

    @app.route("/shutdown")
    def shutdown():
        print("shutdown")
        request.environ.get("werkzeug.server.shutdown")()
        return "shutdown"

    @app.route("/hello")
    def hello():
        print("hello")
        return "hello"

    app.run(host="0.0.0.0", port=8000)


if __name__ == "__main__":
    receive_requests()
