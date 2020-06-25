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

from logging import DEBUG, basicConfig, getLogger
from typing import Optional

from environs import Env
from grpc import ssl_channel_credentials

from opentelemetry.ext.datadog.propagator import DatadogFormat
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
from opentelemetry.trace.propagation.tracecontexthttptextformat import (
    TraceContextHTTPTextFormat,
)

_env = Env()

_DEFAULT_LS_SATELLITE_URL = "ingest.lightstep.com:443"
_DEFAULT_LS_METRICS_URL = "ingest.lightstep.com:443/metrics"

_LS_ACCESS_TOKEN = _env.str("LS_ACCESS_TOKEN", None)
_LS_SATELLITE_URL = _env.str("LS_SATELLITE_URL", _DEFAULT_LS_SATELLITE_URL)
_LS_METRICS_URL = _env.str("LS_METRICS_URL", _DEFAULT_LS_METRICS_URL)
_LS_SERVICE_NAME = _env.str("LS_SERVICE_NAME", None)
_LS_SERVICE_VERSION = _env.str("LS_SERVICE_VERSION", "unknown")
_LS_PROPAGATOR = _env.list("LS_PROPAGATOR", ["tracecontext", "b3"])
_LS_RESOURCE_ATTRIBUTES = _env.dict(
    "LS_RESOURCE_ATTRIBUTES",
    {
        "service.name": _LS_SERVICE_NAME,
        "service.version": _LS_SERVICE_VERSION,
        "telemetry.sdk.language": "python",
        "telemetry.sdk.version": __version__,
    },
)
_LS_DEBUG = _env.bool("LS_DEBUG", False)
_LS_INSECURE = _env.bool("LS_INSECURE", False)

_logger = getLogger(__name__)


class InvalidConfigurationError(Exception):
    """
    To be raised when an invalid configuration is attempted
    """


def configure_opentelemetry(
    access_token: str = _LS_ACCESS_TOKEN,
    satellite_url: str = _LS_SATELLITE_URL,
    metrics_url: str = _LS_METRICS_URL,
    service_name: str = _LS_SERVICE_NAME,
    service_version: str = _LS_SERVICE_VERSION,
    propagator: list = _LS_PROPAGATOR,
    resource_attributes: str = _LS_RESOURCE_ATTRIBUTES,
    debug: bool = _LS_DEBUG,
    insecure: bool = _LS_INSECURE,
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
        satellite_url (str): LS_SATELLITE_URL, the URL of the Lightstep
            satellite where the spans are to be exported. Defaults to
            `ingest.lightstep.com:443`.
        metrics_url (str): LS_METRICS_URL, the URL of the metrics collector
            where the metrics are to be exported. Defaults to
            `ingest.lightstep.com:443/metrics`.
        service_name (str): LS_SERVICE_NAME, the name of the service that is
            used along with the access token to send spans to the Lighstep
            satellite. This configuration value is mandatory.
        service_version (str): LS_SERVICE_VERSION, the version of the service
            used to sernd spans to the Lightstep satellite. Defaults to
            `"unknown"`.
        propagator (str): LS_PROPAGATOR, a list of propagators to be used.
            Defaults to `["tracecontext", "b3"]`.
        resource_attributes (dict): LS_RESOURCE_ATTRIBUTES, a dictionary of
            key value pairs used to instantiate the resouce of the tracer
            provider. Defaults to
            `{
                "service.name": _LS_SERVICE_NAME,
                "service.version": _LS_SERVICE_VERSION,
                "telemetry.sdk.language": "python",
                "telemetry.sdk.version": "0.9b0",
            }`
        debug (bool): LS_DEBUG, a boolean value that indicates if debug
            information is to be printed. Defaults to `False`.
        insecure (bool): LS_INSECURE, a boolean value that indicates if an
            insecure channel is to be used to communicate with the satellite.
            Defaults to `False`.
    """

    if debug:
        basicConfig(level=DEBUG)

    _logger.debug("configuration")

    for key, value in {
        "access_token": access_token,
        "satellite_url": satellite_url,
        "metrics_url": metrics_url,
        "service_name": service_name,
        "service_version": service_version,
        "propagator": propagator,
        "resource_attributes": resource_attributes,
        "debug": debug,
        "insecure": insecure,
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

    if satellite_url == _DEFAULT_LS_SATELLITE_URL:
        if access_token is None:
            message = (
                "Invalid configuration: token missing. "
                "Must be set to send data to {}. "
                "Set environment variable LS_ACCESS_TOKEN or call"
                "configure_opentelemetry with access_token defined"
            ).format(_LS_SATELLITE_URL)
            _logger.error(message)
            raise InvalidConfigurationError(message)

        if not _validate_token(access_token):
            message = (
                "Invalid configuration: invalid token. "
                "Token must be a 104 character long string."
            )
            _logger.error(message)
            raise InvalidConfigurationError(message)

    _logger.debug("configuring propagation")

    # FIXME use entry points (instead of a dictionary) to locate propagator
    # classes
    set_global_httptextformat(
        CompositeHTTPPropagator(
            [
                {
                    "tracecontext": TraceContextHTTPTextFormat,
                    "b3": B3Format,
                    "datadog": DatadogFormat,
                }[propagator]
                for propagator in _LS_PROPAGATOR
            ]
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
        metadata = ("lightstep-access-token", access_token)

    # FIXME rename insecure to secure in order to avoid a negation
    if not insecure:
        credentials = ssl_channel_credentials()

    else:
        credentials = None

    # FIXME Do the same for metrics when the OTLPMetricsExporter is in
    # OpenTelemetry.
    get_tracer_provider().add_span_processor(
        BatchExportSpanProcessor(
            LightstepOTLPSpanExporter(
                endpoint=satellite_url,
                credentials=credentials,
                metadata=metadata,
            )
        )
    )

    get_tracer_provider().resource = Resource(resource_attributes)

    if debug:
        get_tracer_provider().add_span_processor(
            BatchExportSpanProcessor(ConsoleSpanExporter())
        )


def _validate_token(token: str):
    return len(token) == 104


def _validate_service_name(service_name: Optional[str]):
    return service_name is not None
