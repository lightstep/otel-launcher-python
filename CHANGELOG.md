## Unreleased

## 1.14.0

- Updated opentelemetry-instrumentation to 0.38b0

## 1.13.0

- Updated setuptools to 65.5.1

## 1.12.0

- Add support for OTEL_METRIC_EXPORT_INTERVAL
- Updated dependencies to 1.16.0 & 0.37b0

## 1.11.0

- Add support for LS_METRICS_ENABLED
- Add support for OTLP_EXPORTER_METRICS_ENDPOINT
- Add support for OTLP_EXPORTER_METRICS_TEMPORALITY_PREFERENCE

## 1.10.0

- Updated dependencies to 1.14.0 & 0.35b0

## 1.9.0

- Remove support for Python 3.6
- Updated dependencies to 1.13.0 & 0.34b0

## 1.8.0

- Updated dependencies to 1.11.1 & 0.30b1

## 1.7.2

- Add support for OTEL_SERVICE_NAME

## 1.7.1

- Updated dependencies to 1.7.1

## 1.3.0

- Updated dependencies to 1.3.0

## 1.2.0

- Updated dependencies to 1.2.0
- Load propagators from entry points

## 1.1.0

- Updated dependencies to 1.1.0
- Updated import paths
- Added protocol to default endpoints
- Updated documentation

## 1.0.0

- Updated dependencies to 1.0.0

## 1.0.0rc1

- Removing metrics configuration since this feature is not part of trace GA
- Removing support for 3.5

## 0.17b0

- Updating dependencies to 0.17b0
- Added `opentelemetry-propagator-b3` dependency
- Client example updated to reflect that `RequestsInstrumentor`
  needs to be instrumented after `configure_opentelemetry`, otherwise
  the `MeterProvider` will already have been set.

## 0.15b0

- Add configuration for Metrics Exporter

## 0.14b0

- Add support for `host.name` in Resource attributes
- Add support for baggage propagation (#51)
- Updating dependencies to 0.14b0 (#51)
- Add support for tracecontext propagation (#52)

## 0.13b0

- Add error message when `configure_opentelemetry` fails
  from auto-instrumentation

## 0.12b0

- Support not configuring a token

## 0.11b0

- Initial version
