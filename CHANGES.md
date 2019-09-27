# Changelog

## Upcoming (0.6.0)

- A "Reload" button in the top right in dagit restarts the web-server process and updates
  the UI to reflect repo changes, including DAG structure, solid names, type names, etc.

## 0.5.9

- Fixes an issue using custom types for fan-in dependencies with intermediate storage.

## 0.5.8
- Fixes an issue running some Dagstermill notebooks on Windows.
- Fixes a transitive dependency issue with Airflow.
- Bugfixes, performance improvements, and better documentation.

## 0.5.7
- Fixed an issue with specifying composite output mappings (#1674)
- Added support for specifying
  [Dask worker resources](https://distributed.dask.org/en/latest/resources.html) (#1679)
- Fixed an issue with launching Dagit on Windows

## 0.5.6
- Execution details are now configurable. The new top-level `ExecutorDefinition` and `@executor`
  APIs are used to define in-process, multiprocess, and Dask executors, and may be used by users to
  define new executors. Like loggers and storage, executors may be added to a `ModeDefinition` and
  may be selected and configured through the `execution` field in the environment dict or YAML,
  including through Dagit. Executors may no longer be configured through the `RunConfig`.
- The API of dagster-dask has changed. Pipelines are now executed on Dask using the
  ordinary `execute_pipeline` API, and the Dask executor is configured through the environment.
  (See the dagster-dask README for details.)
- Added the `PresetDefinition.from_files` API for constructing a preset from a list of environment
  files (replacing the old usage of this class). `PresetDefinition` may now be directly
  instantiated with an environment dict.
- Added a prototype integration with [dbt](https://www.getdbt.com/).
- Added a prototype integration with [Great Expectations](https://greatexpectations.io/).
- Added a prototype integration with [Papertrail](https://papertrailapp.com/).
- Added the dagster-bash library.
- Added the dagster-ssh library.
- Added the dagster-sftp library.
- Loosened the PyYAML compatibility requirement.
- The dagster CLI no longer takes a `--raise-on-error` or `--no-raise-on-error` flag. Set this
  option in executor config.
- Added a `MarkdownMetadataEntryData` class, so events yielded from client code may now render
  markdown in their metadata.
- Bug fixes, documentation improvements, and improvements to error display.

## 0.5.5
- Dagit now accepts parameters via environment variables prefixed with `DAGIT_`, e.g. `DAGIT_PORT`.
- Fixes an issue with reexecuting Dagstermill notebooks from Dagit.
- Bug fixes and display improvments in Dagit.

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
