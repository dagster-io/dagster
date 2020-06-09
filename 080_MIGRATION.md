# Migrating to 0.8.0 from 0.7.x

This document discusses the major public-facing API changes in dagster 0.8.0 as well as some of the
underlying rationale.

## Repository loading

Dagit and other tools no longer load a single repository containing user definitions such as
pipelines into the same process as the framework code. Instead, they load a "workspace" that can
contain multiple repositories sourced from a variety of different external locations (e.g., Python
modules and Python virtualenvs, with containers and source control repositories soon to come).

The repositories in a workspace are loaded into their own "user" processes distinct from the
"host" framework process. Dagit and other tools now communicate with user code over an IPC
mechanism.

As a consequence, the former `repository.yaml` and the associated `-y`/`--repository-yaml` CLI
arguments are deprecated in favor of a new `workspace.yaml` file format and associated
`-w`/`--workspace-yaml` arguments.

### Steps to migrate

You should replace your `repository.yaml` files with `workspace.yaml` files, which can define a
number of possible sources from which to load repositories.

```yaml
load_from:
  - python_module:
      module_name: dagster_examples
      attribute: define_internal_dagit_repository
  - python_module: dagster_examples.intro_tutorial.repos
  - python_file: repos.py
  - python_environment:
      executable_path: "/path/to/venvs/dagster-dev-3.7.6/bin/python"
      target:
        python_module:
          module_name: dagster_examples
          location_name: dagster_examples
          attribute: define_internal_dagit_repository
```

## Repository definition

The `@scheduler` and `@repository_partitions` decorators have been removed. In addition, users
should prefer the new `@repository` decorator to instantiating `RepositoryDefinition` directly.

One consequence of this change is that `PartitionSetDefinition` names, including those defined by
a `PartitionScheduleDefinition`, must now be unique within a single repository.

### Steps to migrate

Previously you might have defined your pipelines, schedules, partition sets, and repositories in a
python file such as the following:

```python
@pipeline
def test():
    ...

@daily_schedule(
    pipeline_name='test',
    start_date=datetime.datetime(2020, 1, 1),
)
def daily_test_schedule(_):
    return {}

test_partition_set = PartitionSetDefinition(
    name="test",
    pipeline_name="test",
    partition_fn=lambda: ["test"],
    environment_dict_fn_for_partition=lambda _: {},
)

@schedules
def define_schedules():
    return [daily_test_schedule]

@repository_partitions
def define_partitions():
    return [test_partition_set]

def define_repository():
    return RepositoryDefinition('test', pipeline_defs=[test])
```

With a `repository.yaml` such as:

```yaml
repository:
  file: repo.py
  fn: define_repository

scheduler:
  file: repo.py
  fn: define_schedules

partitions:
  file: repo.py
  fn: define_partitions
```

In 0.8.0, you'll write Python like:

```python
@pipeline
def test_pipeline():
    ...

@daily_schedule(
    pipeline_name='test',
    start_date=datetime.datetime(2020, 1, 1),
)
def daily_test_schedule(_):
    return {}

test_partition_set = PartitionSetDefinition(
    name="test",
    pipeline_name="test",
    partition_fn=lambda: ["test"],
    run_config_fn_for_partition=lambda _: {},
)

@repository
def test_repository():
    return [test_pipeline, daily_test_schedule, test_partition_set]
```

Your `workspace.yaml` will look like:

```yaml
load_from:
  - python_file: repo.py
```

If you have more than one repository defined in a single Python file, you'll want to instead load
the repository using `workspace.yaml` like:

```yaml
load_from:
  - python_file:
      relative_path: repo.py
      attribute: test_repository
  - python_file:
      relative_path: repo.py
      attribute: other_repository
```

Of course, the `workspace.yaml` also supports loading from a `python_module`, or with a specific
Python interpreter from a `python_environment`.

Note that the `@repository` decorator also supports more sophisticated, lazily-loaded repositories.
Consult the documentation for the decorator for more details.

## Reloadable repositories

In 0.7.x, dagster attempted to elide the difference between a pipeline that was defined in memory
and one that was loaded through machinery that used the `ExecutionTargetHandle` machinery. This
resulted in opaque and hard-to-predict errors and unpleasant workarounds, for instance:

- Pipeline execution in test using `execute_pipeline` would suddenly fail when a multiprocess
  executor was used.
- Tests of pipelines with dagstermill solids had to resort to workarounds such as

```python
    handle = handle_for_pipeline_cli_args(
        {'module_name': 'some_module.repository', 'fn_name': 'some_pipeline'}
    )
    pipeline = handle.build_pipeline_definition()
    result = execute_pipeline(pipeline, ...)
```

In 0.8.0, we've added the `reconstructable` helper to explicitly convert in-memory pipelines into
reconstructable pipelines that can be passed between processes.

```python
@pipeline(...)
def some_pipeline():
    ...

execute_pipeline(reconstructable(some_pipeline), {'execution': {'multiprocess': {}})
```

Pipelines must be defined in module scope in order for `reconstructable` to be used. Note that
pipelines defined _interactively_, e.g., in the Python REPL, cannot be passed between processes.

## Renaming environment_dict and removing RunConfig

In 0.8.0, we've renamed the common `environment_dict` parameter to many user-facing APIs to
`run_config`, and we've dropped the previous `run_config` parameter. This change affects the
`execute_pipeline_iterator` and `execute_pipeline` APIs, the `PresetDefinition` and
`ScheduleDefinition`, and the `execute_solid` test API. Similarly, the `environment_dict_fn`, `user_defined_environment_dict_fn_for_partition`, and `environment_dict_fn_for_partition` parameters
to `ScheduleDefinition`, `PartitionSetDefinition`, and `PartitionScheduleDefinition` have been
renamed to `run_config_fn`, `user_defined_run_config_fn_for_partition`, and
`run_config_fn_for_partition` respectively.

The previous `run_config` parameter has been removed, as has the backing `RunConfig` class. This
change affects the `execute_pipeline_iterator` and `execute_pipeline` APIs, and the
`execute_solids_within_pipeline` and `execute_solid_within_pipeline` test APIs. Instead, you should
set the `mode`, `preset`, `tags`, `solid_selection`, and, in test, `raise_on_error parameters
directly.

This change is intended to reduce ambiguity around the notion of a pipeline execution's
"environment", since the config value passed as `run_config` is scoped to a single execution.

## Renaming config

In 0.8.0, we've renamed the common `config` parameter to the user-facing definition APIs to
`config_schema`. This is intended to reduce ambiguity between config values (provided at
execution time) and their user-specified schemas (provided at definition time). This change affects
the `ConfigMapping`, `@composite_solid`, `@solid`, `SolidDefinition`, `@executor`,
`ExecutorDefinition`, `@logger`, `LoggerDefinition`, `@resource`, and `ResourceDefinition` APIs.
In the CLI, `dagster pipeline execute` and `dagster pipeline launch` now take `-c/--config` instead
of `-e/--env`.

## Renaming solid_subset and enabling support for solid selection DSL in Python API

In 0.8.0, we've renamed the `solid_subset`/`--solid-subset` argument to
`solid_selection`/`--solid-selection` throughout the Python API and CLI. This affects the
`dagster pipeline execute`, `dagster pipeline launch`, and `dagster pipeline backfill` CLI commands,
and the `@schedule`, `@monthly_schedule`, `@weekly_schedule`, `@daily_schedule`, `@hourly_schedule`,
`ScheduleDefinition`, `PresetDefinition`, `PartitionSetDefinition`, `PartitionScheduleDefinition`,
`execute_pipeline`, `execute_pipeline_iterator`, `DagsterInstance.create_run_for_pipeline`,
`DagsterInstance.create_run` APIs.

In addition to the names of individual solids, the new `solid_selection` argument supports selection
queries like `*solid_name++` (i.e., `solid_name`, all of its ancestors, its immediate descendants,
and their immediate descendants), previously supported only in Dagit views.

## Removal of deprectated properties, methods, and arguments

- The deprecated `runtime_type` property on `InputDefinition` and `OutputDefinition` has been
  removed. Use `dagster_type` instead.
- The deprecated `has_runtime_type`, `runtime_type_named`, and `all_runtime_types` methods on
  `PipelineDefinition` have been removed. Use `has_dagster_type`, `dagster_type_named`, and
  `all_dagster_types` instead.
- The deprecated `all_runtime_types` method on `SolidDefinition` and `CompositeSolidDefinition`
  has been removed. Use `all_dagster_types` instead.
- The deprecated `metadata` argument to `SolidDefinition` and `@solid` has been removed. Use
  `tags` instead.
- The use of `is_optional` throughout the codebase was deprecated in 0.7.x and has been removed. Use
  `is_required` instead.

## Removal of Path config type

The built-in config type `Path` has been removed. Use `String`.

## dagster-bash

This package has been renamed to dagster-shell. The`bash_command_solid` and `bash_script_solid`
solid factory functions have been renamed to `create_shell_command_solid` and
`create_shell_script_solid`.

## Dask config

The config schema for the `dagster_dask.dask_executor` has changed. The previous config should
now be nested under the key `local`.

## Spark solids

`dagster_spark.SparkSolidDefinition` has been removed - use `create_spark_solid` instead.
