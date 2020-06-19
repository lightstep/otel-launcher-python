import grpc
import logging
import os
import sys

from opentelemetry import trace
from opentelemetry.ext.otlp.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import Resource, TracerProvider
from opentelemetry.sdk.trace.export import (
    ConsoleSpanExporter,
    SimpleExportSpanProcessor,
)

_ENV_VAR_LS_DEBUG = "LS_DEBUG"
_ENV_VAR_LS_ACCESS_TOKEN = "LS_ACCESS_TOKEN"

_DEFAULT_SATELLITE_URL = "ingest.lightstep.com:443"
_DEFAULT_SERVICE_VERSION = "unknown"

logger = logging.getLogger("opentelemetry.lightstep")


class InvalidConfigurationException(Exception):
    pass


def get_tracer(
    service_name: str = None,
    service_version: str = _DEFAULT_SERVICE_VERSION,
    token: str = "",
    satellite_url: str = _DEFAULT_SATELLITE_URL,
    debug: bool = False,
):
    if service_name is None:
        logger.error("invalid configuration: missing service_name")
        sys.exit(1)
    trace.set_tracer_provider(TracerProvider())

    if token == "":
        token = os.getenv(_ENV_VAR_LS_ACCESS_TOKEN, "")

    if token == "" and satellite_url == _DEFAULT_SATELLITE_URL:
        logger.error("token must be set to send data to %s", _DEFAULT_SATELLITE_URL)
        sys.exit(1)

    if debug or os.getenv(_ENV_VAR_LS_DEBUG, False):
        trace.get_tracer_provider().add_span_processor(
            SimpleExportSpanProcessor(ConsoleSpanExporter())
        )

    metadata = None
    if token != "":
        metadata = (("lightstep-access-token", token),)

    trace.get_tracer_provider().add_span_processor(
        SimpleExportSpanProcessor(
            OTLPSpanExporter(
                endpoint=satellite_url,
                credentials=grpc.ssl_channel_credentials(),
                metadata=metadata,
            )
        )
    )
    trace.get_tracer_provider().resource = Resource(
        {"service.name": service_name, "service.version": service_version,}
    )
    return trace.get_tracer(__name__)
