# Copyright Lightstep Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from logging import DEBUG, ERROR, basicConfig, getLogger
from typing import Optional

from environs import Env
from grpc import ssl_channel_credentials

from opentelemetry.lightstep.tracer import LightstepOTLPSpanExporter
from opentelemetry.lightstep.version import __version__
from opentelemetry.propagators import set_global_httptextformat
from opentelemetry.propagators.composite import CompositeHTTPPropagator
from opentelemetry.sdk.trace import Resource, TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchExportSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.sdk.trace.propagation.b3_format import B3Format
from opentelemetry.trace import get_tracer_provider, set_tracer_provider

_env = Env()

_DEFAULT_OTEL_EXPORTER_OTLP_SPAN_ENDPOINT = "ingest.lightstep.com:443"
_DEFAULT_OTEL_EXPORTER_OTLP_METRIC_ENDPOINT = (
    "ingest.lightstep.com:443/metrics"
)

_LS_ACCESS_TOKEN = _env.str("LS_ACCESS_TOKEN", None)
_OTEL_EXPORTER_OTLP_SPAN_ENDPOINT = _env.str(
    "OTEL_EXPORTER_OTLP_SPAN_ENDPOINT",
    _DEFAULT_OTEL_EXPORTER_OTLP_SPAN_ENDPOINT,
)
_OTEL_EXPORTER_OTLP_METRIC_ENDPOINT = _env.str(
    "OTEL_EXPORTER_OTLP_METRIC_ENDPOINT",
    _DEFAULT_OTEL_EXPORTER_OTLP_METRIC_ENDPOINT,
)
_LS_SERVICE_NAME = _env.str("LS_SERVICE_NAME", None)
_LS_SERVICE_VERSION = _env.str("LS_SERVICE_VERSION", "unknown")
_OTEL_PROPAGATORS = _env.list("OTEL_PROPAGATORS", ["b3"])
_OTEL_RESOURCE_LABELS = _env.dict(
    "OTEL_RESOURCE_LABELS",
    {
        "service.name": _LS_SERVICE_NAME,
        "service.version": _LS_SERVICE_VERSION,
        "telemetry.sdk.language": "python",
        "telemetry.sdk.version": __version__,
    },
)
_OTEL_LOG_LEVEL = _env.int("OTEL_LOG_LEVEL", ERROR)
_OTEL_EXPORTER_OTLP_SPAN_INSECURE = _env.bool(
    "OTEL_EXPORTER_OTLP_SPAN_INSECURE", False
)
_OTEL_EXPORTER_OTLP_METRIC_INSECURE = _env.bool(
    "OTEL_EXPORTER_OTLP_METRIC_INSECURE", False
)

_logger = getLogger(__name__)


class InvalidConfigurationError(Exception):
    """
    To be raised when an invalid configuration is attempted
    """


def configure_opentelemetry(
    access_token: str = _LS_ACCESS_TOKEN,
    span_endpoint: str = _OTEL_EXPORTER_OTLP_SPAN_ENDPOINT,
    metric_endpoint: str = _OTEL_EXPORTER_OTLP_METRIC_ENDPOINT,
    service_name: str = _LS_SERVICE_NAME,
    service_version: str = _LS_SERVICE_VERSION,
    propagator: list = _OTEL_PROPAGATORS,
    resource_labels: str = _OTEL_RESOURCE_LABELS,
    log_level: int = _OTEL_LOG_LEVEL,
    span_exporter_endpoint_insecure: bool = _OTEL_EXPORTER_OTLP_SPAN_INSECURE,
    metric_exporter_endpoint_insecure: bool = (
        _OTEL_EXPORTER_OTLP_METRIC_INSECURE
    ),
):
    """
    Configures OpenTelemetry with Lightstep environment variables

    This function works as a configuration layer that allows the Lightstep end
    user to use current environment variables seamlessly with OpenTelemetry. In
    this way, it is not needed to make any configuration changes to the
    environment before using OpenTelemetry. The configuration can be done via
    environment variables (prefixed with `LS`) or via arguments passed to this
    function. Each argument has a 1:1 correspondence with an environment
    variable, their description follows:

    Arguments:
        access_token (str): LS_ACCESS_TOKEN, the access token used to
            authenticate with the Lightstep satellite. This configuration value
            is mandatory.
        span_endpoint (str): OTEL_EXPORTER_OTLP_SPAN_ENDPOINT, the URL of the Lightstep
            satellite where the spans are to be exported. Defaults to
            `ingest.lightstep.com:443`.
        metric_endpoint (str): OTEL_EXPORTER_OTLP_METRIC_ENDPOINT, the URL of the metrics collector
            where the metrics are to be exported. Defaults to
            `ingest.lightstep.com:443/metrics`.
        service_name (str): LS_SERVICE_NAME, the name of the service that is
            used along with the access token to send spans to the Lighstep
            satellite. This configuration value is mandatory.
        service_version (str): LS_SERVICE_VERSION, the version of the service
            used to sernd spans to the Lightstep satellite. Defaults to
            `"unknown"`.
        propagator (list): OTEL_PROPAGATORS, a list of propagators to be used.
            Defaults to `["b3"]`.
        resource_labels (dict): OTEL_RESOURCE_LABELS, a dictionary of
            key value pairs used to instantiate the resouce of the tracer
            provider. Defaults to
            `{
                "service.name": _LS_SERVICE_NAME,
                "service.version": _LS_SERVICE_VERSION,
                "telemetry.sdk.language": "python",
                "telemetry.sdk.version": "0.9b0",
            }`
        log_level (int): OTEL_LOG_LEVEL, an int value that indicates the log
            level. Defaults to `logging.ERROR`.
        span_exporter_endpoint_insecure (bool):
            OTEL_EXPORTER_OTLP_SPAN_INSECURE, a boolean value that indicates if
            an insecure channel is to be used to send spans to the satellite.
            Defaults to `False`.
        metric_exporter_endpoint_insecure (bool):
            OTEL_EXPORTER_OTLP_METRIC_INSECURE, a boolean value that indicates
            if an insecure channel is to be used to send spans to the
            satellite. Defaults to `False`.
    """

    basicConfig(level=log_level)

    _logger.debug("configuration")

    for key, value in {
        "access_token": access_token,
        "span_endpoint": span_endpoint,
        "metric_endpoint": metric_endpoint,
        "service_name": service_name,
        "service_version": service_version,
        "propagator": propagator,
        "resource_labels": resource_labels,
        "log_level": log_level,
        "span_exporter_endpoint_insecure": span_exporter_endpoint_insecure,
        "metric_exporter_endpoint_insecure": metric_exporter_endpoint_insecure,
    }.items():
        _logger.debug("%s: %s", key, value)

    if not _validate_service_name(service_name):

        message = (
            "Invalid configuration: service name missing. "
            "Set environment variable LS_SERVICE_NAME or call "
            "configure_opentelemetry with service_name defined"
        )
        _logger.error(message)
        raise InvalidConfigurationError(message)

    if access_token is None:
        if span_endpoint == _DEFAULT_OTEL_EXPORTER_OTLP_SPAN_ENDPOINT:
            message = (
                "Invalid configuration: token missing. "
                "Must be set to send data to {}. "
                "Set environment variable LS_ACCESS_TOKEN or call"
                "configure_opentelemetry with access_token defined"
            ).format(_OTEL_EXPORTER_OTLP_SPAN_ENDPOINT)
            _logger.error(message)
            raise InvalidConfigurationError(message)

    if not _validate_token(access_token):
        message = (
            "Invalid configuration: invalid token. "
            "Token must be a 32, 84 or 104 character long string."
        )
        _logger.error(message)
        raise InvalidConfigurationError(message)

    _logger.debug("configuring propagation")

    # FIXME use entry points (instead of a dictionary) to locate propagator
    # classes
    set_global_httptextformat(
        CompositeHTTPPropagator(
            [{"b3": B3Format}[propagator] for propagator in _OTEL_PROPAGATORS]
        )
    )

    _logger.debug("configuring tracing")

    metadata = None

    if _env.str("OPENTELEMETRY_PYTHON_TRACER_PROVIDER", None) is None:
        # FIXME now that new values can be set in the global configuration
        # object, check for this object having a tracer_provider attribute, if
        # not, set it to "sdk_tracer_provider" instead of using
        # set_tracer_provider, this in order to avoid having more than one
        # method of setting configuration.
        set_tracer_provider(TracerProvider())

    if access_token != "":
        metadata = (("lightstep-access-token", access_token),)

    credentials = ssl_channel_credentials()

    if span_exporter_endpoint_insecure:
        credentials = None

    # FIXME Do the same for metrics when the OTLPMetricsExporter is in
    # OpenTelemetry.
    get_tracer_provider().add_span_processor(
        BatchExportSpanProcessor(
            LightstepOTLPSpanExporter(
                endpoint=span_endpoint,
                credentials=credentials,
                metadata=metadata,
            )
        )
    )

    get_tracer_provider().resource = Resource(resource_labels)

    if log_level == DEBUG:
        get_tracer_provider().add_span_processor(
            BatchExportSpanProcessor(ConsoleSpanExporter())
        )


def _validate_token(token: str):
    return len(token) in [32, 84, 104]


def _validate_service_name(service_name: Optional[str]):
    return service_name is not None
