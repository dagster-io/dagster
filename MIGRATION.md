# Version migration

When new releases include breaking changes or deprecations, this document describes how to migrate.

## Migrating to 1.5.0

### Breaking changes

- The UI dialog for launching a backfill no longer includes a toggle to determine whether the backfill is launched as a single run or multiple runs. This toggle was misleading, because it implied that all backfills could be launched as single-run backfills, when it actually required special handling in the implementations of the assets targeted by the backfill to achieve this behavior.  Instead, whether to execute a backfill as a single run is now determined by a setting on the asset definition. To enable single-run backfills, set `backfill_policy=BackfillPolicy.single_run()` on the asset definitions. Refer to the [docs on single-run backfills](https://docs.dagster.io/concepts/partitions-schedules-sensors/backfills#single-run-backfills) for more information.

- `AssetExecutionContext` is now a subclass of `OpExecutionContext`, not a type alias. The code
```python
def my_helper_function(context: AssetExecutionContext):
    ...

@op
def my_op(context: OpExecutionContext):
    my_helper_function(context)
```
will cause type checking errors. To migrate, update type hints to respect the new subclassing.

- `AssetExecutionContext` cannot be used as the type annotation for `@op`s. To migrate, update the type hint in `@op` to `OpExecutionContext`. `@op`s that are used in `@graph_assets` may still use the `AssetExecutionContext` type hint.
```python
# old
@op
def my_op(context: AssetExecutionContext):
    ...

# correct
@op
def my_op(context: OpExecutionContext):
    ...
```

- `AssetCheckResult(success=True)` is renamed to `AssetCheckResult(passed=True)`

- Asset checks defined with Dagster version 1.4 will no longer work with Dagster Cloud, or with Dagster UI 1.5. Upgrade your `dagster` library to continue using checks.

## Migrating to 1.4.0

### Deprecations

- The `dagit` python package and all references to it are now deprecated. We will continue to publish `dagit` and support APIs that used the term “dagit” until v2.0, but you should transition to newer `dagster-webserver` package. This is a drop-in replacement for `dagit`. Like `dagit`, it exposes an executable of the same name as the package itself, i.e. `dagster-webserver`.
- Any Dockerfiles or other Python environment specifications used for running the webserver now use `dagster-webserver` instead, e.g.:

```dockerfile
# no (deprecated)
RUN pip install dagster dagit ...
...
ENTRYPOINT ["dagit", "-h", "0.0.0.0", "-p", "3000"]

# yes
RUN pip install dagster dagster-webserver
...
ENTRYPOINT ["dagster-webserver", "-h", "0.0.0.0", "-p", "3000"]
```

- [Helm Chart] Three fields that were using the term “dagit” have been deprecated and replaced with “dagsterWebserver” instead:

```yaml
# no (deprecated)
dagit:
  ...
  # ...
ingress:
  dagit: ...
  readOnlyDagit: ...

# yes
dagsterWebserver:
  ...
  # ...
ingress:
  dagsterWebserver: ...
  readOnlyDagsterWebserver: ...
```

- We’ve deprecated the `non_argument_deps` parameter of `@asset` and `@multi_asset` in favor of a new `deps` parameter. To update your code to use `deps`, simply rename any instances of `non_argument_deps` to `deps` and change the type from a set to list. Additionally, you may also want to begin passing the python symbols for assets, rather than their `AssetKey`s to improve in-editor experience with type-aheads and linting.

```python
@asset
def my_asset():
   ...

@asset(
   non_argument_deps={"my_asset"}
)
def a_downstream_asset():
   ...

# becomes

@asset
def my_asset():
   ...

@asset(
   deps=["my_asset"]
)
def a_downstream_asset():
   ...

# or

@asset
def my_asset():
   ...

@asset(
   deps=[my_asset]
)
def a_downstream_asset():
   ...
```

- [Dagster Cloud ECS Agent] We've introduced performance improvements that rely on the [AWS Resource Groups Tagging API](https://docs.aws.amazon.com/resourcegroupstagging/latest/APIReference/overview.html). To enable, grant your agent's IAM policy permission to `tag:DescribeResources`. Without this policy, the ECS Agent will log a deprecation warning and fall back to its old behavior (listing all ECS services in the cluster and then listing each service's tags).
- [dagster-dbt] `DbtCliClientResource`, `dbt_cli_resource` and `DbtCliOutput` are now being deprecated in favor of `DbtCliResource`. `dagster-dbt` Asset APIs like `load_assets_from_dbt_manifest` and `load_assets_from_dbt_project` will continue to work if given either a `DbtCliClientResource` or `DbtCliResource`.

```python
# old
@op
def my_dbt_op(dbt_resource: DbtCliClientResource):
    dbt: DbtCliClient = dbt.get_client()

    dbt.cli("run")

    dbt.cli("run", full_refresh=True)

    dbt.cli("test")
    manifest_json = dbt.get_manifest_json()

# new
with Path("my/dbt/manifest").open() as handle:
    manifest = json.loads(dbt_manifest.read())

@op
def my_dbt_op(dbt: DbtCliResource):
   dbt.cli(["run"], manifest=manifest).stream()

   dbt.cli(["run", "--full-refresh"], manifest=manifest).stream()

   dbt_test_invocation = dbt.cli(["test"], manifest_manifest).stream()
   manifest_json = dbt_test_invocation.get_artifact("manifest.json")

# old
dbt_assets = load_assets_from_dbt_project(project_dir="my/dbt/project")

defs = Definitions(
    assets=dbt_assets,
    resources={
        "dbt": DbtCliClientResource(project_dir="my/dbt/project")
    },
)

# new
dbt_assets = load_assets_from_dbt_project(project_dir="my/dbt/project")

defs = Definitions(
    assets=dbt_assets,
    resources={
        "dbt": DbtCliResource(project_dir="my/dbt/project")
    }
)

```

- The following arguments on `load_assets_from_dbt_project` and `load_assets_from_dbt_manifest` are now deprecated in favor of other options. Arguments will continue to work when passed into these functions, but a deprecation warning will be emitted.

| Deprecated Arguments                      | Recommendation                                                                                                                                                   |
| ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `key_prefix`                              | Instead, provide a custom `DagsterDbtTranslator` that overrides `get_asset_key`                                                                                  |
| `source_key_prefix`                       | Instead, provide a custom `DagsterDbtTranslator` that overrides `get_asset_key`                                                                                  |
| `op_name`                                 | Use the `@dbt_assets` decorator if you need to customize your op name.                                                                                           |
| `manifest_json`                           | Use the `manifest` parameter instead.                                                                                                                            |
| `display_raw_sql`                         | Instead, provide a custom `DagsterDbtTranslator` that overrides `get_description`.                                                                               |
| `selected_unique_ids`                     | Use the `select` parameter instead.                                                                                                                              |
| `dbt_resource_key`                        | Use the `@dbt_assets` decorator if you need to customize your resource key.                                                                                      |
| `use_build_command`                       | Use the `@dbt_assets` decorator if you need to customize the underlying dbt commands.                                                                            |
| `partitions_def`                          | Use the `@dbt_assets` decorator to define partitioned dbt assets.                                                                                                |
| `partition_key_to_vars_fn`                | Use the `@dbt_assets` decorator to define partitioned dbt assets.                                                                                                |
| `runtime_metadata_fn`                     | Use the `@dbt_assets` decorator if you need to customize runtime metadata.                                                                                       |
| `node_info_to_asset_key_fn`               | Instead, provide a custom `DagsterDbtTranslator` that overrides `get_asset_key`.                                                                                 |
| `node_info_to_group_fn`                   | Instead, configure dagster groups on a dbt resource's meta field, assign dbt groups, or provide a custom `DagsterDbtTranslator` that overrides `get_group_name`. |
| `node_info_to_auto_materialize_policy_fn` | Instead, configure Dagster auto-materialize policies on a dbt resource's meta field.                                                                             |
| `node_info_to_freshness_policy_fn`        | Instead, configure Dagster freshness policies on a dbt resource's meta field.                                                                                    |
| `node_info_to_definition_metadata_fn`     | Instead, provide a custom `DagsterDbtTranslator` that overrides `get_metadata`.                                                                                  |

### Breaking changes

- From this release forward Dagster will no longer be tested against Python 3.7. Python 3.7 reached end of life on June 27th 2023 meaning it will no longer receive any security fixes. Previously releases will continue to work on 3.7. Details about moving to 3.8 or beyond can be found at https://docs.python.org/3/whatsnew/3.8.html#porting-to-python-3-8 .
- `build_asset_reconciliation_sensor` (Experimental) has been removed. It was deprecated in 1.3 in favor of `AutoMaterializePolicy`. Docs are [here](https://docs.dagster.io/concepts/assets/asset-auto-execution).
- The `dagster-dbt` integration with `dbt-rpc` has been removed, as [the dbt plugin is being deprecated](https://github.com/dbt-labs/dbt-rpc).
- Previously, `DbtCliResource` was a class alias for `DbtCliClientResource`. Now, `DbtCliResource` is a new resource with a different API. Furthermore, it requires at least `dbt-core>=1.4` to run.
- [Helm Chart] If upgrading an existing installation to 1.4 and the `dagit.nameOverride` value is set, you will need to either change the value or delete the existing deployment to allow helm to update values that can not be patched for the rename from dagit to dagster-webserver.
- [dagster-dbt] `load_assets_from_dbt_project` and `load_assets_from_dbt_manifest` now default to `use_build=True`. To switch back to the previous behavior, use `use_build=False`.

```python
from dagster_dbt import group_from_dbt_resource_props_fallback_to_directory

load_assets_from_dbt_project(
    ...,
    use_build=False,
)
```

- [dagster-dbt] The default assignment of groups to dbt models loaded from `load_assets_from_dbt_project` and `load_assets_from_dbt_manifest` has changed. Rather than assigning a group name using the model’s subdirectory, a group name will be assigned using the dbt model’s [dbt group](https://docs.getdbt.com/docs/build/groups). To switch back to the previous behavior, use the following utility function, `group_from_dbt_resource_props_fallback_to_directory`:

```python
from dagster_dbt import group_from_dbt_resource_props_fallback_to_directory

load_assets_from_dbt_project(
    ...,
    node_info_to_group_fn=group_from_dbt_resource_props_fallback_to_directory,
)
```

- [dagster-dbt] The argument `node_info_to_definition_metadata_fn` for `load_assets_from_dbt_project` and `load_assets_from_dbt_manifest` now overrides metadata instead of adding to it. To switch back to the previous behavior, use the following utility function:

```python
from dagster_dbt import default_metadata_from_dbt_resource_props

def my_metadata_from_dbt_resource_props(dbt_resource_props):
    my_metadata = {...}
    return {**default_metadata_from_dbt_resource_props(dbt_resource_props), **my_metadata}

load_assets_from_dbt_manifest(
    ...,
    node_info_to_definition_metadata_fn=my_metadata_from_dbt_resource_props
)
```

- [dagster-dbt] The arguments for `load_assets_from_dbt_project` and `load_assets_from_dbt_manifest` now must be specified using keyword arguments.
- [dagster-dbt] When using the new `DbtCliResource` with `load_assets_from_dbt_project` and `load_assets_from_dbt_manifest`, stdout logs from the dbt process will now appear in the compute logs instead of the event logs. To view these compute logs, you should ensure that your Dagster instance has [compute log storage configured](https://docs.dagster.io/deployment/dagster-instance#compute-log-storage).

## Migrating to 1.3.0

### Deprecations

- **[deprecation, 1.4.0]** `build_asset_reconciliation_sensor`, which was experimental, is now deprecated, in favor of setting `AutoMaterializePolicy` on assets. Refer to the docs on `AutoMaterializePolicy` for how this works: [https://docs.dagster.io/concepts/assets/asset-auto-execution](https://docs.dagster.io/concepts/assets/asset-auto-execution).
- **[deprecation, 2.0.0]** Previously, the recommended pattern for creating a run request for a given partition of a job within a sensor was `yield job_def.run_request_for_partition(partition_key="...")`. This has been deprecated, in favor of `yield RunRequest(partition_key="...")`.

### Breaking Changes

- By default, resources defined on `Definitions` are now automatically bound to jobs. This will only result in a change in behavior if you a) have a job with no "io_manager" defined in its `resource_defs` and b) have supplied an `IOManager` with key "io_manager" to the `resource_defs` argument of your `Definitions`. Prior to 1.3.0, this would result in the job using the default filesystem-based `IOManager` for the key "io_manager". In 1.3.0, this will result in the "io_manager" supplied to your `Definitions` being used instead. The `BindResourcesToJobs` wrapper, introduced in 1.2 to simulate this behavior, no longer has any effect.
- **[experimental]** The `minutes_late` and `previous_minutes_late` properties on the experimental `FreshnesPolicySensorContext` have been renamed to `minutes_overdue` and `previous_minutes_overdue`, respectively.
- **[previously deprecated, 0.15.0]** The `metadata_entries` arguments to user-constructed events (`AssetObservation`,  `AssetMaterialization`,  `ExpectationResult`,  `TypeCheck`,  `Failure`,  `Output`,  `DynamicOutput`), as well as the `DagsterType` object have been removed. Instead, a dictionary of metadata should be passed into the `metadata` argument.
- **[dagster-celery-k8s]** The default kubernetes namespace for run pods when using the Dagster Helm chart with the `CeleryK8sRunLauncher` is now the same namespace as the Helm chart, instead of the `default` namespace. To restore the previous behavior, you can set the `celeryK8sRunLauncher.jobNamespace` field to the string `default`.
- **[dagster-snowflake-pandas]** Prior to `dagster-snowflake` version `0.19.0` the Snowflake I/O manager converted all timestamp data to strings before loading the data in Snowflake, and did the opposite conversion when fetching a DataFrame from Snowflake. The I/O manager now ensures timestamp data has a timezone attached and stores the data as TIMESTAMP_NTZ(9) type. If you used the Snowflake I/O manager prior to version `0.19.0` you can set the `store_timestamps_as_strings=True` configuration value for the Snowflake I/O manager to continue storing time data as strings while you do table migrations.

To migrate a table created prior to `0.19.0` to one with a TIMESTAMP_NTZ(9) type, you can run the follow SQL queries in Snowflake. In the example, our table is located at `database.schema.table` and the column we want to migrate is called `time`:

```sql

// Add a column of type TIMESTAMP_NTZ(9)
ALTER TABLE database.schema.table
ADD COLUMN time_copy TIMESTAMP_NTZ(9)

// copy the data from time and convert to timestamp data
UPDATE database.schema.table
SET time_copy = to_timestamp_ntz(time)

// drop the time column
ALTER TABLE database.schema.table
DROP COLUMN time

// rename the time_copy column to time
ALTER TABLER database.schema.table
RENAME COLUMN time_copy TO time

```

## Migrating to 1.2.0

### Database migration

1.2.0 adds a set of optional database schema migrations, which can be run via `dagster instance migrate`:

- Improves Dagit performance by adding a database index which should speed up job run views.
- Enables dynamic partitions definitions by creating a database table to store partition keys. This feature is experimental and may require future migrations.
- Adds a primary key `id` column to the `kvs`, `daemon_heartbeats` and `instance_info` tables, enforcing that all tables have a primary key.

### Breaking changes

#### Core changes

- The minimum `grpcio` version supported by Dagster has been increased to 1.44.0 so that Dagster can support both `protobuf` 3 and `protobuf` 4. Similarly, the minimum `protobuf` version supported by Dagster has been increased to 3.20.0. We are working closely with the gRPC team on resolving the upstream issues keeping the upper-bound `grpcio` pin in place in Dagster, and hope to be able to remove it very soon.
- Prior to 0.9.19, asset keys were serialized in a legacy format. This release removes support for querying asset events serialized with this legacy format. Contact #dagster-support for tooling to migrate legacy events to the supported version. Users who began using assets after 0.9.19 will not be affected by this change.

#### Changes to experimental APIs

- [experimental] `LogicalVersion` has been renamed to `DataVersion` and `LogicalVersionProvenance` has been renamed to `DataProvenance`.
- [experimental] Methods on the experimental `DynamicPartitionsDefinition` to add, remove, and check for existence of partitions have been removed. Refer to documentation for updated API methods.

#### Removal of deprecated APIs

- [previously deprecated, 0.15.0] Static constructors on `MetadataEntry` have been removed.
- [previously deprecated, 1.0.0] `DagsterTypeMaterializer`, `DagsterTypeMaterializerContext`, and `@dagster_type_materializer` have been removed.
- [previously deprecated, 1.0.0] `PartitionScheduleDefinition` has been removed.
- [previously deprecated, 1.0.0] `RunRecord.pipeline_run` has been removed (use `RunRecord.dagster_run`).
- [previously deprecated, 1.0.0] `DependencyDefinition.solid` has been removed (use `DependencyDefinition.node`).
- [previously deprecated, 1.0.0] The `pipeline_run` argument to `build_resources` has been removed (use `dagster_run`)

#### Extension Libraries

- [dagster-snowflake] The `execute_query`and `execute_queries` methods of the `SnowflakeResource` now have consistent behavior based on the values of the `fetch_results` and `use_pandas_result` parameters. If `fetch_results` is True, the standard Snowflake result will be returned. If `fetch_results` and `use_pandas_result` are True, a pandas DataFrame will be returned. If `fetch_results` is False and `use_pandas_result` is True, an error will be raised. If both are False, no result will be returned.
- [dagster-snowflake] The `execute_queries` command now returns a list of DataFrames when `use_pandas_result` is True, rather than appending the results of each query to a single DataFrame.
- [dagster-shell] The default behavior of the `execute` and `execute_shell_command` functions is now to include any environment variables in the calling op. To restore the previous behavior, you can pass in `env={}` to these functions.
- [dagster-k8s] Several Dagster features that were previously disabled by default in the Dagster Helm chart are now enabled by default. These features are:

  - The [run queue](https://docs.dagster.io/deployment/run-coordinator#limiting-run-concurrency) (by default, without a limit). Runs will now always be launched from the Daemon.
  - Run queue parallelism - by default, up to 4 runs can now be pulled off of the queue at a time (as long as the global run limit or tag-based concurrency limits are not exceeded).
  - [Run retries](https://docs.dagster.io/deployment/run-retries#run-retries) - runs will now retry if they have the `dagster/max_retries` tag set. You can configure a global number of retries in the Helm chart by setting `run_retries.max_retries` to a value greater than the default of 0.
  - Schedule and sensor parallelism - by default, the daemon will now run up to 4 sensors and up to 4 schedules in parallel.
  - [Run monitoring](https://docs.dagster.io/deployment/run-monitoring) - Dagster will detect hanging runs and move them into a FAILURE state for you (or start a retry for you if the run is configured to allow retries). By default, runs that have been in STARTING for more than 5 minutes will be assumed to be hanging and will be terminated.

  Each of these features can be disabled in the Helm chart to restore the previous behavior.

- [dagster-k8s] The experimental `[k8s_job_op](https://docs.dagster.io/_apidocs/libraries/dagster-k8s#dagster_k8s.k8s_job_op)` op and `[execute_k8s_job](https://docs.dagster.io/_apidocs/libraries/dagster-k8s#dagster_k8s.execute_k8s_job)` functions no longer automatically include configuration from a `dagster-k8s/config` tag on the Dagster job in the launched Kubernetes job. To include raw Kubernetes configuration in a `k8s_job_op`, you can set the `container_config`, `pod_template_spec_metadata`, `pod_spec_config`, or `job_metadata` config fields on the `k8s_job_op` (or arguments to the `execute_k8s_job` function).
- [dagster-databricks] The integration has now been refactored to support the official Databricks API.
  - `create_databricks_job_op` is now deprecated. To submit one-off runs of Databricks tasks, you must now use the `create_databricks_submit_run_op`.
  - The Databricks token that is passed to the `databricks_client` resource must now begin with `https://`.

## Migrating to 1.1.1

### Database migration

Two optional database schema migrations, which can be run via `dagster instance migrate`:

- Improves Dagit performance by adding database indexes which should speed up the run view as well as a range of asset-based queries.
- Enables multi-dimensional asset partitions and asset versioning.

### Breaking changes and deprecations

- `define_dagstermill_solid`, a legacy API, has been removed from `dagstermill`. Use `define_dagstermill_op` or `define_dagstermill_asset` instead to create an `op` or `asset` from a Jupyter notebook, respectively.
- The internal `ComputeLogManager` API is marked as deprecated in favor of an updated interface: `CapturedLogManager`. It will be removed in `1.2.0`. This should only affect dagster instances that have implemented a custom compute log manager.

## Migrating to 1.0

- Most of the classes and decorators in Dagster have moved to using a bare asterisk argument, enforcing that arguments are provided as keywords. **If using long lists of non-keyword arguments with dagster decorators or classes, you will likely run into errors in 1.0.** This can be fixed by switching to using keyword arguments.
- In an upcoming 1.x release, we plan to make a change that renders values supplied to `configured` in Dagit. Up through this point, values provided to `configured` have not been sent anywhere outside the process where they were used. This change will mean that, like other places you can supply configuration, `configured` is not a good place to put secrets: **You should not include any values in configuration that you don't want to be stored in the Dagster database and displayed inside Dagit.**
- **All submodules of dagster have been marked private.** We currently provide aliasing to avoid incurring linting errors, but in a future 1.x release, this will be removed, and imports from submodules of dagster may incur errors.
- The `dagster.experimental` submodule has been deleted, which previously contained dynamic output APIs, which are available from the top level of the `dagster` module.
- As of 1.0, **Dagster no longer guarantees support for python 3.6.** This is in line with [PEP 494](https://peps.python.org/pep-0494/), which outlines that 3.6 has reached end of life.
- Dagster’s integration libraries haven’t yet achieved the same API maturity as Dagster core. For this reason, all integration libraries will remain on a pre-1.0 (0.16.x) versioning track for the time being. However, 0.16.x library releases remain fully compatible with Dagster 1.x. In the coming months, we will graduate integration libraries one-by-one to the 1.x versioning track as they achieve API maturity. If you have installs of the form:

```
pip install dagster=={DAGSTER_VERSION} dagster-somelibrary=={DAGSTER_VERSION}
```

this should be converted to:

```
pip install dagster=={DAGSTER_VERSION} dagster-somelibrary
```

to make sure the correct library version is installed.

### Legacy API Removals

- Dagster's legacy APIs, which were marked "legacy" in 0.13.0, have been removed. This includes `@solid`, `SolidDefinition`, `@pipeline`, `PipelineDefinition`, `@composite_solid`, `CompositeSolidDefinition`, `ModeDefinition`, `PresetDefinition`, `PartitionSetDefinition`, `InputDefinition`, `OutputDefinition`, `DynamicOutputDefinition`, `pipeline_failure_sensor`, `@hourly_schedule`, `@daily_schedule`, `@weekly_schedule`, and `@monthly_schedule`. [Here is a guide](https://docs.dagster.io/0.15.6/guides/dagster/graph_job_op) to migrating from the legacy APIs to the stable APIs.
- Deprecated arguments to library ops have been switched to reflect stable APIs. This includes `input_defs`/`output_defs` arguments on `define_dagstermill_op`, which have been changed to `ins`/`outs` respectively, and `input_defs` argument on `create_shell_script_op`, which has been changed to `ins`.
- The `pipeline_selection` argument has been removed from `run_failure_sensor` and related decorators / functions, and `job_selection` has been deprecated. Instead, use `monitored_jobs`.
- `ScheduleExecutionContext` and `SensorExecutionContext` APIs have been removed. In 0.13.0, these were renamed to `ScheduleEvaluationContext` and `SensorEvaluationContext` respectively, and marked deprecated.
- Along with the rest of the legacy APIs, `execute_pipeline` has been removed. The functionality previously supplied by `execute_pipeline` has been split between `JobDefinition.execute_in_process` ([docs](https://docs.dagster.io/_apidocs/jobs#dagster.JobDefinition.execute_in_process)) and `execute_job` ([docs](https://docs.dagster.io/_apidocs/execution#dagster.execute_job)). If you were previously using `execute_pipeline` for in-process testing, then `JobDefinition.execute_in_process` should replace. If using `execute_pipeline` for out-of-process execution, or non-testing workflows, then `execute_job` is the recommended replacement.
- Alongside other removals of pipeline-related APIs, the `dagster pipeline` CLI subgroup has been removed in favor of `dagster job`.
- The `dagster new-project` CLI subgroup has been removed in favor of `dagster project`.
- `AssetGroup` and `build_assets_job`, which were advertised in an experimental iteration of software-defined assets, have been removed. Instead, check out the docs on [grouping assets](https://docs.dagster.io/concepts/assets/software-defined-assets#assigning-assets-to-groups), and the docs on [defining asset jobs](https://docs.dagster.io/concepts/ops-jobs-graphs/jobs#from-software-defined-assets).
- The deprecated `partition_mappings` arguments on `@asset` and `@multi_asset` have been removed. Instead, user the `partition_mapping` argument the corresponding `AssetIn`s.
- The deprecated `namespace` arguments on `@asset` and `AssetIn` have been removed. Instead, use the `key_prefix` argument.
- The `input_defs` and `output_defs` arguments on [OpDefinition](https://docs.dagster.io/_apidocs/ops#dagster.OpDefinition) have been removed, and replaced with `ins` and `outs` arguments. `input_defs`/`output_defs` have been deprecated since 0.13.0.
- The `preset_defs` argument on [JobDefinition](https://docs.dagster.io/_apidocs/jobs#dagster.JobDefinition) has been removed. When constructing a `JobDefinition` directly, config can be provided using the `config` argument instead. `preset_defs` has been deprecated since 0.13.0.
- `EventMetadata` and `EventMetadataEntryData` APIs have been removed. Instead, metadata should be specified using the [MetadataValue](https://docs.dagster.io/_apidocs/ops#dagster.MetadataValue) APIs.
- APIs referencing pipelines/solids in extension libraries have been removed. This includes `define_dagstermill_solid`, `make_dagster_pipeline_from_airflow_dag`, `create_databricks_job_solid`, the various `dbt_cli_*` and `dbt_rpc_*` solids, `bq_solid_for_queries`, `ge_validation_solid_factory`, `end_mlflow_run_on_pipeline_finished`, the various `shell_command_solid` APIs, `make_slack_on_pipeline_failure_sensor`, `snowflake_solid_for_query`, `end_mlflow_run_on_pipeline_finished`, and `create_spark_solid`.
- `custom_path_fs_io_manager` has been removed, as its functionality is entirely subsumed by the `fs_io_manager`, where a custom path can be specified via config.

### Removed API List

This serves as an exhaustive list of the removed APIs.

From the main Dagster module:

- `AssetGroup`
- `DagsterPipelineRunMetadataValue`
- `CompositeSolidDefinition`
- `InputDefinition`
- `Materialization`
- `ModeDefinition`
- `OutputDefinition`
- `PipelineDefinition`
- `PresetDefinition`
- `SolidDefinition`
- `SolidInvocation`
- `DynamicOutputDefinition`
- `composite_solid`
- `lambda_solid`
- `pipeline`
- `solid`
- `pipeline_failure_sensor`
- `CompositeSolidExecutionResult`
- `PipelineExecutionResult`
- `SolidExecutionResult`
- `SolidExecutionContext`
- `build_solid_context`
- `PipelineRun`
- `PipelineRunStatus`
- `default_executors`
- `execute_pipeline_iterator`
- `execute_pipeline`
- `execute_solid_within_pipeline`
- `reexecute_pipeline_iterator`
- `reexecute_pipeline`
- `execute_solid`
- `execute_solids_within_pipeline`
- `build_assets_job`
- `schedule_from_partitions`
- `PartitionSetDefinition`
- `ScheduleExecutionContext`
- `SensorExecutionContext`
- `PipelineFailureSensorContext`
- `daily_schedule`
- `hourly_schedule`
- `monthly_schedule`
- `weekly_schedule`
- `create_offset_partition_selector`
- `date_partition_range`
- `identity_partition_selector`
- `custom_path_fs_io_manager`

From libraries (APIs removed in 0.16.0 onwards):

- `dagster_airflow.make_dagster_pipeline_from_airflow_dag`
- `dagster_databricks.create_databricks_job_solid`
- `dagster_dbt.dbt_cli_compile`
- `dagster_dbt.dbt_cli_run`
- `dagster_dbt.dbt_cli_run_operation`
- `dagster_dbt.dbt_cli_snapshot`
- `dagster_dbt.dbt_cli_snapshot_freshness`
- `dagster_dbt.dbt_cli_test`
- `dagster_dbt.create_dbt_rpc_run_sql_solid`
- `dagster_dbt.dbt_rpc_run`
- `dagster_dbt.dbt_rpc_run_and_wait`
- `dagster_dbt.dbt_rpc_run_operation`
- `dagster_dbt.dbt_rpc_run_operation_and_wait`
- `dagster_dbt.dbt_rpc_snapshot`
- `dagster_dbt.dbt_rpc_snapshot_and_wait`
- `dagster_dbt.dbt_rpc_snapshot_freshness`
- `dagster_dbt.dbt_rpc_snapshot_freshness_and_wait`
- `dagster_dbt.dbt_rpc_test`
- `dagster_dbt.dbt_rpc_test_and_wait`
- `dagster_gcp.bq_solid_for_queries`
- `dagster_ge.ge_validation_solid_factory`
- `dagster_mlflow.end_mlflow_run_on_pipeline_finishes`
- `dagster_shell.create_shell_command_solid`
- `dagster_shell.create_shell_script_solid`
- `dagster_shell.shell_solid`
- `dagster_slack.make_slack_on_pipeline_failure_sensor`
- `dagster_msteams.make_teams_on_pipeline_failure_sensor`
- `dagster_snowflake.snowflake_solid_for_query`
- `dagster_spark.create_spark_solid`

## Migrating to 0.15.0

All items below are breaking changes unless marked with _(deprecation)_.

### Software-defined assets

This release marks the official transition of software-defined assets from experimental to stable. We made some final changes to incorporate feedback and make the APIs as consistent as possible:

- Support for adding tags to asset materializations, which was previously marked as experimental, has been removed.
- Some of the properties of the previously-experimental AssetsDefinition class have been renamed. group_names is now group_names_by_key, asset_keys_by_input_name is now keys_by_input_name, and asset_keys_by_output_name is now keys_by_output_name, asset_key is now key, and asset_keys is now keys.
- fs_asset_io_manager has been removed in favor of merging its functionality with fs_io_manager. fs_io_manager is now the default IO manager for asset jobs, and will store asset outputs in a directory named with the asset key. Similarly, removed adls2_pickle_asset_io_manager, gcs_pickle_asset_io_manager , and s3_pickle_asset_io_manager. Instead, adls2_pickle_io_manager, gcs_pickle_io_manager , and s3_pickle_io_manager now support software-defined assets.
- _(deprecation)_ The namespace argument on the @asset decorator and AssetIn has been deprecated. Users should use key_prefix instead.
- _(deprecation)_ AssetGroup has been deprecated. Users should instead place assets directly on repositories, optionally attaching resources using with_resources. Asset jobs should be defined using define_asset_job (replacing AssetGroup.build_job), and arbitrary sets of assets can be materialized using the standalone function materialize (replacing AssetGroup.materialize).
- _(deprecation)_ The outs property of the previously-experimental @multi_asset decorator now prefers a dictionary whose values are AssetOut objects instead of a dictionary whose values are Out objects. The latter still works, but is deprecated.

### Event records

- The get_event_records method on DagsterInstance now requires a non-None argument event_records_filter. Passing a None value for the event_records_filter argument will now raise an exception where previously it generated a deprecation warning.
- Removed methods events_for_asset_key and get_asset_events, which have been deprecated since 0.12.0.

### Extension libraries

- [dagster-dbt] (breaks previously-experimental API) When using the load_assets_from_dbt_project or load_assets_from_dbt_manifest , the AssetKeys generated for dbt sources are now the union of the source name and the table name, and the AssetKeys generated for models are now the union of the configured schema name for a given model (if any), and the model name. To revert to the old behavior: dbt_assets = load_assets_from_dbt_project(..., node_info_to_asset_key=lambda node_info: AssetKey(node_info["name"]).
- [dagster-k8s] In the Dagster Helm chart, user code deployment configuration (like secrets, configmaps, or volumes) is now automatically included in any runs launched from that code. Previously, this behavior was opt-in. In most cases, this will not be a breaking change, but in less common cases where a user code deployment was running in a different kubernetes namespace or using a different service account, this could result in missing secrets or configmaps in a launched run that previously worked. You can return to the previous behavior where config on the user code deployment was not applied to any runs by setting the includeConfigInLaunchedRuns.enabled field to false for the user code deployment. See the Kubernetes Deployment docs (https://docs.dagster.io/deployment/guides/kubernetes/deploying-with-helm#configure-your-user-deployment) for more details.
- [dagster-snowflake] dagster-snowflake has dropped support for python 3.6. The library it is currently built on, snowflake-connector-python, dropped 3.6 support in their recent 2.7.5 release.

### Other

- The prior_attempts_count parameter is now removed from step-launching APIs. This parameter was not being used, as the information it held was stored elsewhere in all cases. It can safely be removed from invocations without changing behavior.
- The FileCache class has been removed.
- Previously, when schedules/sensors targeted jobs with the same name as other jobs in the repo, the jobs on the sensor/schedule would silently overwrite the other jobs. Now, this will cause an error.

## Migrating to 0.14.0

If migrating from below 0.13.17, you can run

```
dagster instance migrate
```

This optional migration makes performance improvements to the runs page in Dagit.

### Breaking Changes

- The Dagster Daemon now uses the same workspace.yaml file as Dagit to locate your Dagster code. You should ensure that if you make any changes to your workspace.yaml file, they are included in both Dagit’s copy and the Dagster Daemon’s copy. When you make changes to the workspace.yaml file, you don’t need to restart either Dagit or the Dagster Daemon - in Dagit, you can reload the workspace from the Workspace tab, and the Dagster Daemon will periodically check the workspace.yaml file for changes every 60 seconds. If you are using the Dagster Helm chart, no changes are required to include the workspace in the Dagster Daemon.
- In previous releases, it was possible to supply either an AssetKey, or a function that produced an AssetKey from an OutputContext as the asset_key argument to an Out/OutputDefinition. The latter behavior makes it impossible to gain information about these relationships without running a job, and has been deprecated. However, we still support supplying a static AssetKey as an argument.
- We have renamed many of the core APIs that interact with ScheduleStorage, which keeps track of sensor/schedule state and ticks. The old term for the generic schedule/sensor “job” has been replaced by the term “instigator” in order to avoid confusion with the execution API introduced in 0.12.0. If you have implemented your own schedule storage, you may need to change your method signatures appropriately.
- Dagit is now powered by Starlette instead of Flask. If you have implemented a custom run coordinator, you may need to make the following change:

  ```python
  from flask import has_request_context, request

  def submit_run(self, context: SubmitRunContext) -> PipelineRun:
      jwt_claims_header = (
          request.headers.get("X-Amzn-Oidc-Data", None) if has_request_context() else None
      )
  ```

  Should be replaced by:

  ```python
  def submit_run(self, context: SubmitRunContext) -> PipelineRun:
      jwt_claims_header = context.get_request_header("X-Amzn-Oidc-Data")
  ```

- The Dagster Daemon now requires a workspace.yaml file, much like Dagit.
- Ellipsis (“...”) is now an invalid substring of a partition key. This is because Dagit accepts an ellipsis to specify partition ranges.
- [Helm] The Dagster Helm chart now only supported Kubernetes clusters above version 1.18.

### Deprecation: Metadata API Renames

Dagster’s metadata API has undergone a signficant overhaul. Changes include:

- To reflect the fact that metadata can be specified on definitions in addition to events, the following names are changing. The old names are deprecated, and will function as aliases for the new names until 0.15.0:
  - `EventMetadata` > `MetadataValue`
  - `EventMetadataEntry` > `MetadataEntry`
  - `XMetadataEntryData` > `XMetadataValue` (e.g. `TextMetadataEntryData` > `TextMetadataValue`)
- The `metadata_entries` keyword argument to events and Dagster types is deprecated. Instead, users should use the metadata keyword argument, which takes a dictionary mapping string labels to `MetadataValue`s.
- Arbitrary metadata on In/InputDefinition and Out/OutputDefinition is deprecated. In 0.15.0, metadata passed for these classes will need to be resolvable to `MetadataValue` (i.e. function like metadata everywhere else in Dagster).
- The description attribute of `EventMetadataEntry` is deprecated.
- The static API of `EventMetadataEntry` (e.g. `EventMetadataEntry.text`) is deprecated. In 0.15.0, users should avoid constructing `EventMetadataEntry` objects directly, instead utilizing the metadata dictionary keyword argument, which maps string labels to `MetadataValues`.

## Migrating to 0.13.0

Jobs, ops, and graphs have replaced pipelines, solids, modes, and presets as the stable core of the
system. [Here](https://docs.dagster.io/0.15.7/guides/dagster/graph_job_op) is a guide you can use to update your code using the legacy APIs into using the new Dagster core APIs. 0.13.0 is still compatible with the pipeline, solid, mode, and preset APIs, which means that you don't need to migrate your code to upgrade to 0.13.0.

## Migrating to 0.12.0

The new experimental core API experience in Dagit uses some features that require a data migration. Before enabling the experimental core API flag in Dagit, you will first need to run this command:

```
dagster instance migrate
```

If you are not going to enable the experimental core API experience, this data migration is optional. However, you may still want to run the migration anyway, which will enable better performance in viewing the Asset catalog in Dagit.

## Migrating to 0.11.0

### Action Required: Run and event storage schema changes

Run this after migrating to 0.11.0:

```
dagster instance migrate
```

This release includes several schema changes to the Dagster storages that improve performance, allow support for MySQL, and enable new features like asset tags and reliable backfills. After upgrading to 0.11.0, run the `dagster instance migrate` command to migrate your instance storage to the latest schema.

### Action Required: Schedule timezones

Schedules now run in UTC (instead of the system timezone) if no timezone has been set on the schedule. If you’re using a deprecated scheduler like `SystemCronScheduler` or `K8sScheduler`, we recommend that you switch to the native Dagster scheduler. The deprecated schedulers will be removed in the next Dagster release.

### Action Required: Asset storage

If upgrading directly to `0.11.0` from `0.9.22` or lower, you might notice some asset keys missing from the catalog if they have not been materialized using a version `0.9.16` or greater. We removed some back-compatibility for performance reasons. If this is the case, you can either run `dagster instance reindex` or execute the appropriate pipelines to materialize those assets again. In either case, the full history of the asset will still be maintained.

### Removals of Deprecated APIs

- The `instance` argument to `RunLauncher.launch_run` has been removed. If you have written a custom RunLauncher, you’ll need to update the signature of that method. You can still access the `DagsterInstance` on the `RunLauncher` via the `_instance` parameter.
- The `has_config_entry`, `has_configurable_inputs`, and `has_configurable_outputs` properties of `solid` and `composite_solid` have been removed.
- The deprecated optionality of the `name` argument to `PipelineDefinition` has been removed, and the argument is now required.
- The `execute_run_with_structured_logs` and `execute_step_with_structured_logs` internal CLI entry points have been removed. Use `execute_run` or `execute_step` instead.
- The `python_environment` key has been removed from `workspace.yaml`. Instead, to specify that a repository location should use a custom python environment, set the `executable_path` key within a `python_file` or `python_module` key. See [the docs](https://docs.dagster.io/concepts/code-locations/workspace-files) for more information on configuring your `workspace.yaml` file.
- [dagster-dask] The deprecated schema for reading or materializing dataframes has been removed. Use the `read` or `to` keys accordingly.

### Breaking Changes

- Names provided to `alias` on solids now enforce the same naming rules as solids. You may have to update provided names to meet these requirements.
- The `retries` method on `Executor` should now return a `RetryMode` instead of a `Retries`. This will only affect custom `Executor` classes.
- Submitting partition backfills in Dagit now requires `dagster-daemon` to be running. The instance setting in `dagster.yaml` to optionally enable daemon-based backfills has been removed, because all backfills are now daemon-based backfills.

  ```
  # removed, no longer a valid setting in dagster.yaml

  backfill:
    daemon_enabled: true
  ```

The corresponding value flag `dagsterDaemon.backfill.enabled` has also been removed from the Dagster helm chart.

- The sensor daemon interval settings in `dagster.yaml` has been removed. The sensor daemon now runs in a continuous loop so this customization is no longer useful.

  ```
  # removed, no longer a valid setting in dagster.yaml

  sensor_settings:
    interval_seconds: 10
  ```

## Migrating to 0.10.0

### Action Required: Run and event storage schema changes

```bash
# Run after migrating to 0.10.0

$ dagster instance migrate
```

This release includes several schema changes to the Dagster storages that improve performance and
enable new features like sensors and run queueing. After upgrading to 0.10.0, run the
`dagster instance migrate` command to migrate your instance storage to the latest schema. This will
turn off any running schedules, so you will need to restart any previously running schedules after
migrating the schema. Before turning them back on, you should follow the steps below to migrate
to `DagsterDaemonScheduler`.

### New scheduler: DagsterDaemonScheduler

This release includes a new `DagsterDaemonScheduler` with improved fault tolerance and full support
for timezones. We highly recommend upgrading to the new scheduler during this release. The existing
schedulers, `SystemCronScheduler` and `K8sScheduler`, are deprecated and will be removed in a
future release.

#### Steps to migrate

Instead of relying on system cron or k8s cron jobs, the `DaemonScheduler` uses the new
`dagster-daemon` service to run schedules. This requires running the `dagster-daemon` service as a
part of your deployment.

Refer to our [deployment documentation](https://docs.dagster.io/deployment) for a guides on how to
set up and run the daemon process for local development, Docker, or Kubernetes deployments.

**If you are currently using the SystemCronScheduler or K8sScheduler:**

1. Stop any currently running schedules, to prevent any dangling cron jobs from being left behind.
   You can do this through the Dagit UI, or using the following command:

   ```bash
   dagster schedule stop --location {repository_location_name} {schedule_name}
   ```

   If you do not stop running schedules before changing schedulers, Dagster will throw an exception
   on startup due to the misconfigured running schedules.

2. In your `dagster.yaml` file, remove the `scheduler:` entry. If there is no `scheduler:` entry,
   the `DagsterDaemonScheduler` is automatically used as the default scheduler.

3. Start the `dagster-daemon` process. Guides can be found in our
   [deployment documentations](https://docs.dagster.io/deployment).

See our [schedules troubleshooting guide](https://docs.dagster.io/troubleshooting/schedules) for
help if you experience any problems with the new scheduler.

**If you are not using a legacy scheduler:**

No migration steps are needed, but make sure you run `dagster instance migrate` as a part of
upgrading to 0.10.0.

### Deprecation: Intermediate Storage

We have deprecated the intermediate storage machinery in favor of the new IO manager abstraction,
which offers finer-grained control over how inputs and outputs are serialized and persisted. Check
out the [IO Managers Overview](https://docs.dagster.io/concepts/io-management/io-managers) for
more information.

#### Steps to Migrate

- We have deprecated the top level `"storage"` and `"intermediate_storage"` fields on `run_config`.
  If you are currently executing pipelines as follows:

  ```python
  @pipeline
  def my_pipeline():
      ...

  execute_pipeline(
      my_pipeline,
      run_config={
          "intermediate_storage": {
              "filesystem": {"base_dir": ...}
          }
      },
  )

  execute_pipeline(
      my_pipeline,
      run_config={
          "storage": {
              "filesystem": {"base_dir": ...}
          }
      },
  )
  ```

  You should instead use the built-in IO manager `fs_io_manager`, which can be attached to your
  pipeline as a resource:

  ```python
  @pipeline(
      mode_defs=[
          ModeDefinition(
              resource_defs={"io_manager": fs_io_manager}
          )
      ],
  )
  def my_pipeline():
      ...

  execute_pipeline(
      my_pipeline,
      run_config={
          "resources": {
              "io_manager": {"config": {"base_dir": ...}}
          }
      },
  )
  ```

  There are corresponding IO managers for other intermediate storages, such as the S3- and
  ADLS2-based storages

- We have deprecated `IntermediateStorageDefinition` and `@intermediate_storage`.

  If you have written custom intermediate storage, you should migrate to custom IO managers
  defined using the `@io_manager` API. We have provided a helper method,
  `io_manager_from_intermediate_storage`, to help migrate your existing custom intermediate
  storages to IO managers.

  ```python
  my_io_manager_def = io_manager_from_intermediate_storage(
      my_intermediate_storage_def
  )

  @pipeline(
      mode_defs=[
          ModeDefinition(
              resource_defs={
                  "io_manager": my_io_manager_def
              }
          ),
      ],
  )
  def my_pipeline():
      ...
  ```

- We have deprecated the `intermediate_storage_defs` argument to `ModeDefinition`, in favor of the
  new IO managers, which should be attached using the `resource_defs` argument.

### Removal: input_hydration_config and output_materialization_config

Use `dagster_type_loader` instead of `input_hydration_config` and `dagster_type_materializer`
instead of `output_materialization_config`.

On `DagsterType` and type constructors in `dagster_pandas` use the `loader` argument instead of
`input_hydration_config` and the `materializer` argument instead of `dagster_type_materializer`
argument.

### Removal: repository key in workspace YAML

We have removed the ability to specify a repository in your workspace using the `repository:` key.
Use `load_from:` instead when specifying how to load the repositories in your workspace.

### Deprecated: python_environment key in workspace YAML

The `python_environment:` key is now deprecated and will be removed in a future release.

Previously, when you wanted to load a repository location in your workspace using a different
Python environment from Dagit’s Python environment, you needed to use a `python_environment:` key
under `load_from:` instead of the `python_file:` or `python_package:` keys. Now, you can simply
customize the `executable_path` in your workspace entries without needing to change to the
`python_environment:` key.

For example, the following workspace entry:

```yaml
- python_environment:
    executable_path: "/path/to/venvs/dagster-dev-3.7.6/bin/python"
    target:
      python_package:
        package_name: dagster_examples
        location_name: dagster_examples
```

should now be expressed as:

```yaml
- python_package:
    executable_path: "/path/to/venvs/dagster-dev-3.7.6/bin/python"
    package_name: dagster_examples
    location_name: dagster_examples
```

See our [Workspaces Overview](https://docs.dagster.io/overview/repositories-workspaces/workspaces#loading-from-an-external-environment)
for more information and examples.

### Removal: config_field property on definition classes

We have removed the property `config_field` on definition classes. Use `config_schema` instead.

### Removal: System Storage

We have removed the system storage abstractions, i.e. `SystemStorageDefinition` and
`@system_storage` ([deprecated in 0.9.0](#deprecation-system_storage_defs)).

Please note that the intermediate storage abstraction is also deprecated and will be removed in
0.11.0. [Use IO managers instead](#deprecation-intermediate-storage).

- We have removed the `system_storage_defs` argument (deprecated in 0.9.0) to `ModeDefinition`, in
  favor of `intermediate_storage_defs.`
- We have removed the built-in system storages, e.g. `default_system_storage_defs`
  (deprecated in 0.9.0).

### Removal: step_keys_to_execute

We have removed the `step_keys_to_execute` argument to `reexecute_pipeline` and
`reexecute_pipeline_iterator`, in favor of `step_selection`. This argument accepts the Dagster
selection syntax, so, for example, `*solid_a+` represents `solid_a`, all of its upstream steps,
and its immediate downstream steps.

### Breaking Change: date_partition_range

Starting in 0.10.0, Dagster uses the [pendulum](https://pypi.org/project/pendulum/) library to
ensure that schedules and partitions behave correctly with respect to timezones. As part of this
change, the `delta` parameter to `date_partition_range` (which determined the time different between
partitions and was a `datetime.timedelta`) has been replaced by a `delta_range` parameter
(which must be a string that's a valid argument to the `pendulum.period` function, such as
`"days"`, `"hours"`, or `"months"`).

For example, the following partition range for a monthly partition set:

```python
date_partition_range(
    start=datetime.datetime(2018, 1, 1),
    end=datetime.datetime(2019, 1, 1),
    delta=datetime.timedelta(months=1)
)
```

should now be expressed as:

```python
date_partition_range(
    start=datetime.datetime(2018, 1, 1),
    end=datetime.datetime(2019, 1, 1),
    delta_range="months"
)
```

### Breaking Change: PartitionSetDefinition.create_schedule_definition

When you create a schedule from a partition set using
`PartitionSetDefinition.create_schedule_definition`, you now must supply a `partition_selector`
argument that tells the scheduler which partition to use for a given schedule time.

We have added two helper functions, `create_offset_partition_selector` and
`identity_partition_selector`, that capture two common partition selectors (schedules that execute
at a fixed offset from the partition times, e.g. a schedule that creates the previous day's
partition each morning, and schedules that execute at the same time as the partition times).

The previous default partition selector was `last_partition`, which didn't always work as expected
when using the default scheduler and has been removed in favor of the two helper partition selectors
above.

For example, a schedule created from a daily partition set that fills in each partition the next
day at 10AM would be created as follows:

```python
partition_set = PartitionSetDefinition(
    name='hello_world_partition_set',
    pipeline_name='hello_world_pipeline',
    partition_fn= date_partition_range(
        start=datetime.datetime(2021, 1, 1),
        delta_range="days",
        timezone="US/Central",
    )
    run_config_fn_for_partition=my_run_config_fn,
)

schedule_definition = partition_set.create_schedule_definition(
    "daily_10am_schedule",
    "0 10 * * *",
    partition_selector=create_offset_partition_selector(lambda d: d.subtract(hours=10, days=1))
    execution_timezone="US/Central",
)
```

### Renamed: Helm values

Following convention in the [Helm docs](https://helm.sh/docs/chart_best_practices/values/#naming-conventions),
we now camel case all of our Helm values. To migrate to 0.10.0, you'll need to update your
`values.yaml` with the following renames:

- `pipeline_run` → `pipelineRun`
- `dagster_home` → `dagsterHome`
- `env_secrets` → `envSecrets`
- `env_config_maps` → `envConfigMaps`

### Restructured: scheduler in Helm values

When specifying the Dagster instance scheduler, rather than using a boolean field to switch between
the current options of `K8sScheduler` and `DagsterDaemonScheduler`, we now require the scheduler
type to be explicitly defined under `scheduler.type`. If the user specified `scheduler.type` has
required config, additional fields will need to be specified under `scheduler.config`.

`scheduler.type` and corresponding `scheduler.config` values are enforced via
[JSON Schema](https://helm.sh/docs/topics/charts/#schema-files).

For example, if your Helm values previously were set like this to enable the
`DagsterDaemonScheduler`:
​

```yaml
scheduler:
  k8sEnabled: false
```

​
You should instead have:
​

```yaml
scheduler:
  type: DagsterDaemonScheduler
```

### Restructured: celery and k8sRunLauncher in Helm values

`celery` and `k8sRunLauncher` now live under `runLauncher.config.celeryK8sRunLauncher` and
`runLauncher.config.k8sRunLauncher` respectively. Now, to enable celery, `runLauncher.type` must
equal `CeleryK8sRunLauncher`. To enable the vanilla K8s run launcher, `runLauncher.type` must
equal `K8sRunLauncher`.

`runLauncher.type` and corresponding `runLauncher.config` values are enforced via
[JSON Schema](https://helm.sh/docs/topics/charts/#schema-files).

For example, if your Helm values previously were set like this to enable the `K8sRunLauncher`:
​

```yaml
celery:
  enabled: false
​
k8sRunLauncher:
  enabled: true
  jobNamespace: ~
  loadInclusterConfig: true
  kubeconfigFile: ~
  envConfigMaps: []
  envSecrets: []
```

​
You should instead have:
​

```yaml
runLauncher:
  type: K8sRunLauncher
  config:
    k8sRunLauncher:
      jobNamespace: ~
      loadInclusterConfig: true
      kubeconfigFile: ~
      envConfigMaps: []
      envSecrets: []
```

### New Helm defaults

By default, `userDeployments` is enabled and the `runLauncher` is set to the `K8sRunLauncher`.
Along with the latter change, all message brokers (e.g. `rabbitmq` and `redis`) are now disabled
by default.

If you were using the `CeleryK8sRunLauncher`, one of `rabbitmq` or `redis` must now be explicitly
enabled in your Helm values.

## Migrating to 0.9.0

### Removal: config argument

We have removed the `config` argument to the `ConfigMapping`, `@composite_solid`, `@solid`,
`SolidDefinition`, `@executor`, `ExecutorDefinition`, `@logger`, `LoggerDefinition`, `@resource`,
and `ResourceDefinition` APIs, which we deprecated in 0.8.0, in favor of `config_schema`, as
described [here](#renaming-config).

## Migrating to 0.8.8

### Deprecation: Materialization

We deprecated the `Materialization` event type in favor of the new `AssetMaterialization` event type,
which requires the `asset_key` parameter. Solids yielding `Materialization` events will continue
to work as before, though the `Materialization` event will be removed in a future release.

### Deprecation: system_storage_defs

We are starting to deprecate "system storages" - instead of pipelines having a system storage
definition which creates an intermediate storage, pipelines now directly have an intermediate
storage definition.

- We have added an `intermediate_storage_defs` argument to `ModeDefinition`, which accepts a
  list of `IntermediateStorageDefinition`s, e.g. `s3_plus_default_intermediate_storage_defs`.
  As before, the default includes an in-memory intermediate and a local filesystem intermediate
  storage.
- We have deprecated `system_storage_defs` argument to `ModeDefinition` in favor of
  `intermediate_storage_defs`. `system_storage_defs` will be removed in 0.10.0 at the earliest.
- We have added an `@intermediate_storage` decorator, which makes it easy to define intermediate
  storages.
- We have added `s3_file_manager` and `local_file_manager` resources to replace the file managers
  that previously lived inside system storages. The airline demo has been updated to include
  an example of how to do this:
  https://github.com/dagster-io/dagster/blob/0.8.8/examples/airline_demo/airline_demo/solids.py#L171.

For example, if your `ModeDefinition` looks like this:

```python
from dagster_aws.s3 import s3_plus_default_storage_defs

ModeDefinition(system_storage_defs=s3_plus_default_storage_defs)
```

it is recommended to make it look like this:

```python
from dagster_aws.s3 import s3_plus_default_intermediate_storage_defs

ModeDefinition(intermediate_storage_defs=s3_plus_default_intermediate_storage_defs)
```

## Migrating to 0.8.7

### Loading python modules from the working directory

Loading python modules reliant on the working directory being on the PYTHONPATH is no longer
supported. The `dagster` and `dagit` CLI commands no longer add the working directory to the
PYTHONPATH when resolving modules, which may break some imports. Explicitly installed python
packages can be specified in workspaces using the `python_package` workspace yaml config option.
The `python_module` config option is deprecated and will be removed in a future release.

## Migrating to 0.8.6

### dagster-celery

The `dagster-celery` module has been broken apart to manage dependencies more coherently. There
are now three modules: `dagster-celery`, `dagster-celery-k8s`, and `dagster-celery-docker`.

Related to above, the `dagster-celery worker start` command now takes a required `-A` parameter
which must point to the `app.py` file within the appropriate module. E.g if you are using the
`celery_k8s_job_executor` then you must use the `-A dagster_celery_k8s.app` option when using the
`celery` or `dagster-celery` cli tools. Similar for the `celery_docker_executor`:
`-A dagster_celery_docker.app` must be used.

### Deprecation: input_hydration_config and output_materialization_config

We renamed the `input_hydration_config` and `output_materialization_config` decorators to
`dagster_type_` and `dagster_type_materializer` respectively. We also renamed DagsterType's
`input_hydration_config` and `output_materialization_config` arguments to `loader` and `materializer`
respectively.

For example, if your dagster type definition looks like this:

```python
from dagster import DagsterType, input_hydration_config, output_materialization_config


@input_hydration_config(config_schema=my_config_schema)
def my_loader(_context, config):
    '''some implementation'''


@output_materialization_config(config_schema=my_config_schema)
def my_materializer(_context, config):
    '''some implementation'''


MyType = DagsterType(
    input_hydration_config=my_loader,
    output_materialization_config=my_materializer,
    type_check_fn=my_type_check,
)
```

it is recommended to make it look like this:

```python
from dagster import DagsterType, dagster_type_loader, dagster_type_materializer


@dagster_type_loader(config_schema=my_config_schema)
def my_loader(_context, config):
    '''some implementation'''


@dagster_type_materializer(config_schema=my_config_schema)
def my_materializer(_context, config):
    '''some implementation'''


MyType = DagsterType(
    loader=my_loader,
    materializer=my_materializer,
    type_check_fn=my_type_check,
)
```

## Migrating to 0.8.5

### Python 3.5

Python 3.5 is no longer under test.

### Engine and ExecutorConfig -> Executor

`Engine` and `ExecutorConfig` have been deleted in favor of `Executor`. Instead of the `@executor` decorator decorating a function that returns an `ExecutorConfig` it should now decorate a function that returns an `Executor`.

## Migrating to 0.8.3

### Change: gcs_resource

Previously, the `gcs_resource` returned a `GCSResource` wrapper which had a single `client` property that returned a `google.cloud.storage.client.Client`. Now, the `gcs_resource` returns the client directly.

To update solids that use the `gcp_resource`, change:

```
context.resources.gcs.client
```

To:

```
context.resources.gcs
```

## Migrating to 0.8.0

### Repository loading

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

#### Steps to migrate

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

### Repository definition

The `@scheduler` and `@repository_partitions` decorators have been removed. In addition, users
should prefer the new `@repository` decorator to instantiating `RepositoryDefinition` directly.

One consequence of this change is that `PartitionSetDefinition` names, including those defined by
a `PartitionScheduleDefinition`, must now be unique within a single repository.

#### Steps to migrate

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

### Reloadable repositories

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

### Renaming environment_dict and removing RunConfig

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

### Deprecation: config argument

In 0.8.0, we've renamed the common `config` parameter to the user-facing definition APIs to
`config_schema`. This is intended to reduce ambiguity between config values (provided at
execution time) and their user-specified schemas (provided at definition time). This change affects
the `ConfigMapping`, `@composite_solid`, `@solid`, `SolidDefinition`, `@executor`,
`ExecutorDefinition`, `@logger`, `LoggerDefinition`, `@resource`, and `ResourceDefinition` APIs.
In the CLI, `dagster pipeline execute` and `dagster pipeline launch` now take `-c/--config` instead
of `-e/--env`.

### Renaming solid_subset and enabling support for solid selection DSL in Python API

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

### Removal of deprectated properties, methods, and arguments

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

### Removal of Path config type

The built-in config type `Path` has been removed. Use `String`.

### dagster-bash

This package has been renamed to dagster-shell. The`bash_command_solid` and `bash_script_solid`
solid factory functions have been renamed to `create_shell_command_solid` and
`create_shell_script_solid`.

### Dask config

The config schema for the `dagster_dask.dask_executor` has changed. The previous config should
now be nested under the key `local`.

### Spark solids

`dagster_spark.SparkSolidDefinition` has been removed - use `create_spark_solid` instead.

## Migrating to 0.7.0

The 0.7.0 release contains a number of breaking API changes. While listed
in the changelog, this document goes into more detail about how to
resolve the change easily. Most of the eliminated or changed APIs
can be adjusted to with relatively straightforward changes.

The easiest way to use this guide is to search for associated
error text.

### Dagster Types

There have been substantial changes to the core dagster type APIs.

Error:

`ImportError: cannot import name 'dagster_type' from 'dagster'`

Fix:

Use `usable_as_dagster_type` instead. If dynamically generating
types, construct using `DagsterType` instead.

Error:

`ImportError: cannot import name 'as_dagster_type' from 'dagster'`

Fix:

Use `make_python_type_usable_as_dagster_type` instead.

Error:

`dagster.core.errors.DagsterInvalidDefinitionError: type_check_fn argument type "BadType" must take 2 arguments, received 1`

Fix:

Add a context argument (named `_`, `_context`, `context`, or `context_`) as the first argument
of the `type_check_fn`. The second argument is the value being type-checked.

Further Information:

We have eliminated the `@dagster_type` and `as_dagster_type`
APIs, which previously were promoted as our primary type
creation API. This API automatically created a mapping
between a Python type and a Dagster Type. While convenient,
this ended up causing unpredictable behavior based on import
order, as well as being wholly incompatible with dynamically
created Dagster types.

Our core type creation API is now the `DagsterType` class. It creates a
Dagster type (which is just an instance of `DagsterType`) that can be passed
to `InputDefinition` and `OutputDefinition`.

The functionality of `@dagster_type` is preserved, but under a different name:
`usable_as_dagster_type`. This decorator signifies that the author wants
a bare Python type to be usable in contexts that expect dagster types, such as
an `InputDefinition` or `OutputDefinition`.

Any user that had been programmatically creating dagster types and was forced
to decorate classes in local scope using `@dagster_type` and return that class
should instead just create a `DagsterType` directly.

`as_dagster_type` has replaced by `make_python_type_usable_as_dagster_type`.
The semantics of `as_dagster_type` did not indicate what is was actually doing
very well. This function is meant to take an _existing_ type -- often from
a library that one doesn't control -- and make that type usable as a dagster
type, the second argument.

The `type_check_fn` argument has been renamed from `type_check` and now takes
two arguments instead of one. The first argument is a instance of `TypeCheckContext`;
the second argument is the value being checked. This allows the type check
to have access to resources.

### Config System

The config APIs have been renamed to have no collisions with names in neither python's
`typing` API nor the dagster type system. Here are some example errors:

Error:

`dagster.core.errors.DagsterInvariantViolationError: Cannot resolve Dagster Type Optional.Int to a config type. Repr of type: <dagster.core.types.dagster_type.OptionalType object at 0x102bb2a50>`

Fix:

Use `Noneable` of `Optional`.

Error:

`TypeError: 'DagsterDictApi' object is not callable`

Fix:

Pass a raw python dictionary instead of Dict.

`config=Dict({'foo': str})` becomes `config={'foo': str}`

Error:

`ImportError: cannot import name 'PermissiveDict' from 'dagster'`

Fix:

Use `Permissive` instead.

Error:

`dagster.core.errors.DagsterInvariantViolationError: Cannot use List in the context of config. Please use a python list (e.g. [int]) or dagster.Array (e.g. Array(int)) instead.`

Fix:

This happens when a properly constructed List is used within config. Use Array instead.

Error:

`dagster.core.errors.DagsterInvalidDefinitionError: Invalid type: dagster_type must be DagsterType, a python scalar, or a python type that has been marked usable as a dagster type via @usable_dagster_type or make_python_type_usable_as_dagster_type: got <dagster.config.config_type.Noneable object at 0x1029c8a10>.`

Fix:

This happens when a List takes an invalid argument and is never constructed.
The error could be much better. This is what happens a config type (in this
case `Noneable`) is passed to a `List`. The fix is to use either `Array` or
to use a bare list with a single element, which is a config type.

### Required Resources

Any solid, type, or configuration function that accesses a resource off of a context
object must declare that resource key with a `required_resource_key` argument.

Error:

`DagsterUnknownResourceError: Unknown resource <resource_name>. Specify <resource_name> as a required resource on the compute / config function that accessed it.`

Fix:

Find any references to `context.resources.<resource_name>`, and ensure that the enclosing
solid definition, type definition, or config function has the resource key specified
in its `required_resource_key` argument.

Further information:

When only a subset of solids are being executed in a given process, we only need to
initialize resources that will be used by that subset of solids. In order to improve
the performance of pipeline execution, we need each solid and type to explicitly declare
its required resources.

As a result, we should see improved performance for pipeline subset execution,
multiprocess execution, and retry execution.

### RunConfig Removed

Error:

`AttributeError: 'ComputeExecutionContext' object has no attribute 'run_config'`

Fix:

Replace all references to `context.run_config` with `context.pipeline_run`. The `run_config` field
on the pipeline execution context has been removed and replaced with `pipeline_run`, a `PipelineRun`
instance. Along with the fields previously on `RunConfig`, this also includes the pipeline run
status.

### Scheduler

Scheduler configuration has been moved to the `dagster.yaml`. After upgrading, the previous schedule
history is no longer compatible with the new storage.

Make sure you delete your existing `$DAGSTER_HOME/schedules` directory, then run:

```
dagster schedule wipe && dagster schedule up
```

Error:

`TypeError: schedules() got an unexpected keyword argument 'scheduler'`

Fix:

The `@schedules` decorator no longer takes a `scheduler` argument. Remove the argument and instead
configure the scheduler on the instance.

Instead of:

```
@schedules(scheduler=SystemCronScheduler)
def define_schedules():
    ...
```

Remove the `scheduler` argument:

```
@schedules
def define_schedules():
    ...
```

Configure the scheduler on your instance by adding the following to `$DAGSTER_HOME/dagster.yaml`:

```
scheduler:
    module: dagster_cron.cron_scheduler
    class: SystemCronScheduler
```

Error:

`TypeError: <lambda>() takes 0 positional arguments but 1 was given"`

Stack Trace:

```
    File ".../dagster/python_modules/dagster/dagster/core/definitions/schedule.py", line 171, in should_execute
        return self._should_execute(context)
```

Fix:

The `should_execute` and `environment_dict_fn` argument to `ScheduleDefinition` now has a required
first argument `context`, representing the `ScheduleExecutionContext`.
