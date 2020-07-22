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

from unittest import TestCase
from unittest.mock import patch, ANY
from time import sleep
from sys import version_info
from logging import DEBUG, WARNING

from opentelemetry.launcher.configuration import (
    configure_opentelemetry, InvalidConfigurationError
)
from opentelemetry import trace
from opentelemetry.sdk.trace.export import BatchExportSpanProcessor


class TestConfiguration(TestCase):
    def test_all_environment_variables_used(self):
        pass

    def test_no_service_name(self):
        with self.assertRaises(InvalidConfigurationError):
            with self.assertLogs(level="ERROR") as log:
                configure_opentelemetry()
                self.assertIn("service name missing", log.output[0])

    def test_no_token(self):
        with self.assertRaises(InvalidConfigurationError):
            with self.assertLogs(level="ERROR") as log:
                configure_opentelemetry(service_name="service-123")
                self.assertIn("token missing", log.output[0])

    class MockBatchExportSpanProcessor(BatchExportSpanProcessor):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, schedule_delay_millis=1, **kwargs)

    @patch(
        "opentelemetry.launcher.configuration.BatchExportSpanProcessor",
        new=MockBatchExportSpanProcessor
    )
    @patch("opentelemetry.launcher.tracer.LightstepOTLPSpanExporter.export")
    def test_only_service_name_and_token(self, mock_otlp_span_exporter):

        configure_opentelemetry(
            service_name="service_123", access_token="a" * 104
        )

        with trace.get_tracer_provider().get_tracer(
            __name__
        ).start_as_current_span("name"):
            pass

        # The worker thread in MockBatchExportSpanProcessor is configured to
        # wait 1ms before exporting. Sleeping here to give enough time to the
        # export method mock to be called.
        sleep(0.002)

        # 3.5 does not include the assert_called method.
        if (version_info.major, version_info.minor) == (3, 5):
            with self.assertRaises(AssertionError):
                mock_otlp_span_exporter.assert_not_called()
        else:
            mock_otlp_span_exporter.assert_called()

    @patch("opentelemetry.launcher.configuration.LightstepOTLPSpanExporter")
    def test_metadata(self, mock_otlp_span_exporter):

        configure_opentelemetry(
            service_name="service_123", access_token="a" * 104
        )

        mock_otlp_span_exporter.assert_called_with(
            endpoint="ingest.lightstep.com:443",
            credentials=ANY,
            metadata=(("lightstep-access-token", "a" * 104),),
        )

    def test_log_level(self):

        with self.assertLogs(level=DEBUG):
            configure_opentelemetry(
                service_name="service_123",
                access_token="a" * 104,
                log_level="DEBUG",
            )

        with self.assertRaises(AssertionError):
            with self.assertLogs(level=WARNING):
                configure_opentelemetry(
                    service_name="service_123",
                    access_token="a" * 104,
                    log_level="WARNING",
                )

        with self.assertLogs(level=DEBUG):
            configure_opentelemetry(
                service_name="service_123",
                access_token="a" * 104,
                log_level="DeBuG",
            )

        with self.assertRaises(AssertionError):
            with self.assertLogs(level=WARNING):
                configure_opentelemetry(
                    service_name="service_123",
                    access_token="a" * 104,
                    log_level="WaRNiNG",
                )
