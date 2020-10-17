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
from unittest.mock import patch, ANY, Mock
from time import sleep
from sys import version_info
from logging import DEBUG, WARNING

from opentelemetry.launcher.configuration import (
    configure_opentelemetry,
    _logger,
    InvalidConfigurationError,
    _ATTRIBUTE_HOST_NAME,
)
from opentelemetry.launcher.version import __version__
from opentelemetry import baggage, trace
from opentelemetry.propagators import get_global_textmap
from opentelemetry.sdk.trace.export import BatchExportSpanProcessor
from opentelemetry.trace import get_tracer_provider, set_tracer_provider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.metrics import get_meter_provider, set_meter_provider


class TestConfiguration(TestCase):
    def test_all_environment_variables_used(self):
        pass

    def tearDown(self):
        get_tracer_provider().shutdown()
        get_meter_provider().shutdown()

    @classmethod
    def setUpClass(cls):
        set_tracer_provider(TracerProvider())
        set_meter_provider(MeterProvider())

    @patch("opentelemetry.launcher.configuration.LightstepOTLPMetricsExporter")
    def test_no_service_name(self, mock_otlp_metrics_exporter):
        with self.assertRaises(InvalidConfigurationError):
            with self.assertLogs(logger=_logger, level="ERROR") as log:
                configure_opentelemetry()
                self.assertIn("service name missing", log.output[0])

    def test_no_token(self):
        with self.assertRaises(InvalidConfigurationError):
            with self.assertLogs(logger=_logger, level="ERROR") as log:
                configure_opentelemetry(service_name="service-123")
                self.assertIn("token missing", log.output[0])

    @patch("opentelemetry.launcher.configuration.LightstepOTLPMetricsExporter")
    def test_no_token_other_endpoint(self, mock_otlp_metrics_exporter):
        # no exception is thrown
        configure_opentelemetry(
            service_name="service-123",
            span_exporter_endpoint="localhost:1234",
        )

    class MockBatchExportSpanProcessor(BatchExportSpanProcessor):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, schedule_delay_millis=1, **kwargs)

    @patch(
        "opentelemetry.launcher.configuration.BatchExportSpanProcessor",
        new=MockBatchExportSpanProcessor,
    )
    @patch("opentelemetry.launcher.configuration.LightstepOTLPMetricsExporter")
    @patch("opentelemetry.launcher.tracer.LightstepOTLPSpanExporter.export")
    def test_only_service_name_and_token(
        self, mock_otlp_span_exporter, mock_otlp_metrics_exporter
    ):

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
    @patch("opentelemetry.launcher.configuration.LightstepOTLPMetricsExporter")
    def test_metadata(
        self, mock_otlp_metrics_exporter, mock_otlp_span_exporter
    ):

        configure_opentelemetry(
            service_name="service_123", access_token="a" * 104
        )

        mock_otlp_span_exporter.assert_called_with(
            endpoint="ingest.lightstep.com:443",
            credentials=ANY,
            metadata=(("lightstep-access-token", "a" * 104),),
        )

    @patch("opentelemetry.launcher.configuration.LightstepOTLPMetricsExporter")
    def test_log_level(self, mock_otlo_metrics_exporter):

        with self.assertLogs(logger=_logger, level=DEBUG):
            configure_opentelemetry(
                service_name="service_123",
                access_token="a" * 104,
                log_level="DEBUG",
            )

        with self.assertRaises(AssertionError):
            with self.assertLogs(logger=_logger, level=WARNING):
                configure_opentelemetry(
                    service_name="service_123",
                    access_token="a" * 104,
                    log_level="WARNING",
                )

        with self.assertLogs(logger=_logger, level=DEBUG):
            configure_opentelemetry(
                service_name="service_123",
                access_token="a" * 104,
                log_level="DeBuG",
            )

        with self.assertRaises(AssertionError):
            with self.assertLogs(logger=_logger, level=WARNING):
                configure_opentelemetry(
                    service_name="service_123",
                    access_token="a" * 104,
                    log_level="WaRNiNG",
                )

    @patch("opentelemetry.launcher.configuration.LightstepOTLPMetricsExporter")
    @patch("opentelemetry.launcher.configuration.gethostname")
    @patch("opentelemetry.launcher.configuration.Resource")
    def test_resource_attributes(
        self, mock_resource, mock_gethostname, mock_otlp_metrics_exporter
    ):
        mock_gethostname.return_value = "the_hostname"

        configure_opentelemetry(
            service_name="service_name",
            service_version="service_version",
            access_token="a" * 104,
        )

        mock_resource.assert_called_with(
            {
                "telemetry.sdk.language": "python",
                "telemetry.sdk.version": __version__,
                "service.name": "service_name",
                "service.version": "service_version",
                _ATTRIBUTE_HOST_NAME: "the_hostname",
            }
        )

    @patch("opentelemetry.launcher.configuration.LightstepOTLPMetricsExporter")
    @patch("opentelemetry.launcher.configuration.gethostname")
    @patch("opentelemetry.launcher.configuration.Resource")
    def test_service_version(
        self, mock_resource, mock_gethostname, mock_otlp_metrics_exporter
    ):
        mock_gethostname.return_value = "the_hostname"

        configure_opentelemetry(
            service_name="service_name",
            access_token="a" * 104,
        )

        mock_resource.assert_called_with(
            {
                "telemetry.sdk.language": "python",
                "telemetry.sdk.version": __version__,
                "service.name": "service_name",
                _ATTRIBUTE_HOST_NAME: "the_hostname",
            }
        )

    @patch("opentelemetry.launcher.configuration.LightstepOTLPMetricsExporter")
    def test_propagation(self, mock_otlp_metrics_exporter):
        configure_opentelemetry(
            service_name="service_name",
            service_version="service_version",
            access_token="a" * 104,
        )

        with trace.get_tracer(__name__).start_as_current_span("test") as span:
            ctx = baggage.set_baggage("abc", "def")
            prop = get_global_textmap()
            carrier = {}
            prop.inject(dict.__setitem__, carrier, context=ctx)
            self.assertEqual(
                format(span.get_span_context().trace_id, "032x"),
                carrier.get("x-b3-traceid"),
            )
            self.assertIsNone(carrier.get("baggage"))

    def test_propagation_baggage(self):
        configure_opentelemetry(
            service_name="service_name",
            service_version="service_version",
            access_token="a" * 104,
            propagators="baggage",
        )

        with trace.get_tracer(__name__).start_as_current_span("test"):
            ctx = baggage.set_baggage("abc", "def")
            prop = get_global_textmap()
            carrier = {}
            prop.inject(dict.__setitem__, carrier, context=ctx)
            self.assertIsNone(carrier.get("x-b3-traceid"))
            self.assertEqual(carrier.get("baggage"), "abc=def")

    def test_propagation_tracecontext(self):
        configure_opentelemetry(
            service_name="service_name",
            service_version="service_version",
            access_token="a" * 104,
            propagators="tracecontext",
        )

        with trace.get_tracer(__name__).start_as_current_span("test") as span:
            ctx = baggage.set_baggage("abc", "def")
            prop = get_global_textmap()
            carrier = {}
            prop.inject(dict.__setitem__, carrier, context=ctx)
            self.assertIn(
                "00-{}".format(
                    format(span.get_span_context().trace_id, "032x")
                ),
                carrier.get("traceparent"),
            )

    def test_propagation_multiple(self):
        configure_opentelemetry(
            service_name="service_name",
            service_version="service_version",
            access_token="a" * 104,
            propagators="b3,baggage,tracecontext",
        )

        with trace.get_tracer(__name__).start_as_current_span("test") as span:
            ctx = baggage.set_baggage("abc", "def")
            prop = get_global_textmap()
            carrier = {}
            prop.inject(dict.__setitem__, carrier, context=ctx)
            self.assertEqual(
                format(span.get_span_context().trace_id, "032x"),
                carrier.get("x-b3-traceid"),
            )
            self.assertEqual(carrier.get("baggage"), "abc=def")
            self.assertIn(
                "00-{}".format(
                    format(span.get_span_context().trace_id, "032x")
                ),
                carrier.get("traceparent"),
            )

    @patch("opentelemetry.launcher.configuration.gethostname")
    @patch("opentelemetry.launcher.configuration.Resource")
    def test_hostname(self, mock_resource, mock_gethostname):

        mock_gethostname.return_value = "the_hostname"

        configure_opentelemetry(
            service_name="service_name",
            access_token="a" * 104,
        )

        mock_resource.assert_called_with(
            {
                "telemetry.sdk.language": "python",
                "telemetry.sdk.version": __version__,
                "service.name": "service_name",
                _ATTRIBUTE_HOST_NAME: "the_hostname",
            }
        )

        configure_opentelemetry(
            service_name="service_name",
            access_token="a" * 104,
            resource_attributes="{}=other_hostname".format(
                _ATTRIBUTE_HOST_NAME
            )
        )

        mock_resource.assert_called_with(
            {
                "service.name": "service_name",
                _ATTRIBUTE_HOST_NAME: "other_hostname",
            }
        )

    @patch("opentelemetry.launcher.configuration.LightstepOTLPMetricsExporter")
    @patch("opentelemetry.launcher.configuration.LightstepOTLPSpanExporter")
    @patch("opentelemetry.launcher.configuration._common_configuration")
    def test_metric_configuration(
        self,
        mock_common_configuration,
        mock_otlp_span_exporter,
        mock_otlp_metrics_exporter,
    ):

        credentials_mock = Mock()
        mock_common_configuration.return_value = credentials_mock

        configure_opentelemetry(
            service_name="service_name",
            service_version="service_version",
            access_token="a" * 104,
            metric_exporter_endpoint="metric_exporter_endpoint",
            system_metrics_config={"a": "b", "c": "d"}
        )

        mock_otlp_metrics_exporter.assert_called_with(
            **{
                "endpoint": "metric_exporter_endpoint",
                "credentials": credentials_mock,
                "metadata": (("lightstep-access-token", "a" * 104),),
            }
        )
