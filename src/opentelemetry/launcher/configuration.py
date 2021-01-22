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
# pylint: disable=too-many-branches

from logging import (
    CRITICAL,
    DEBUG,
    ERROR,
    INFO,
    NOTSET,
    WARNING,
    basicConfig,
    getLevelName,
    getLogger,
)
from socket import gethostname
from typing import Optional

from environs import Env
from grpc import ssl_channel_credentials

from opentelemetry.baggage.propagation import BaggagePropagator
from opentelemetry.instrumentation.distro import BaseDistro
from opentelemetry.instrumentation.system_metrics import SystemMetrics
from opentelemetry.launcher.metrics import LightstepOTLPMetricsExporter
from opentelemetry.launcher.tracer import LightstepOTLPSpanExporter
from opentelemetry.launcher.version import __version__
from opentelemetry.metrics import (
    get_meter_provider,
    set_meter_provider,
)
from opentelemetry.propagators import set_global_textmap
from opentelemetry.propagators.composite import CompositeHTTPPropagator
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import Resource, TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchExportSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.propagators.b3 import B3Format
from opentelemetry.trace import get_tracer_provider, set_tracer_provider
from opentelemetry.trace.propagation.tracecontext import (
    TraceContextTextMapPropagator,
)

_env = Env()
_logger = getLogger(__name__)

_DEFAULT_OTEL_EXPORTER_OTLP_SPAN_ENDPOINT = "ingest.lightstep.com:443"
_DEFAULT_OTEL_EXPORTER_OTLP_METRIC_ENDPOINT = "ingest.lightstep.com:443"

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
_LS_SERVICE_VERSION = _env.str("LS_SERVICE_VERSION", None)
_LS_METRICS_ENABLED = _env.bool("LS_METRICS_ENABLED", True)
_OTEL_PROPAGATORS = _env.str("OTEL_PROPAGATORS", "b3")
_OTEL_RESOURCE_ATTRIBUTES = _env.str(
    "OTEL_RESOURCE_ATTRIBUTES",
    "telemetry.sdk.language=python,"
    "telemetry.sdk.version={}".format(__version__),
)
_OTEL_LOG_LEVEL = _env.str("OTEL_LOG_LEVEL", "ERROR")
_OTEL_EXPORTER_OTLP_SPAN_INSECURE = _env.bool(
    "OTEL_EXPORTER_OTLP_SPAN_INSECURE", False
)
_OTEL_EXPORTER_OTLP_METRIC_INSECURE = _env.bool(
    "OTEL_EXPORTER_OTLP_METRIC_INSECURE", False
)

# FIXME Find a way to "import" this value from:
# https://github.com/open-telemetry/opentelemetry-collector/blob/master/translator/conventions/opentelemetry.go
# instead of hardcoding it here.
_ATTRIBUTE_HOST_NAME = "host.name"


class InvalidConfigurationError(Exception):
    """
    To be raised when an invalid configuration is attempted
    """


def _common_configuration(
    provider_setter, provider_class, environment_variable, insecure
):
    if _env.str(environment_variable, None) is None:
        # FIXME now that new values can be set in the global configuration
        # object, check for this object having a tracer_provider attribute,
        # if not, set it to "sdk_tracer_provider" instead of using
        # set_x_provider, this in order to avoid having more than one
        # method of setting configuration.
        provider_setter(provider_class())

    if insecure:
        credentials = None
    else:
        credentials = ssl_channel_credentials()

    return credentials


def configure_opentelemetry(
    access_token: str = _LS_ACCESS_TOKEN,
    span_exporter_endpoint: str = _OTEL_EXPORTER_OTLP_SPAN_ENDPOINT,
    metric_exporter_endpoint: str = _OTEL_EXPORTER_OTLP_METRIC_ENDPOINT,
    service_name: str = _LS_SERVICE_NAME,
    service_version: str = _LS_SERVICE_VERSION,
    propagators: str = _OTEL_PROPAGATORS,
    resource_attributes: str = _OTEL_RESOURCE_ATTRIBUTES,
    log_level: str = _OTEL_LOG_LEVEL,
    span_exporter_insecure: bool = _OTEL_EXPORTER_OTLP_SPAN_INSECURE,
    metric_exporter_insecure: bool = _OTEL_EXPORTER_OTLP_METRIC_INSECURE,
    system_metrics_config: dict = None,
    metrics_enabled: bool = _LS_METRICS_ENABLED,
    _auto_instrumented: bool = False,
):
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements
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
        span_exporter_endpoint (str): OTEL_EXPORTER_OTLP_SPAN_ENDPOINT, the URL of the Lightstep
            satellite where the spans are to be exported. Defaults to
            `ingest.lightstep.com:443`.
        metric_exporter_endpoint (str): OTEL_EXPORTER_OTLP_METRIC_ENDPOINT, the URL of the metrics collector
            where the metrics are to be exported. Defaults to
            `ingest.lightstep.com:443/metrics`.
        service_name (str): LS_SERVICE_NAME, the name of the service that is
            used along with the access token to send spans to the Lighstep
            satellite. This configuration value is mandatory.
        service_version (str): LS_SERVICE_VERSION, the version of the service
            used to sernd spans to the Lightstep satellite. Defaults to `None`.
        propagators (str): OTEL_PROPAGATORS, a list of propagators to be used.
            The list is specified as a comma-separated string of values, for
            example: `a,b,c,d,e,f`. Defaults to `b3`.
        resource_attributes (str): OTEL_RESOURCE_ATTRIBUTES, a dictionary of
            key value pairs used to instantiate the resouce of the tracer
            provider. The dictionary is specified as a string of
            comma-separated `key=value` pairs. For example: `a=1,b=2,c=3`.
            Defaults to
            `telemetry.sdk.language=python,telemetry.sdk.version=X` where `X`
            is the version of this package.
        log_level (str): OTEL_LOG_LEVEL, one of:

            - `NOTSET` (0)
            - `DEBUG` (10)
            - `INFO` (20)
            - `WARNING` (30)
            - `ERROR` (40)
            - `CRITICAL` (50)

            Defaults to `logging.ERROR`.
        span_exporter_insecure (bool):
            OTEL_EXPORTER_OTLP_SPAN_INSECURE, a boolean value that indicates if
            an insecure channel is to be used to send spans to the satellite.
            Defaults to `False`.
        metric_exporter_insecure (bool):
            OTEL_EXPORTER_OTLP_METRIC_INSECURE, a boolean value that indicates
            if an insecure channel is to be used to send spans to the
            satellite. Defaults to `False`.
        system_metrics_config (dict):
            Configuration for the SystemMetrics instrumentation
    """

    log_levels = {
        "NOTSET": NOTSET,
        "DEBUG": DEBUG,
        "INFO": INFO,
        "WARNING": WARNING,
        "ERROR": ERROR,
        "CRITICAL": CRITICAL,
    }

    # No environment variable is passed here as the first argument since what
    # is intended here is just to parse the value of the already obtained value
    # of the environment variables OTEL_PROPAGATORS and
    # OTEL_RESOURCE_ATTRIBUTES into a list and a dictionary. This is not done
    # at the attribute declaration to avoid having mutable objects as default
    # arguments.
    propagators = _env.list("", propagators)
    resource_attributes = _env.dict("", resource_attributes)

    log_level = log_level.upper()

    if log_level not in log_levels.keys():

        message = (
            "Invalid configuration: invalid log_level value."
            "It must be one of {}.".format(", ".join(log_levels.keys()))
        )
        _logger.error(message)
        raise InvalidConfigurationError(message)

    log_level = log_levels[log_level]

    basicConfig(level=log_level)

    _logger.debug("configuration")

    if not _validate_service_name(service_name):

        message = (
            "Invalid configuration: service name missing. "
            "Set environment variable LS_SERVICE_NAME"
        )

        if not _auto_instrumented:
            message += (
                " or call configure_opentelemetry with service_name defined"
            )
        _logger.error(message)
        raise InvalidConfigurationError(message)

    resource_attributes["service.name"] = service_name

    logged_attributes = {
        "access_token": access_token,
        "span_exporter_endpoint": span_exporter_endpoint,
        "metric_exporter_endpoint": metric_exporter_endpoint,
        "service_name": service_name,
        "propagators": propagators,
        "resource_attributes": resource_attributes,
        "log_level": getLevelName(log_level),
        "span_exporter_insecure": span_exporter_insecure,
        "metric_exporter_insecure": metric_exporter_insecure,
    }

    if service_version is not None:
        resource_attributes["service.version"] = service_version
        logged_attributes["service_version"] = service_version

    for key, value in logged_attributes.items():
        _logger.debug("%s: %s", key, value)

    if access_token is None:
        if span_exporter_endpoint == _DEFAULT_OTEL_EXPORTER_OTLP_SPAN_ENDPOINT:
            message = (
                "Invalid configuration: token missing. "
                "Must be set to send data to {}. "
                "Set environment variable LS_ACCESS_TOKEN"
            ).format(_OTEL_EXPORTER_OTLP_SPAN_ENDPOINT)
            if not _auto_instrumented:
                message += " or call configure_opentelemetry with access_token defined"
            _logger.error(message)
            raise InvalidConfigurationError(message)

    if access_token is not None and not _validate_token(access_token):
        message = (
            "Invalid configuration: invalid token. "
            "Token must be a 32, 84 or 104 character long string."
        )
        _logger.error(message)
        raise InvalidConfigurationError(message)

    _logger.debug("configuring propagation")

    # FIXME use entry points (instead of a dictionary) to locate propagator
    # classes
    set_global_textmap(
        CompositeHTTPPropagator(
            [
                {
                    "b3": B3Format(),
                    "baggage": BaggagePropagator(),
                    "tracecontext": TraceContextTextMapPropagator(),
                }[propagator]
                for propagator in propagators
            ]
        )
    )

    headers = None

    if access_token != "":
        headers = (("lightstep-access-token", access_token),)

    _logger.debug("configuring tracing")

    credentials = _common_configuration(
        set_tracer_provider,
        TracerProvider,
        "OTEL_PYTHON_TRACER_PROVIDER",
        span_exporter_insecure,
    )

    # FIXME Do the same for metrics when the OTLPMetricsExporter is in
    # OpenTelemetry.
    get_tracer_provider().add_span_processor(
        BatchExportSpanProcessor(
            LightstepOTLPSpanExporter(
                endpoint=span_exporter_endpoint,
                credentials=credentials,
                headers=headers,
            )
        )
    )

    if _ATTRIBUTE_HOST_NAME not in resource_attributes.keys() or not (
        resource_attributes[_ATTRIBUTE_HOST_NAME]
    ):

        no_hostname_message = (
            "set it with the environment variable OTEL_RESOURCE_ATTRIBUTES or "
            'with the resource_attributes argument. Use "host.name" as key '
            "in both cases."
        )
        try:
            hostname = gethostname()
            if not hostname:
                _logger.warning("Hostname is empty, %s", no_hostname_message)
            else:
                resource_attributes[_ATTRIBUTE_HOST_NAME] = hostname
        # pylint: disable=broad-except
        except Exception:
            _logger.exception(
                "Unable to get hostname, %s", no_hostname_message
            )

    get_tracer_provider().resource = Resource(resource_attributes)

    if log_level >= DEBUG:
        get_tracer_provider().add_span_processor(
            BatchExportSpanProcessor(ConsoleSpanExporter())
        )

    if metrics_enabled:

        _logger.debug("configuring metrics")

        credentials = _common_configuration(
            set_meter_provider,
            MeterProvider,
            "OTEL_PYTHON_METER_PROVIDER",
            metric_exporter_insecure,
        )

        lightstep_otlp_metrics_exporter = LightstepOTLPMetricsExporter(
            endpoint=metric_exporter_endpoint,
            credentials=credentials,
            headers=headers,
        )

        system_metrics = SystemMetrics(
            lightstep_otlp_metrics_exporter, system_metrics_config
        )
        get_meter_provider().start_pipeline(
            system_metrics.accumulator,
            lightstep_otlp_metrics_exporter,
            5,
        )

        get_meter_provider().resource = Resource(resource_attributes)


def _validate_token(token: str):
    return len(token) in [32, 84, 104]


def _validate_service_name(service_name: Optional[str]):
    return service_name is not None


class LightstepLauncherDistro(BaseDistro):
    def _configure(self, **kwargs):
        try:
            configure_opentelemetry(_auto_instrumented=True)
        except InvalidConfigurationError:
            _logger.exception(
                (
                    "application instrumented via opentelemetry-instrument. "
                    "all required configuration must be set via environment "
                    "variables"
                )
            )
