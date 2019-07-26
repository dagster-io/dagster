# Changelog

## 0.5.4
- Reworked the display of structured log information and system events in Dagit, including support
  for structured rendering of client-provided event metadata.
- Dagster now generates events when intermediates are written to filesystem and S3 storage, and
  these events are displayed in Dagit and exposed in the GraphQL API.
- Whitespace display styling in Dagit can now be toggled on and off.
- Bug fixes, display nits and improvements, and improvements to JS build process, including better
  display for some classes of errors in Dagit and improvements to the config editor in Dagit.

## 0.5.3
- Pinned RxPY to 1.6.1 to avoid breaking changes in 3.0.0 (py3-only).
- Most definition objects are now read-only, with getters corresponding to the previous properties.
- The `valueRepr` field has been removed from `ExecutionStepInputEvent` and `ExecutionStepOutputEvent`.
- Bug fixes and dagit UX improvements, including SQL highlighting and error handling.
  
## 0.5.2
- Added top-level `define_python_dagster_type` function.
- Renamed `metadata_fn` to `typecheck_metadata_fn` in all runtime type creation APIs.
- Renamed `result_value` and `result_values` to `output_value` and `output_values` on `SolidExecutionResult`
- Dagstermill: Reworked public API now contains only `define_dagstermill_solid`, `get_context`,
  `yield_event`, `yield_result`, `DagstermillExecutionContext`, `DagstermillError`, and
  `DagstermillExecutionError`. Please see the new
  [guide](https://dagster.readthedocs.io/en/0.5.2/sections/learn/guides/data_science/data_science.html)
  for details.
- Bug fixes, including failures for some dagster CLI invocations and incorrect handling of Airflow
  timestamps.
