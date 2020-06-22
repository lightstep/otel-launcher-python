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

import logging
import os
import sys

import opentelemetry.sdk.trace.propagation.b3_format as b3_format
from opentelemetry import propagators
from opentelemetry.propagators import composite
from opentelemetry.trace.propagation.tracecontexthttptextformat import (
    TraceContextHTTPTextFormat,
)

from .tracer import configure_tracing

_ENV_VAR_LS_ACCESS_TOKEN = "LS_ACCESS_TOKEN"
_ENV_VAR_LS_SERVICE_NAME = "LS_SERVICE_NAME"

_DEFAULT_SATELLITE_URL = "ingest.lightstep.com:443"
_ENV_VAR_LS_SATELLITE_URL = os.getenv(
    "LS_SATELLITE_URL", _DEFAULT_SATELLITE_URL
)
_DEFAULT_METRICS_URL = "ingest.lightstep.com:443/metrics"
_ENV_VAR_LS_METRICS_URL = os.getenv("LS_METRICS_URL", _DEFAULT_METRICS_URL)
_ENV_VAR_LS_SERVICE_VERSION = os.getenv("LS_SERVICE_VERSION", "unknown")
_ENV_VAR_LS_PROPAGATOR = os.getenv("LS_PROPAGATOR", "b3,tracecontext")
_ENV_VAR_LS_GLOBAL_TAGS = "LS_GLOBAL_TAGS"
_ENV_VAR_LS_DEBUG = os.getenv("LS_DEBUG", False)

logger = logging.getLogger(__name__)


def configure_propagators():
    logger.debug("configuring propagators")
    multiformat_propagator = composite.CompositeHTTPPropagator(
        [TraceContextHTTPTextFormat(), b3_format.B3Format()]
    )
    propagators.set_global_httptextformat(multiformat_propagator)


def configure_opentelemetry(
    service_name: str = None,
    service_version: str = _ENV_VAR_LS_SERVICE_VERSION,
    token: str = "",
    satellite_url: str = _DEFAULT_SATELLITE_URL,
    metrics_url: str = _DEFAULT_METRICS_URL,
    debug: bool = _ENV_VAR_LS_DEBUG,
):
    if service_name is None:
        logger.error("invalid configuration: missing service_name")
        sys.exit(1)

    if token == "":
        token = os.getenv(_ENV_VAR_LS_ACCESS_TOKEN, "")

    if token == "" and satellite_url == _DEFAULT_SATELLITE_URL:
        logger.error(
            "invalid configuration: missing token, must be set to send data to %s",
            _DEFAULT_SATELLITE_URL,
        )
        sys.exit(1)
    config = {
        "service_name": service_name,
        "service_version": service_version,
        "token": token,
        "satellite_url": satellite_url,
        "metrics_url": metrics_url,
        "debug": debug,
    }

    if debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("debug logging enabled")
        logger.debug("configuration")
        logger.debug("-------------")
        for key, value in config.items():
            logger.debug("{}: {}".format(key, value))
    configure_tracing(config)
    configure_propagators()
