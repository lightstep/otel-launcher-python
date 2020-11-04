#!/usr/bin/env python3

from flask import Flask
from opentelemetry.launcher import configure_opentelemetry
from opentelemetry.instrumentation.flask import FlaskInstrumentor


configure_opentelemetry(
    service_name="server-456",
    service_version="4.5.6",
    log_level="DEBUG",  # optional
)

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)


@app.route("/hello")
def hello():
    return "hello"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
