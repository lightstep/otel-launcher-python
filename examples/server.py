#!/usr/bin/env python3

from logging import basicConfig, debug, DEBUG

from flask import Flask, request
from opentelemetry.launcher import configure_opentelemetry
from opentelemetry.instrumentation.flask import FlaskInstrumentor


basicConfig(format="\033[94mSERVER:\033[0m %(message)s", level=DEBUG)


def receive_requests():
    configure_opentelemetry(
        service_name="server_service_name",
        service_version="server_version",  # optional
    )

    app = Flask(__name__)
    FlaskInstrumentor().instrument_app(app)

    @app.route("/shutdown")
    def shutdown():
        request.environ.get("werkzeug.server.shutdown")()
        debug("Server shut down")
        return "shutdown"

    @app.route("/hello")
    def hello():
        debug("Hello, client!")
        return "hello"

    app.run(host="0.0.0.0", port=8000)


if __name__ == "__main__":
    receive_requests()
