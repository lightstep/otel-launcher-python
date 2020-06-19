import grpc
import logging
import os
import sys

# from dynaconf import settings

from opentelemetry import propagators, trace
from opentelemetry.propagators import composite
import opentelemetry.sdk.trace.propagation.b3_format as b3_format
from opentelemetry.trace.propagation.tracecontexthttptextformat import (
    TraceContextHTTPTextFormat,
)
from opentelemetry.ext.otlp.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import Resource, TracerProvider
from opentelemetry.sdk.trace.export import (
    ConsoleSpanExporter,
    SimpleExportSpanProcessor,
)

_ENV_VAR_LS_ACCESS_TOKEN = "LS_ACCESS_TOKEN"
_ENV_VAR_LS_SATELLITE_URL = "LS_SATELLITE_URL"
_ENV_VAR_LS_METRICS_URL = "LS_METRICS_URL"
_ENV_VAR_LS_SERVICE_NAME = "LS_SERVICE_NAME"
_ENV_VAR_LS_SERVICE_VERSION = "LS_SERVICE_VERSION"
_ENV_VAR_LS_PROPAGATOR = "LS_PROPAGATOR"
_ENV_VAR_LS_GLOBAL_TAGS = "LS_GLOBAL_TAGS"
_ENV_VAR_LS_DEBUG = "LS_DEBUG"

_DEFAULT_SATELLITE_URL = "ingest.lightstep.com:443"
_DEFAULT_SERVICE_VERSION = "unknown"

logger = logging.getLogger("opentelemetry.lightstep")


class InvalidConfigurationException(Exception):
    pass


def configure_propagators():
    multiformat_propagator = composite.CompositeHTTPPropagator(
        [TraceContextHTTPTextFormat(), b3_format.B3Format()]
    )
    propagators.set_global_httptextformat(multiformat_propagator)


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

    if trace.get_tracer_provider() is trace.DefaultTracerProvider:
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
    configure_propagators()

    return trace.get_tracer(__name__)
