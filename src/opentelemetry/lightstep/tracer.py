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
import typing

import grpc

from opentelemetry import trace
from opentelemetry.ext.otlp.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import Resource, TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchExportSpanProcessor,
    ConsoleSpanExporter,
)

from .version import __version__

logger = logging.getLogger(__name__)


class InvalidConfigurationException(Exception):
    pass


def parse_global_tags():
    pass


def configure_tracing(config: typing.Dict):
    metadata = None

    if isinstance(trace.get_tracer_provider(), trace.DefaultTracerProvider):
        trace.set_tracer_provider(TracerProvider())

    if config.get("token") != "":
        metadata = (("lightstep-access-token", config.get("token")),)

    trace.get_tracer_provider().add_span_processor(
        BatchExportSpanProcessor(
            OTLPSpanExporter(
                endpoint=config.get("satellite_url"),
                credentials=grpc.ssl_channel_credentials(),
                metadata=metadata,
            )
        )
    )

    trace.get_tracer_provider().resource = Resource(
        {
            "service.name": config.get("service_name"),
            "service.version": config.get("service_version"),
            "telemetry.sdk.language": "python",
            "telemetry.sdk.version": __version__,
        }
    )

    if config.get("debug"):
        trace.get_tracer_provider().add_span_processor(
            BatchExportSpanProcessor(ConsoleSpanExporter())
        )
