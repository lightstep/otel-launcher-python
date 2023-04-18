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
from sys import version_info
from unittest.mock import patch, ANY
from time import sleep
from logging import DEBUG, WARNING, ERROR
from importlib import reload
from os import environ

from opentelemetry.sdk.metrics import (
    Counter,
    Histogram,
    ObservableCounter,
    ObservableGauge,
    ObservableUpDownCounter,
    UpDownCounter,
)
from opentelemetry.sdk.metrics.export import (
    AggregationTemporality
)
from opentelemetry.launcher.configuration import (
    configure_opentelemetry,
    _logger,
    InvalidConfigurationError,
    _ATTRIBUTE_HOST_NAME,
)
from opentelemetry.launcher.version import __version__ as launcher_version
from opentelemetry.sdk.version import __version__
from opentelemetry import baggage, trace
from opentelemetry.propagate import get_global_textmap
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Once
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.propagators.ot_trace import OTTracePropagator
from opentelemetry.attributes import BoundedAttributes


class TestConfiguration(TestCase):

    def setUp(self):
        trace._TRACER_PROVIDER_SET_ONCE = Once()
        trace._TRACER_PROVIDER = None

    @patch("opentelemetry.launcher.configuration.LightstepOTLPMetricExporter")
    def test_metrics_enabled(self, mock_metrics_exporter):

        configure_opentelemetry(
            service_name="service_name",
            metrics_enabled=True,
            access_token="a" * 104
        )

        mock_metrics_exporter.assert_called_with(
            endpoint="https://ingest.lightstep.com:443",
            credentials=ANY,
            headers=(("lightstep-access-token", "a" * 104),),
            preferred_temporality={
                Counter: AggregationTemporality.DELTA,
                UpDownCounter: AggregationTemporality.CUMULATIVE,
                Histogram: AggregationTemporality.DELTA,
                ObservableCounter: AggregationTemporality.CUMULATIVE,
                ObservableUpDownCounter: AggregationTemporality.CUMULATIVE,
                ObservableGauge: AggregationTemporality.CUMULATIVE,
            }
        )

    @patch("opentelemetry.launcher.configuration.CompositePropagator")
    def test_propagator_entry_point(self, mock_compositepropagator):
        configure_opentelemetry(
            service_name="service-123",
            span_exporter_endpoint="localhost:1234",
        )

        if version_info.major < 8:
            call_arg = mock_compositepropagator.call_args[0][0][0]

        else:
            call_arg = mock_compositepropagator.call_args.args[0][0]

        self.assertIsInstance(call_arg, B3MultiFormat)

        trace._TRACER_PROVIDER_SET_ONCE = Once()
        trace._TRACER_PROVIDER = None

        configure_opentelemetry(
            service_name="service-123",
            span_exporter_endpoint="localhost:1234",
            propagators="ottrace"
        )

        if version_info.major < 8:
            call_arg = mock_compositepropagator.call_args[0][0][0]

        else:
            call_arg = mock_compositepropagator.call_args.args[0][0]

        self.assertIsInstance(call_arg, OTTracePropagator)

    def test_no_service_name(self):
        with self.assertRaises(InvalidConfigurationError):
            with self.assertLogs(logger=_logger, level="ERROR") as log:
                # service_name is set here as None in order to override any
                # possible LS_SERVICE_NAME environment variable that may be
                # set
                configure_opentelemetry(service_name=None)
                self.assertIn("service name missing", log.output[0])

    def test_no_token(self):
        with self.assertRaises(InvalidConfigurationError):
            with self.assertLogs(logger=_logger, level="ERROR") as log:
                # access_token is set here as None in order to override any
                # possible LS_ACCES_TOKEN environment variable that may be set
                configure_opentelemetry(
                    service_name="service-123", access_token=None
                )
                self.assertIn("token missing", log.output[0])

        with self.assertRaises(InvalidConfigurationError):
            with self.assertLogs(logger=_logger, level="ERROR") as log:
                # access_token is set here as None in order to override any
                # possible LS_ACCES_TOKEN environment variable that may be set
                configure_opentelemetry(
                    service_name="service-123",
                    access_token=None,
                    metrics_enabled=True
                )
                self.assertIn("token missing", log.output[0])

    def test_no_token_other_endpoint(self):
        # no exception is thrown
        configure_opentelemetry(
            service_name="service-123",
            span_exporter_endpoint="localhost:1234",
        )

    class MockBatchSpanProcessor(BatchSpanProcessor):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, schedule_delay_millis=1, **kwargs)

    @patch(
        "opentelemetry.launcher.configuration.BatchSpanProcessor",
        new=MockBatchSpanProcessor,
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

        # The worker thread in MockBatchSpanProcessor is configured to
        # wait 10ms before exporting. Sleeping here to give enough time to the
        # export method mock to be called.
        sleep(0.01)

        mock_otlp_span_exporter.assert_called()

    @patch("opentelemetry.launcher.configuration.LightstepOTLPSpanExporter")
    def test_headers(self, mock_otlp_span_exporter):

        configure_opentelemetry(
            service_name="service_123", access_token="a" * 104
        )

        mock_otlp_span_exporter.assert_called_with(
            endpoint="https://ingest.lightstep.com:443",
            credentials=ANY,
            headers=(("lightstep-access-token", "a" * 104),),
        )

    def test_log_level_good_debug(self):

        with self.assertLogs(logger=_logger, level=DEBUG):
            configure_opentelemetry(
                service_name="service_123",
                access_token="a" * 104,
                log_level="DEBUg",
            )

    def test_log_level_good_warning(self):

        with self.assertLogs(logger=_logger, level=WARNING):
            configure_opentelemetry(
                service_name="service_123",
                access_token="a" * 104,
                log_level="WARNINg",
            )

    def test_log_level_bad_warning(self):

        with self.assertRaises(InvalidConfigurationError):
            with self.assertLogs(logger=_logger, level=ERROR):
                configure_opentelemetry(
                    service_name="service_123",
                    access_token="a" * 104,
                    log_level="WaRNiNGx",
                )

    @patch("opentelemetry.launcher.configuration.gethostname")
    @patch("opentelemetry.launcher.configuration.Resource")
    def test_resource_attributes(self, mock_resource, mock_gethostname):
        mock_gethostname.return_value = "the_hostname"

        from opentelemetry import trace
        reload(trace)

        configure_opentelemetry(
            service_name="service_name",
            service_version="service_version",
            access_token="a" * 104,
        )

        mock_resource.assert_called_with(
            BoundedAttributes(
                attributes={
                    "telemetry.sdk.language": "python",
                    "telemetry.sdk.version": __version__,
                    "telemetry.sdk.name": "opentelemetry",
                    "service.name": "service_name",
                    "service.version": "service_version",
                    _ATTRIBUTE_HOST_NAME: "the_hostname",
                    "telemetry.distro.name": "lightstep",
                    "telemetry.distro.version": launcher_version,
                }
            )
        )

    @patch("opentelemetry.launcher.configuration.gethostname")
    @patch("opentelemetry.launcher.configuration.Resource")
    def test_service_version(self, mock_resource, mock_gethostname):
        mock_gethostname.return_value = "the_hostname"

        from opentelemetry import trace
        reload(trace)

        configure_opentelemetry(
            service_name="service_name",
            access_token="a" * 104,
        )

        mock_resource.assert_called_with(
            BoundedAttributes(
                attributes={
                    "telemetry.sdk.language": "python",
                    "telemetry.sdk.version": __version__,
                    "telemetry.sdk.name": "opentelemetry",
                    "service.name": "service_name",
                    _ATTRIBUTE_HOST_NAME: "the_hostname",
                    "telemetry.distro.name": "lightstep",
                    "telemetry.distro.version": launcher_version,
                }
            )
        )

    def test_propagation(self):
        configure_opentelemetry(
            service_name="service_name",
            service_version="service_version",
            access_token="a" * 104,
        )

        with trace.get_tracer(__name__).start_as_current_span("test") as span:
            ctx = baggage.set_baggage("abc", "def")
            prop = get_global_textmap()
            carrier = {}

            prop.inject(carrier, context=ctx)
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
            prop.inject(carrier, context=ctx)
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
            prop.inject(carrier, context=ctx)
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
            propagators="b3multi,baggage,tracecontext",
        )

        with trace.get_tracer(__name__).start_as_current_span("test") as span:
            ctx = baggage.set_baggage("abc", "def")
            prop = get_global_textmap()
            carrier = {}
            prop.inject(carrier, context=ctx)
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
    def test_hostname_no_resource_attributes(
        self, mock_resource, mock_gethostname
    ):

        from opentelemetry import trace
        reload(trace)

        mock_gethostname.return_value = "the_hostname"

        configure_opentelemetry(
            service_name="service_name",
            access_token="a" * 104,
        )

        mock_resource.assert_called_with(
            BoundedAttributes(
                attributes={
                    "telemetry.sdk.language": "python",
                    "telemetry.sdk.version": __version__,
                    "service.name": "service_name",
                    _ATTRIBUTE_HOST_NAME: "the_hostname",
                    "telemetry.sdk.name": "opentelemetry",
                    "telemetry.distro.name": "lightstep",
                    "telemetry.distro.version": launcher_version,
                }
            )
        )

    @patch("opentelemetry.launcher.configuration.gethostname")
    @patch("opentelemetry.launcher.configuration.Resource")
    def test_hostname_with_resource_attributes(
        self, mock_resource, mock_gethostname
    ):
        from opentelemetry import trace
        reload(trace)

        configure_opentelemetry(
            service_name="service_name",
            access_token="a" * 104,
            resource_attributes="{}=other_hostname".format(
                _ATTRIBUTE_HOST_NAME
            ),
        )

        mock_resource.assert_called_with(
            BoundedAttributes(
                attributes={
                    "telemetry.sdk.language": "python",
                    "telemetry.sdk.version": __version__,
                    "service.name": "service_name",
                    _ATTRIBUTE_HOST_NAME: "other_hostname",
                    "telemetry.sdk.name": "opentelemetry",
                    "telemetry.distro.name": "lightstep",
                    "telemetry.distro.version": launcher_version,
                }
            )
        )

    def test_backup_for_traces_endpoint(self):
        # This is needed because this function calls reload. Not saving the
        # value for these variables here can cause subsequent tests to fail.
        original_configure_opentelemetry = configure_opentelemetry
        original__logger = _logger
        original_invalid_configuration_error = InvalidConfigurationError
        original_attribute_host_name = _ATTRIBUTE_HOST_NAME

        from opentelemetry.launcher import configuration

        try:
            reload(configuration)

            self.assertEqual(
                configuration._OTEL_EXPORTER_OTLP_TRACES_ENDPOINT,
                "https://ingest.lightstep.com:443",
            )

            with patch.dict(
                environ,
                {"OTEL_EXPORTER_OTLP_TRACES_ENDPOINT": "traces_endpoint"}
            ):

                reload(configuration)

                self.assertEqual(
                    configuration._OTEL_EXPORTER_OTLP_TRACES_ENDPOINT,
                    "traces_endpoint",
                )

            with patch.dict(
                environ,
                {
                    "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT": "traces_endpoint",
                    "OTEL_EXPORTER_OTLP_SPAN_ENDPOINT": "span_endpoint",
                }
            ):

                reload(configuration)

                self.assertEqual(
                    configuration._OTEL_EXPORTER_OTLP_TRACES_ENDPOINT,
                    "traces_endpoint",
                )

            with patch.dict(
                environ,
                {
                    "OTEL_EXPORTER_OTLP_SPAN_ENDPOINT": "span_endpoint",
                }
            ):

                reload(configuration)

                self.assertEqual(
                    configuration._OTEL_EXPORTER_OTLP_TRACES_ENDPOINT,
                    "span_endpoint",
                )

        finally:
            # This is needed because this function calls reload(configuration).
            # When that happens, the symbols from configuration no longer match
            # the ones previously imported in:
            # from opentelemetry.launcher.configuration import (
            #     configure_opentelemetry,
            #     _logger,
            #     InvalidConfigurationError,
            #     _ATTRIBUTE_HOST_NAME,
            # )
            # This means that when an InvalidConfigurationError is raised from
            # code in the configuration module when running a subsequent test
            # the InvalidConfigurationError that is raised is not the same
            # InvalidConfigurationError that was imported previously in this
            # module. That causes assertRaises to get a different exception and
            # fails, because it expected InvalidConfigurationError (imported
            # from this module) but received InvalidConfigurationError (new
            # class from the reloaded configuration module).

            configuration.configure_opentelemetry = (
                original_configure_opentelemetry
            )
            configuration._logger = (
                original__logger
            )
            configuration.InvalidConfigurationError = (
                original_invalid_configuration_error
            )
            configuration._ATTRIBUTE_HOST_NAME = (
                original_attribute_host_name
            )

    # FIXME use autospec when the implementation the OTel SDK does not call
    # private attributes of PeriodicExportingMetricReader.
    @patch(
        "opentelemetry.launcher.configuration.PeriodicExportingMetricReader",
    )
    def test_metric_export_interval(self, mock_periodic_exporter_metric_reader):

        configure_opentelemetry(
            service_name="service_name",
            service_version="service_version",
            access_token="a" * 104,
            propagators="b3multi,baggage,tracecontext",
            metrics_enabled=True,
            metrics_exporter_interval=0,
        )

        mock_periodic_exporter_metric_reader.assert_called_with(ANY, export_timeout_millis=0)
