## Unreleased

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
