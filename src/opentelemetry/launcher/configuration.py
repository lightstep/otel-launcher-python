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
from pkg_resources import iter_entry_points

from opentelemetry.instrumentation.distro import BaseDistro
from opentelemetry.launcher.tracer import LightstepOTLPSpanExporter
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.sdk.trace import Resource, TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.trace import get_tracer_provider, set_tracer_provider

_env = Env()
_logger = getLogger(__name__)

_DEFAULT_OTEL_EXPORTER_OTLP_TRACES_ENDPOINT = (
    "https://ingest.lightstep.com:443"
)

_LS_ACCESS_TOKEN = _env.str("LS_ACCESS_TOKEN", None)
_OTEL_EXPORTER_OTLP_TRACES_ENDPOINT = _env.str(
    "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
    # FIXME Remove support for the backup OTEL_EXPORTER_OTLP_SPAN_ENDPOINT
    # environment variable when appropriate.
    _env.str(
        "OTEL_EXPORTER_OTLP_SPAN_ENDPOINT",
        _DEFAULT_OTEL_EXPORTER_OTLP_TRACES_ENDPOINT,
    ),
)
_LS_SERVICE_NAME = _env.str("LS_SERVICE_NAME", None)
_LS_SERVICE_VERSION = _env.str("LS_SERVICE_VERSION", None)
_OTEL_PROPAGATORS = _env.str("OTEL_PROPAGATORS", "b3multi")
_OTEL_RESOURCE_ATTRIBUTES = _env.str("OTEL_RESOURCE_ATTRIBUTES", "")
_OTEL_LOG_LEVEL = _env.str("OTEL_LOG_LEVEL", "ERROR")
_OTEL_EXPORTER_OTLP_TRACES_INSECURE = _env.bool(
    "OTEL_EXPORTER_OTLP_TRACES_INSECURE", False
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
    span_exporter_endpoint: str = _OTEL_EXPORTER_OTLP_TRACES_ENDPOINT,
    service_name: str = _LS_SERVICE_NAME,
    service_version: str = _LS_SERVICE_VERSION,
    propagators: str = _OTEL_PROPAGATORS,
    resource_attributes: str = _OTEL_RESOURCE_ATTRIBUTES,
    log_level: str = _OTEL_LOG_LEVEL,
    span_exporter_insecure: bool = _OTEL_EXPORTER_OTLP_TRACES_INSECURE,
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
        span_exporter_endpoint (str): OTEL_EXPORTER_OTLP_TRACES_ENDPOINT, the
            URL of the Lightstep satellite where the spans are to be exported.
            Defaults to `ingest.lightstep.com:443`.
        service_name (str): LS_SERVICE_NAME, the name of the service that is
            used along with the access token to send spans to the Lighstep
            satellite. This configuration value is mandatory.
        service_version (str): LS_SERVICE_VERSION, the version of the service
            used to sernd spans to the Lightstep satellite. Defaults to `None`.
        propagators (str): OTEL_PROPAGATORS, a list of propagators to be used.
            The list is specified as a comma-separated string of values, for
            example: `a,b,c,d,e,f`. Defaults to `b3multi`.
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
            OTEL_EXPORTER_OTLP_TRACES_INSECURE, a boolean value that indicates
            if an insecure channel is to be used to send spans to the
            satellite. Defaults to `False`.
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
            f"Invalid configuration: invalid log_level value. "
            f"It must be one of {', '.join(log_levels.keys())}"
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

    if access_token is None:
        if (
            span_exporter_endpoint
            == _DEFAULT_OTEL_EXPORTER_OTLP_TRACES_ENDPOINT
        ):
            message = (
                f"Invalid configuration: token missing. "
                f"Must be set to send data to "
                f"{_OTEL_EXPORTER_OTLP_TRACES_ENDPOINT}."
                f"Set environment variable LS_ACCESS_TOKEN"
            )
            if not _auto_instrumented:
                message += (
                    " or call configure_opentelemetry "
                    "with access_token defined"
                )
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

    propagator_instances = []

    for propagator in propagators:

        try:
            propagator_instance = next(
                iter_entry_points("opentelemetry_propagator", name=propagator),
            ).load()()
        # pylint: disable=broad-except
        except Exception:
            _logger.exception(
                "Unable to instantiate propagator %s", propagator
            )
            continue

        propagator_instances.append(propagator_instance)

    set_global_textmap(CompositePropagator(propagator_instances))

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

    get_tracer_provider().add_span_processor(
        BatchSpanProcessor(
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

    tracer_provider = get_tracer_provider()

    if isinstance(tracer_provider, TracerProvider):

        # FIXME: Accessing a private attribute here because resource is no
        # longer settable since:
        # https://github.com/open-telemetry/opentelemetry-python/pull/1652
        # The provider resource can now only be set when the provider is
        # instantiated, which is too soon for this launcher as it is now.
        # pylint: disable=protected-access
        resource = tracer_provider._resource

        if service_name is not None:
            if "service.name" in resource.attributes.keys():
                _logger.warning(
                    "service.name is already defined in the resource "
                    "attributes, overriding with %s",
                    service_name,
                )
            resource_attributes["service.name"] = service_name

        if service_version is not None:
            if "service.version" in resource.attributes.keys():
                _logger.warning(
                    "service.version is already defined in the resource "
                    "attributes, overriding with %s",
                    service_version,
                )
            resource_attributes["service.version"] = service_version

        resource_attributes_copy = resource.attributes.copy()
        resource_attributes_copy.update(resource_attributes)

        get_tracer_provider()._resource = Resource(resource_attributes_copy)

    logged_attributes = {
        "access_token": access_token,
        "span_exporter_endpoint": span_exporter_endpoint,
        "service_name": service_name,
        "propagators": propagators,
        "resource_attributes": resource_attributes,
        "log_level": getLevelName(log_level),
        "span_exporter_insecure": span_exporter_insecure,
    }

    logged_attributes.update(resource_attributes)

    for key, value in logged_attributes.items():
        _logger.debug("%s: %s", key, value)

    if log_level <= DEBUG:
        get_tracer_provider().add_span_processor(
            BatchSpanProcessor(ConsoleSpanExporter())
        )


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
