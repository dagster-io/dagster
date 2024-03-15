# Changelog

## 1.6.11 (core) / 0.22.11 (libraries)

### Bugfixes

- Fixed an issue where `dagster dev` or the Dagster UI would display an error when loading jobs created with op or asset selections.

## 1.6.10 (core) / 0.22.10 (libraries)

### New

- Latency improvements to the scheduler when running many simultaneous schedules.

### Bugfixes

- The performance of loading the Definitions snapshot from a code server when large `@multi_asset` s are in use has been drastically improved.
- The snowflake quickstart example project now renames the “by” column to avoid reserved snowflake names. Thanks @[jcampbell](https://github.com/jcampbell)!
- The existing group name (if any) for an asset is now retained if `the_asset.with_attributes` is called without providing a group name. Previously, the existing group name was erroneously dropped. Thanks @[ion-elgreco](https://github.com/ion-elgreco)!
- [dagster-dbt] Fixed an issue where Dagster events could not be streamed from `dbt source freshness`.
- [dagster university] Removed redundant use of `MetadataValue` in Essentials course. Thanks @[stianthaulow](https://github.com/stianthaulow)!
- [ui] Increased the max number of plots on the asset plots page to 100.

### Breaking Changes

- The `tag_keys` argument on `DagsterInstance.get_run_tags`is no longer optional. This has been done to remove an easy way of accidentally executing an extremely expensive database operation.

### Dagster Cloud

- The maximum number of concurrent runs across all branch deployments is now configurable. This setting can now be set via GraphQL or the CLI.
- [ui] In Insights, fixed display of table rows with zero change in value from the previous time period.
- [ui] Added deployment-level Insights.
- [ui] Fixed an issue causing void invoices to show up as “overdue” on the billing page.
- [experimental] Branch deployments can now indicate the new and modified assets in the branch deployment as compared to the main deployment. To enable this feature, turn on the “Enable experimental branch deployment asset graph diffing” user setting.

## 1.6.9 (core) / 0.22.9 (libraries)

### New

- [ui] When viewing logs for a run, the date for a single log row is now shown in the tooltip on the timestamp. This helps when viewing a run that takes place over more than one date.
- Added suggestions to the error message when selecting asset keys that do not exist as an upstream asset or in an `AssetSelection.`
- Improved error messages when trying to materialize a subset of a multi-asset which cannot be subset.
- [dagster-snowflake] `dagster-snowflake` now requires `snowflake-connector-python>=3.4.0`
- [embedded-elt] `@sling_assets` accepts an optional name parameter for the underlying op
- [dagster-openai] `dagster-openai` library is now available.
- [dagster-dbt] Added a new setting on `DagsterDbtTranslatorSettings` called `enable_duplicate_source_asset_keys` that allows users to set duplicate asset keys for their dbt sources. Thanks @hello-world-bfree!
- Log messages in the Dagster daemon for unloadable sensors and schedules have been removed.
- [ui] Search now uses a cache that persists across pageloads which should greatly improve search performance for very large orgs.
- [ui] groups/code locations in the asset graph’s sidebar are now sorted alphabetically.

### Bugfixes

- Fixed issue where the input/output schemas of configurable IOManagers could be ignored when providing explicit input / output run config.
- Fixed an issue where enum values could not properly have a default value set in a `ConfigurableResource`.
- Fixed an issue where graph-backed assets would sometimes lose user-provided descriptions due to a bug in internal copying.
- [auto-materialize] Fixed an issue introduced in 1.6.7 where updates to ExternalAssets would be ignored when using AutoMaterializePolicies which depended on parent updates.
- [asset checks] Fixed a bug with asset checks in step launchers.
- [embedded-elt] Fix a bug when creating a `SlingConnectionResource` where a blank keyword argument would be emitted as an environment variable
- [dagster-dbt] Fixed a bug where emitting events from `dbt source freshness` would cause an error.
- [ui] Fixed a bug where using the “Terminate all runs” button with filters selected would not apply the filters to the action.
- [ui] Fixed an issue where typing a search query into the search box before the search data was fetched would yield “No results” even after the data was fetched.

### Community Contributions

- [docs] fixed typo in embedded-elt.mdx (thanks [@cameronmartin](https://github.com/cameronmartin))!
- [dagster-databricks] log the url for the run of a databricks job (thanks [@smats0n](https://github.com/smats0n))!
- Fix missing partition property (thanks [christeefy](https://github.com/christeefy))!
- Add op_tags to @observable_source_asset decorator (thanks [@maxfirman](https://github.com/maxfirman))!
- [docs] typo in MultiPartitionMapping docs (thanks [@dschafer](https://github.com/dschafer))
- Allow github actions to checkout branch from forked repo for docs changes (ci fix) (thanks [hainenber](https://github.com/hainenber))!

### Experimental

- [asset checks] UI performance of asset checks related pages has been improved.
- [dagster-dbt] The class `DbtArtifacts` has been added for managing the behavior of rebuilding the manifest during development but expecting a pre-built one in production.

### Documentation

- Added example of writing compute logs to AWS S3 when customizing agent configuration.
- "Hello, Dagster" is now "Dagster Quickstart" with the option to use a Github Codespace to explore Dagster.
- Improved guides and reference to better running multiple isolated agents with separate queues on ECS.

### Dagster Cloud

- Microsoft Teams is now supported for alerts. [Documentation](https://docs.dagster.io/dagster-cloud/managing-deployments/setting-up-alerts)
- A `send sample alert` button now exists on both the alert policies page and in the alert policies editor to make it easier to debug and configure alerts without having to wait for an event to kick them off.

## 1.6.8 (core) / 0.22.8 (libraries)

### Bugfixes

- [dagster-embedded-elt] Fixed a bug in the `SlingConnectionResource` that raised an error when connecting to a database.

### Experimental

- [asset checks] `graph_multi_assets` with `check_specs` now support subsetting.

## 1.6.7 (core) / 0.22.7 (libraries)

### New

- Added a new `run_retries.retry_on_op_or_asset_failures` setting that can be set to false to make run retries only occur when there is an unexpected failure that crashes the run, allowing run-level retries to co-exist more naturally with op or asset retries. See [the docs](https://docs.dagster.io/deployment/run-retries#combining-op-and-run-retries) for more information.
- `dagster dev` now sets the environment variable `DAGSTER_IS_DEV_CLI` allowing subprocesses to know that they were launched in a development context.
- [ui] The Asset Checks page has been updated to show more information on the page itself rather than in a dialog.

### Bugfixes

- [ui] Fixed an issue where the UI disallowed creating a dynamic partition if its name contained the “|” pipe character.
- AssetSpec previously dropped the metadata and code_version fields, resulting in them not being attached to the corresponding asset. This has been fixed.

### Experimental

- The new `@multi_observable_source_asset` decorator enables defining a set of assets that can be observed together with the same function.
- [dagster-embedded-elt] New Asset Decorator `@sling_assets` and Resource `SlingConnectionResource` have been added for the `[dagster-embedded-elt.sling](http://dagster-embedded-elt.sling)` package. Deprecated `build_sling_asset`, `SlingSourceConnection` and `SlingTargetConnection`.
- Added support for op-concurrency aware run dequeuing for the `QueuedRunCoordinator`.

### Documentation

- Fixed reference documentation for isolated agents in ECS.
- Corrected an example in the Airbyte Cloud documentation.
- Added API links to OSS Helm deployment guide.
- Fixed in-line pragmas showing up in the documentation.

### Dagster Cloud

- Alerts now support Microsoft Teams.
- [ECS] Fixed an issue where code locations could be left undeleted.
- [ECS] ECS agents now support setting multiple replicas per code server.
- [Insights] You can now toggle the visibility of a row in the chart by clicking on the dot for the row in the table.
- [Users] Added a new column “Licensed role” that shows the user's most permissive role.

## 1.6.6 (core) / 0.22.6 (libraries)

### New

- Dagster officially supports Python 3.12.
- `dagster-polars` has been added as an integration. Thanks @danielgafni!
- [dagster-dbt] `@dbt_assets` now supports loading projects with semantic models.
- [dagster-dbt] `@dbt_assets` now supports loading projects with model versions.
- [dagster-dbt] `get_asset_key_for_model` now supports retrieving asset keys for seeds and snapshots. Thanks @aksestok!
- [dagster-duckdb] The Dagster DuckDB integration supports DuckDB version 0.10.0.
- [UPath I/O manager] If a non-partitioned asset is updated to have partitions, the file containing the non-partitioned asset data will be deleted when the partitioned asset is materialized, rather than raising an error.

### Bugfixes

- Fixed an issue where creating a backfill of assets with dynamic partitions and a backfill policy would sometimes fail with an exception.
- Fixed an issue with the type annotations on the `@asset` decorator causing a false positive in Pyright strict mode. Thanks @tylershunt!
- [ui] On the asset graph, nodes are slightly wider allowing more text to be displayed, and group names are no longer truncated.
- [ui] Fixed an issue where the groups in the asset graph would not update after an asset was switched between groups.
- [dagster-k8s] Fixed an issue where setting the `security_context` field on the `k8s_job_executor` didn't correctly set the security context on the launched step pods. Thanks @krgn!

### Experimental

- Observable source assets can now yield `ObserveResult`s with no `data_version`.
- You can now include `FreshnessPolicy`s on observable source assets. These assets will be considered “Overdue” when the latest value for the “dagster/data_time” metadata value is older than what’s allowed by the freshness policy.
- [ui] In Dagster Cloud, a new feature flag allows you to enable an overhauled asset overview page with a high-level stakeholder view of the asset’s health, properties, and column schema.

### Documentation

- Updated docs to reflect newly-added support for Python 3.12.

### Dagster Cloud

- [kubernetes] Fixed an issue where the Kubernetes agent would sometimes leave dangling kubernetes services if the agent was interrupted during the middle of being terminated.

## 1.6.5 (core) / 0.22.5 (libraries)

### New

- Within a backfill or within auto-materialize, when submitting runs for partitions of the same assets, runs are now submitted in lexicographical order of partition key, instead of in an unpredictable order.
- [dagster-k8s] Include k8s pod debug info in run worker failure messages.
- [dagster-dbt] Events emitted by `DbtCliResource` now include metadata from the dbt adapter response. This includes fields like `rows_affected`, `query_id` from the Snowflake adapter, or `bytes_processed` from the BigQuery adapter.

### Bugfixes

- A previous change prevented asset backfills from grouping multiple assets into the same run when using BackfillPolicies under certain conditions. While the backfills would still execute in the proper order, this could lead to more individual runs than necessary. This has been fixed.
- [dagster-k8s] Fixed an issue introduced in the 1.6.4 release where upgrading the Helm chart without upgrading the Dagster version used by user code caused failures in jobs using the `k8s_job_executor`.
- [instigator-tick-logs] Fixed an issue where invoking `context.log.exception` in a sensor or schedule did not properly capture exception information.
- [asset-checks] Fixed an issue where additional dependencies for dbt tests modeled as Dagster asset checks were not properly being deduplicated.
- [dagster-dbt] Fixed an issue where dbt model, seed, or snapshot names with periods were not supported.

### Experimental

- `@observable_source_asset`-decorated functions can now return an `ObserveResult`. This allows including metadata on the observation, in addition to a data version. This is currently only supported for non-partitioned assets.
- [auto-materialize] A new `AutoMaterializeRule.skip_on_not_all_parents_updated_since_cron` class allows you to construct `AutoMaterializePolicys` which wait for all parents to be updated after the latest tick of a given cron schedule.
- [Global op/asset concurrency] Ops and assets now take run priority into account when claiming global op/asset concurrency slots.

### Documentation

- Fixed an error in our asset checks docs. Thanks [@vaharoni](https://github.com/vaharoni)!
- Fixed an error in our Dagster Pipes Kubernetes docs. Thanks [@cameronmartin](https://github.com/cameronmartin)!
- Fixed an issue on the Hello Dagster! guide that prevented it from loading.
- Add specific capabilities of the Airflow integration to the Airflow integration page.
- Re-arranged sections in the I/O manager concept page to make info about using I/O versus resources more prominent.

# 1.6.4 (core) / 0.22.4 (libraries)

### New

- `build_schedule_from_partitioned_job` now supports creating a schedule from a static-partitioned job (Thanks `@craustin`!)
- [dagster-pipes] `PipesK8sClient` will now autodetect the namespace when using in-cluster config. (Thanks `@aignas`!)
- [dagster-pipes] `PipesK8sClient` can now inject the context in to multiple containers. (Thanks `@aignas`!)
- [dagster-snowflake] The Snowflake Pandas I/O manager now uses the `write_pandas` method to load Pandas DataFrames in Snowflake. To support this change, the database connector was switched from `SqlDbConnection` to `SnowflakeConnection` .
- [ui] On the overview sensors page you can now filter sensors by type.
- [dagster-deltalake-polars] Added LazyFrame support (Thanks `@ion-elgreco`!)
- [dagster-dbt] When using `@dbt_assets` and multiple dbt resources produce the same `AssetKey`, we now display an exception message that highlights the file paths of the misconfigured dbt resources in your dbt project.
- [dagster-k8s] The debug info reported upon failure has been improved to include additional information from the Job. (Thanks `@jblawatt`!)
- [dagster-k8s] Changed the Dagster Helm chart to apply `automountServiceAccountToken: false` to the default service account used by the Helm chart, in order to better comply with security policies. (Thanks `@MattyKuzyk`!)

### Bugfixes

- A unnecessary thread lock has been removed from the sensor daemon. This should improve sensor throughput for users with many sensors who have enabled threading.
- Retry from failure behavior has been improved for cases where dynamic steps were interrupted.
- Previously, when backfilling a set of assets which shared a BackfillPolicy and PartitionsDefinition, but had a non-default partition mapping between them, a run for the downstream asset could be launched at the same time as a separate run for the upstream asset, resulting in inconsistent partition ordering. Now, the downstream asset will only execute after the parents complete. (Thanks `@ruizh22`!)
- Previously, asset backfills would raise an exception if the code server became unreachable mid-iteration. Now, the backfill will pause until the next evaluation.
- Fixed a bug that was causing ranged backfills over dynamically partitioned assets to fail.
- [dagster-pipes] `PipesK8sClient` has improved handling for init containers and additional containers. (Thanks `@aignas`!)
- Fixed the `last_sensor_start_time` property of the `SensorEvaluationContext`, which would get cleared on ticks after the first tick after the sensor starts.
- [dagster-mysql] Fixed the optional `dagster instance migrate --bigint-migration`, which caused some operational errors on mysql storages.
- [dagster-dbt] Fixed a bug introduced in 1.6.3 that caused errors when ingesting asset checks with multiple dependencies.

### Deprecations

- The following methods on `AssetExecutionContext` have been marked deprecated, with their suggested replacements in parenthesis:
  - `context.op_config` (`context.op_execution_context.op_config`)
  - `context.node_handle` (`context.op_execution_context.node_handle`)
  - `context.op_handle` (`context.op_execution_context.op_handle`)
  - `context.op` (`context.op_execution_context.op`)
  - `context.get_mapping_key` (`context.op_execution_context.get_mapping_key`)
  - `context.selected_output_names` (`context.op_execution_context.selected_output_names`)
  - `context.dagster_run` (`context.run`)
  - `context.run_id` (`context.run.run_id`)
  - `context.run_config` (`context.run.run_config`)
  - `context.run_tags` (`context.run.tags`)
  - `context.has_tag` (`key in context.run.tags`)
  - `context.get_tag` (`context.run.tags.get(key)`)
  - `context.get_op_execution_context` (`context.op_execution_context`)
  - `context.asset_partition_key_for_output` (`context.partition_key`)
  - `context.asset_partition_keys_for_output` (`context.partition_keys`)
  - `context.asset_partitions_time_window_for_output` (`context.partition_time_window`)
  - `context.asset_partition_key_range_for_output` (`context.partition_key_range`)

### Experimental

- [asset checks] `@asset_check` now has a `blocking` parameter. When this is enabled, if the check fails with severity `ERROR` then any downstream assets in the same run won’t execute.

### Documentation

- The Branch Deployment docs have been updated to reflect support for backfills
- Added Dagster’s maximum supported Python version (3.11) to Dagster University and relevant docs
- Added documentation for recommended partition limits (a maximum of 25K per asset).
- References to the Enterprise plan have been renamed to Pro, to reflect recent plan name changes
- Added syntax example for setting environment variables in PowerShell to our dbt with Dagster tutorial
- [Dagster University] Dagster Essentials to Dagster v1.6, and introduced the usage of `MaterializeResult`
- [Dagster University] Fixed a typo in the Dagster University section on adding partitions to an asset (Thanks Brandon Peebles!)
- [Dagster University] Corrected lesson where sensors are covered (Thanks onefloid!)

### Dagster Cloud

- Agent tokens can now be locked down to particular deployments. Agents will not be able to run any jobs scheduled for deployments that they are not permitted to access. By default, agent tokens have access to all deployments in an organization. Use the `Edit` button next to an agent token on the `Tokens` tab in `Org Settings` to configure permissions for a particular token. You must be an Organization Admin to edit agent token permissions.

# 1.6.3 (core) / 0.22.3 (libraries)

### New

- Added support for the 3.0 release of the `pendulum` library, for Python versions 3.9 and higher.
- Performance improvements when starting run worker processes or step worker processes for runs in code locations with a large number of jobs.
- `AllPartitionMapping` now supports mapping to downstream partitions, enabling asset backfills with these dependencies. Thanks [@craustin](https://github.com/craustin)!
- [asset checks][experimental] `@asset_check` has new fields `additional_deps` and `additional_ins` to allow dependencies on assets other than the asset being checked.
- [ui] Asset graph group nodes now show status counts.
  - [dagster-snowflake] The Snowflake I/O Manager now has more specific error handling when a table doesn’t exist.
- [ui] [experimental] A new experimental UI for the auto-materialize history of a specific asset has been added. This view can be enabled under your user settings by setting “Use new asset auto-materialize history page”.
- [ui] Command clicking on an asset group will now select or deselect all assets in that group.
- [dagster-k8s] Added the ability to customize resource limits for initContainers used by Dagster system components in the Dagster Helm chart. Thanks **[@MattyKuzyk](https://github.com/MattyKuzyk)**!
- [dagster-k8s] Added the ability to specify additional containers and initContainers in code locations in the Helm chart. Thanks **[@craustin](https://github.com/craustin)**!
- [dagster-k8s] Explicitly listed the set of RBAC permissions used by the agent Helm chart role instead of using a wildcard. Thanks **[@easontm](https://github.com/easontm)**!
- [dagster-dbt] Support for `dbt-core==1.4.*` is now removed because [the version has reached end-of-life](https://docs.getdbt.com/docs/dbt-versions/core).

### Bugfixes

- Previously, calling `get_partition_keys_not_in_subset` on a `BaseTimeWindowPartitionsSubset` that targeted a partitions definition with no partitions (e.g. a future start date) would raise an error. Now, it returns an empty list.
- Fixed issue which could cause invalid runs to be launched if a code location was updated during the course of an AMP evaluation.
- Previously, some asset backfills raised an error when targeting multi-assets with internal asset dependencies. This has been fixed.
- Previously, using the `LocalComputeLogManager` on Windows could result in errors relating to invalid paths. This has been resolved. Thanks **[@hainenber](https://github.com/hainenber)**!
- An outdated path in the contribution guide has been updated. Thanks **[@hainenber](https://github.com/hainenber)**!
- [ui] Previously an error was sometimes raised when attempting to create a dynamic partition within a multi-partitioned asset via the UI. This has been fixed.
- [ui] The “Upstream materializations are missing” warning when launching a run has been expanded to warn about failed upstream materializations as well.
- [ui] The community welcome modal now renders properly in dark mode and some elements of Asset and Op graphs have higher contrast in both themes.
- [ui] Fixed dark mode colors for datepicker, error message, and op definition elements.
- [ui] Pressing the arrow keys to navigate op/asset graphs while the layout is loading no longer causes errors.
- [ui] Exporting asset and op graphs to SVG no longer fails when chrome extensions inject additional stylesheets into Dagster’s UI.
- [ui] Dagster now defaults to UTC when the user’s default timezone cannot be identified, rather than crashing with a date formatting error.
- [ui] Fixed an issue in the asset graph sidebar that caused groups to only list their first asset.
- [ui] Fixed an issue where sensors runs would undercount the number of dynamic partition requests added or deleted if there were multiple requests for additions/deletions.
- [docs] Fixed a typo in the “Using Dagster with Delta Lake” guide. Thanks **[@avriiil](https://github.com/avriiil)!**
- [asset checks] Fixed an issue which could cause errors when using asset checks with step launchers.
- [dagster-webserver] A bug preventing WebSocket connections from establishing on python 3.11+ has been fixed.
- [dagster-databricks] `DatabricksJobRunner` now ensures the correct`databricks-sdk` is installed. Thanks **[@zyd14](https://github.com/zyd14)**!
- [dagster-dbt] On run termination, an interrupt signal is now correctly forwarded to any in-progress dbt subprocesses.
- [dagster-dbt] Descriptions for dbt tests ingested as asset checks can now be populated using the `config.meta.description`. Thanks **[@CapitanHeMo](https://github.com/CapitanHeMo)**!
- [dagster-dbt] Previously, the error message displayed when no dbt profiles information was found would display an incorrect path. This has been fixed. Thanks **[@zoltanctoth](https://github.com/zoltanctoth)**!
- [dagster-k8s] `PipesK8sClient` can now correctly handle `load_incluster_config` . Thanks **[@aignas](https://github.com/aignas)**!

### Documentation

- Added a new category to **Concepts:** [Automation](https://docs.dagster.io/concepts/automation)**.** This page provides a high-level overview of the various ways Dagster allows you run data pipelines without manual intervention.
- Moved several concept pages under **Concepts > Automation**: Schedules, Sensors, Asset Sensors, and Auto-materialize Policies.

### Dagster Cloud

- Fixed an issue where configuring the `agent_queue` key in a `dagster_cloud.yaml` file incorrectly failed to validate when using the `dagster-cloud ci init` or `dagster-cloud ci check` commands during CI/CD.

# 1.6.2 (core) / 0.22.2 (libraries)

### New

- The warning for unloadable sensors and schedules in the Dagster UI has now been removed.
- When viewing an individual sensor or schedule, we now provide a button to reset the status of the sensor or schedule back to its default status as defined in code.

### Experimental

- [asset-checks] dbt asset checks now respect `warn_if`/ `error_if` severities

### Dagster Cloud

- Fixed a bug introduced in `1.6.0` where run status sensors did not cursor correctly when deployed on Dagster Cloud.
- Schedule and sensor mutations are now tracked in the audit log.

# 1.6.1 (core) / 0.22.1 (libraries)

### New

- Added experimental functionality which hides user code errors from the Dagster UI. You may enable this functionality by setting the `DAGSTER_REDACT_USER_CODE_ERRORS` environment variable to `1`.
- [dagster-dbt] `@dbt_assets` now accepts a `required_resource_keys` argument.

### Bugfixes

- Fixed a bug where a run that targets no steps is launched by an asset backfill when code updates are pushed after backfill launch time.
- Previously a graphQL error would be thrown on the asset backfill page if certain unpartitioned assets were changed to a partitioned assets. This has been fixed.
- [ui] Show run log timestamps in the user’s preferred hour cycle (12/24h) format.
- [ui] The “Export to SVG” option now works as expected in the improved asset graph UI.
- [ui] On the asset graph, hovering over a collapsed group or the title bar of an expanded group highlights all edges in/out of the group.
- Fixed occasional CI/CD errors when building documentation on a feature branch

### Community Contributions

- fix: add missing volumes and volumeMounts in job-instance-migrate.yaml. Thanks [@nhuray](https://github.com/nhuray)!

### Documentation

- Fixed typos in the docs.

### Dagster Cloud

- [ui] Fix dark theme colors for billing components.
- [ui] Show the number of users for each grant type (admin, editor, etc.) on the Users page.

# 1.6.0 (core) / 0.22.0 (libraries)

## Major Changes since 1.5.0 (core) / 0.21.0 (libraries)

### Core

- **Asset lineage graph UI revamp, to make it easier to visualize and navigate large graphs**
  - Lineage now flows left-to-right instead of top-to-bottom.
  - You can expand and collapse asset groups in the graph.
  - A new left-hand sidebar provides a list of assets, organized by asset group and code location.
  - You can right-click on assets or groups to filter or materialize them.
  - You can filter by compute kind.
- **Dark mode for the Dagster UI** – By default, Dagster will match your system’s light or dark theme but you can adjust this in the user settings in the top right of the UI.
- **Report asset materializations from the UI** – I.e. you record an asset materialization event without executing the code to materialize the asset. This is useful in cases where you overwrote data outside of Dagster, and you want Dagster to know about it and represent it in the UI. It’s also useful when you have a preexisting partitioned asset and start managing it with Dagster: you want Dagster to show the historical partitions as materialized instead of missing.
- **`MaterializeResult`, `AssetSpec`, and `AssetDep` now marked stable** – These APIs, introduced in Dagster 1.5, were previously marked experimental. They offer a more straightforward way of defining assets when you don’t want to use I/O managers.
- **Backfill previews** – When launching a backfill that covers assets with different partitions, can you now click “Preview” to see that partitions for each asset that will be covered by the backfill.
- **Viewing logs for a sensor or schedule tick is no longer considered experimental** – previously, accessing this functionality required turning on a feature flag in user settings.
- **Runs triggered by a sensor or schedule link to the tick that triggered them.**

### dagster-pipes

- **AWS Lambda Pipes client** –`PipesLambdaClient` [[guide](https://docs.dagster.io/guides/dagster-pipes/aws-lambda)].
- **Report arbitrary messages between pipes processes and the orchestrating process** – with `report_custom_message` and `get_custom_messages`.
- **Termination forwarding** – ensures that external processes are terminated when an orchestration process is.

## **Since 1.5.14 (core) / 0.21.14 (libraries)**

### New

- Default op/asset concurrency limits are now configurable at the deployment level, using the `concurrency` > `default_op_concurrency_limit` configuration in your `dagster.yaml` (OSS) or Deployment Settings page (Dagster Cloud). In OSS, this feature first requires a storage migration (e.g. `dagster instance migrate`).
- Zero-value op/asset concurrency limits are now supported. In OSS, this feature first requires a storage migration (e.g. `dagster instance migrate`).
- When a `Nothing`-typed output is returned from an `asset` or `op`, the `handle_output` function of the I/O manager will no longer be called. Users of most Dagster-maintained I/O managers will see no behavioral changes, but users of the In-Memory I/O manager, or custom I/O managers that store `Nothing`-typed outputs should reference the migration guide for more information.
- [ui] The updated asset graph is no longer behind an experimental flag. The new version features a searchable left sidebar, a horizontal DAG layout, context menus and collapsible groups!

### Bugfixes

- Previously, if a code location was re-deployed with modified assets during an iteration of the asset daemon, empty auto-materialize runs could be produced. This has been fixed.
- The CLI command `dagster asset materialize` will now return a non-zero exit code upon failure.
- [ui] The Dagster UI now shows resource descriptions as markdown instead of plain text.
- [ui] Viewing stdout/stderr logs for steps emitting hundreds of thousands of messages is much more performant and does not render the Run page unusable.
- [ui] Fixed an issue where sensors with intervals that were less than 30 seconds were shown with an interval of “~30s” in the UI. The correct interval is now shown.
- [dagster-graphql] Fixed an issue where the GraphQL Python client raised an unclear error if the request failed due to a permissions error.

### Breaking Changes

- A slight change has been made to run status sensors cursor values for Dagster instance using the default SQLite storage implementation. If you are using the default SQLite storage and you are upgrading directly from a version of `dagster<1.5.1`, you may see the first tick of your run status sensor skip runs that completed but were not yet registered by the sensor during your upgrade. This should not be common, but to avoid any chance of that, you may consider an interim upgrade to `dagster>=1.5.1,<1.6.0` first.

### Community Contributions

- Fixed a typo in the docs. Thanks [@tomscholz](https://github.com/tomscholz)!
- [dagster-pyspark] Added additional file exclude rules to the zip files created by Dagster Pyspark step launchers. Thanks [@maxfirman](https://github.com/maxfirman)!

### Documentation

- Added a high-level overview page for [Logging](https://docs.dagster.io/concepts/logging).

### Dagster Cloud

- Added the ability to annotate code locations with custom agent queues, allowing you to route requests for code locations in a single deployment to different agents. For example, you can route requests for one code location to an agent running in an on-premise data center but requests for all other code locations to another agent running in the cloud. For more information, see [the docs](https://docs.dagster.io/dagster-cloud/deployment/agents/running-multiple-agents#routing-requests-to-specific-agents).

# 1.5.14 / 0.21.14 (libraries)

### New

- Viewing logs for a sensor or schedule tick is now a generally available feature.
  - The feature flag to view sensor or schedule tick logs has been removed, as the feature is now enabled by default.
  - Logs can now be viewed even when the sensor or schedule tick fails.
  - The logs are now viewable in the sensor or schedule tick modal.
- `graph_multi_asset`s can now accept inputs as `kwargs`.
- [ui] The tick timeline for schedules and sensors now defaults to showing all ticks, instead of excluding skipped ticks. The previous behavior can be enabled by unchecking the “Skipped” checkbox below the timeline view.
- [ui] The updated asset graph is no longer behind an experimental flag. The new version features a searchable left sidebar, a horizontal DAG layout, context menus and collapsible groups!

### Bugfixes

- [ui] Fix layout and scrolling issues that arise when a global banner alert is displayed in the app.
- [ui] Use a larger version of the run config dialog in the Runs list in order to maximize the amount of visible config yaml.
- [ui] When a software-defined asset is removed from a code location, it will now also be removed from global search.
- [ui] When selecting assets in the catalog, you can now opt to materialize only “changed and missing” items in your selection.
- [ui] The “Open in Launchpad” option on asset run pages has been updated to link to the graph of assets or asset job instead of an unusable launchpad page.
- [ui] Partition status dots of multi-dimensional assets no longer wrap on the Asset > Partitions page.
- [asset checks] Fixed a bug that caused the `resource_defs` parameter of `@asset_check` to not be respected
- [ui] Fixed an issue where schedules or sensors with the same name in two different code locations sometimes showed each others runs in the list of runs for that schedule or sensor.
- [pipes] Fixed an issue with the `PipesFileMessageReader` that could cause a crash on Windows.
- Previously, calling `context.log` in different threads within a single op could result in some of those log messages being dropped. This has been fixed (thanks [@quantum-byte](https://github.com/quantum-byte)!)
- [dagster-dbt] On Dagster run termination, the dbt subprocess now exits gracefully to terminate any inflight queries that are materializing models.

### Breaking Changes

- The `file_manager` property on `OpExecutionContext` and `AssetExecutionContext` has been removed. This is an ancient property that was deprecated prior to Dagster 1.0, and since then had been raising a `NotImplementedError` whenever invoked.

### Community Contributions

- Added the Hashicorp Nomad integration to the documentation’s list of [community integrations](https://docs.dagster.io/integrations#community-supported-libraries). Thanks, [@ThomAub](https://github.com/ThomAub)!
- [dagster-deltalake] Fixed an error when passing non-string valued options and extended the supported data types by the arrow type handler to support pyarrow datasets which allows for lazily loading delta tables. Thanks [@roeap](https://github.com/roeap)!

### Experimental

- [dagster-pipes] The subprocess and databricks clients now forward termination to the external process if the orchestration process is terminated. A `forward_termination` argument is available for opting out.

### Documentation

- Fixed an error in the asset checks factory code example.

### Dagster Cloud

- The UI now correctly displays failed partitions after a single-run backfill occurs. Previously, if a single-run backfill failed, the corresponding partitions would not display as failed.
- Several performance improvements when submitting Snowflake metrics to Dagster Cloud Insights.
- Fixed an error which would occur when submitting Snowflake metrics for a removed or renamed asset to Dagster Cloud Insights.

# 1.5.13 / 0.21.13 (libraries)

### New

- The `SensorEvaluationContext` object has two new properties: `last_sensor_start_time` and `is_first_tick_since_sensor_start`. This enables sensor evaluation functions to vary behavior on the first tick vs subsequent ticks after the sensor has started.
- The `asset_selection` argument to `@sensor` and `SensorDefinition` now accepts sequence of `AssetsDefinitions`, a sequences of strings, or a sequence of `AssetKey`s, in addition to `AssetSelection`s.
- [dagster-dbt] Support for `dbt-core==1.3.*` has been removed.
- [ui] In code locations view, link to git repo when it’s a valid URL.
- [ui] To improve consistency and legibility, when displaying elapsed time, most places in the app will now no longer show milliseconds.
- [ui] Runs that were launched by schedules or sensors now show information about the relevant schedule or sensor in the header, with a link to view other runs associated with the same tick.
- [dagster-gcp] Added a `show_url_only` parameter to `GCSComputeLogManager` that allows you to configure the compute log manager so that it displays a link to the GCS console rather than loading the logs from GCS, which can be useful if giving Dagster access to GCS credentials is undesirable.

### Bugfixes

- Fixed behavior of loading partitioned parent assets when using the `BranchingIOManager`
- [ui] Fixed an unwanted scrollbar that sometimes appears on the code location list.

### Community Contributions

- Fixed a bug where dagster would error on FIPS-enabled systems by explicitly marking callsites of `hashlib.md5` as not used for security purposes (Thanks [@jlloyd-widen](https://github.com/jlloyd-widen)!)
- [dagster-k8s] Changed `execute_k8s_job` to be aware of run-termination and op failure by deleting the executing k8s job (Thanks [@Taadas](https://github.com/Taadas)!).
- [dagstermill] Fixed dagstermill integration with the Dagster web UI to allow locally-scoped static resources (required to show certain frontend-components like `plotly` graphs) when viewing dagstermill notebooks (Thanks [@aebrahim](https://github.com/aebrahim)!).
- [dagster-dbt] Fixed type annotation typo in the `DbtCliResource` API docs (Thanks [@akan72](https://github.com/akan72)!)

### Experimental

- [pipes] Methods have been added to facilitate passing non-Dagster data back from the external process (`report_custom_message` ) to the orchestration process (`get_custom_messages`).
- [ui] Added a “System settings” option for UI theming, which will use your OS preference to set light or dark mode.

### Documentation

- [graphql] - Removed experimental marker that was missed when the GraphQL client was fully released
- [assets] - Add an example for using retries with assets to the SDA concept page
- [general] - Fixed some typos and formatting issues

# 1.5.12 / 0.21.12 (libraries)

### Bugfixes

- [dagster-embedded-elt] Fixed an issue where `EnvVar`s used in Sling source and target configuration would not work properly in some circumstances.
- [dagster-insights] Reworked the Snowflake insights ingestion pipeline to improve performance and increase observability.

# 1.5.11 / 0.21.11 (libraries)

### New

- [ui] Asset graph now displays active filters.
- [ui] Asset graph can now be filtered by compute kind.
- [ui] When backfilling failed and missing partitions of assets, a “Preview” button allows you to see which ranges will be materialized.
- [dagster-dbt] When running `DAGSTER_DBT_PARSE_PROJECT_ON_LOAD=1 dagster dev` in a new scaffolded project from `dagster-dbt project scaffold`, dbt logs from creating dbt artifacts to loading the project are now silenced.
- [dagster-airbyte] Added a new `connection_meta_to_group_fn` argument which allows configuring loaded asset groups based on the connection’s metadata dict.
- [dagster-k8s] Debug information about failed run workers in errors surfaced by run monitoring now includes logs from sidecar containers, not just the main dagster container.

### Bugfixes

- The `QueuedRunCoordinatorDaemon` has been refactored to paginate over runs when applying priority sort and tag concurrency limits. Previously, it loaded all runs into memory causing large memory spikes when many runs were enqueued.
- Callable objects can once again be used to back sensor definitions.
- `UPathIOManager` has been updated to use the correct path delimiter when interacting with cloud storages from a Windows process.
- In the default multiprocess executor, the `STEP_WORKER_STARTED` event now fires before importing code in line with the other executors.
- During execution, skipping a step now takes precedence over “abandoning” it due to upstream failure. This is expected to substantially improve the “retry from failure” workflow when conditional branching is in use.
- Fixed an issue where default config values set to `EnvVar` did not work properly.
- Fixed an issue where resources which implemented `IAttachDifferentObjectToOpContext` would pass the incorrect object to schedules and sensors.
- Fixed a bug that caused auto-materialize failures when using the `materialize_on_cron` rule with dynamically partitioned assets.
- Fixed an issue where sensor ticks would sporadically fail with a StopIteration exception.
- [ui] For a job launchpad with a large number of tabs, the “Remove all” option was pushed offscreen. This has been fixed.
- [ui] The asset backfill page now correctly shows backfills that target only unpartitioned assets.
- [ui] Launching an asset job that was defined `without_checks` no longer fails by attempting to include the checks.
- [dagster-databricks] fix bug that caused crash when polling a submitted job that is still in the Databricks queue (due to concurrency limit).

### Community Contributions

- Patched issue where the local compute log path exposed file content outside of the compute log base directory - thanks **[r1b](https://github.com/r1b)!**
- [dagster-databricks] Added ability to authenticate using an Azure service principal and fix minor bugs involving authenticating with a service principal while `DATABRICKS_HOST` is set. Thanks [@zyd14](https://github.com/zyd14)!

### Experimental

- [ui] Dark mode is now available via the User Settings dialog, currently in an experimental state. By default, the app will use a “legacy” theme, closely matching our current colors. A new light mode theme is also available.
- [ui] Asset graph group nodes can be collapsed/expanded by right clicking on the collapsed group node or the header of the expanded group node.
- [ui] Asset graph group nodes can be all collapsed or all expanded by right clicking anywhere on the graph and selecting the appropriate action.
- [ui] The tree view was removed from the asset graph.
- [pipes] `PipesLambdaClient`, an AWS Lambda pipes client has been added to `dagster_aws`.
- Fixed a performance regression introduced in the 1.5.10 release where auto-materializing multi-assets became slower.

### Documentation

- [getting-started] Added an [overview to the Getting Started section](https://docs.dagster.io/getting-started/overview) that explains the whats and whys of Dagster.
- [pipes] Added [a guide](https://docs.dagster.io/guides/dagster-pipes/aws-lambda) for using the new `PipesLambdaClient` with Dagster Pipes.
- [getting-started] Simplified the **Getting Started** category. The following pages have been moved:
  - [Understanding Dagster project files](https://docs.dagster.io/guides/understanding-dagster-project-files) is now in **Guides**
  - [Telemetry](https://docs.dagster.io/about/telemetry) is now in **About**
- [guides] Fixed a broken link in the [Airflow-to-Dagster concept mapping guide](https://docs.dagster.io/integrations/airflow).
- [deployment] Cleaned up and updated the [Executing with Celery OSS deployment guide](https://docs.dagster.io/deployment/guides/celery).
- [general] Added two guides that were previously missing to the side navigation:
  - [Utilizing SCIM provisioning](https://docs.dagster.io/dagster-cloud/account/authentication/utilizing-scim-provisioning) (**Deployment > Cloud > Authentication & users > SCIM provisioning**)
  - [Pandera](https://docs.dagster.io/integrations/pandera) (**Integrations > Pandera**)

### Dagster Cloud

- When a Dagster Cloud agent starts up, it will now wait to display as Running on the Agents tab in the Dagster Cloud UI until it has launched all the code servers that it needs in order to serve requests.

# 1.5.10 / 0.21.10 (libraries)

### New

- Added a new `MetadataValue.job` metadata type, which can be used to link to a Dagster job from other objects in the UI.
- [asset backfills] Previously, when partitions definitions were changed after backfill launch, the asset backfill page would be blank. Now, when partitions definitions are changed, the backfill page will display statuses by asset.
- [dagster-bigquery, dagster-duckdb, dagster-snowflake]. The BigQuery, DuckDB, and Snowflake I/O Managers will now determine the schema (dataset for BigQuery) in the following order of precedence: `schema` metadata set on the `asset` or `op`, I/O manager `schema`/ `dataset` configuration, `key_prefix` set on the `asset`. Previously, all methods for setting the schema/dataset were mutually exclusive, and setting more than one would raise an exception.
- [dagster-shell] Added option to exclude the shell command from logs.
- [dagster-dbt] When running `DAGSTER_DBT_PARSE_PROJECT_ON_LOAD=1 dagster dev` in a new scaffolded project from `dagster-dbt project scaffold`, dbt artifacts for loading the project are now created in a static `target/` directory.

### Bugfixes

- Problematic inheritance that was causing pydantic warnings to be emitted has been corrected.
- It's now possible to use the logger of `ScheduleEvaluationContext` when testing via `build_schedule_context`.
- The `metadata` from a `Failure` exception is now hoisted up to the failure that culminates when retry limits are exceeded.
- Fixed bug in which the second instance of an hour partition at a DST boundary would never be shown as “materialized” in certain UI views.
- Fixed an issue where backfilling an hourly partition that occurred during a fall Daylight Savings Time transition sometimes raised an error.
- [auto-materialize] Fix issue where assets which were skipped because required parent partitions did not exist would not be materialized once those partitions came into existence.
- [dagster ecs] The exit code of failed containers is now included in the failure message.
- [dagster pipes] The `PipesK8sClient` now correctly raises on failed containers.
- [dagster pipes] Using pipes within ops instead of assets no longer enforces problematic constraints.
- [helm] Added `maxCatchupRuns` and `maxTickRetries` configuration options for the scheduler in the Helm chart.
- [embedded-elt] Fixed crashes for non-unicode logs.
- [UI] Fixed an issue where the test sensor dialog for a sensor that targeted multiple jobs would claim that all of the runs were targeting the same job.
- [UI] Asset keys, job names, and other strings in Dagster UI no longer truncate unnecessarily in Firefox in some scenarios
- [UI] A larger “View prior events” button on the Asset > Partitions page makes it easier to see the historical materializations of a specific partition of an asset.
- [asset-checks, dbt] Fixed a bug that that caused asset checks to not execute when a run was not a subset. As part of the fix, the default dbt selection selection string will not be used for dbt runs, even when not in a subset. Instead we pass the explicit set of models and tests to execute, with `DBT_INDIRECT_SELECTION=empty`.
- [asset-checks] Fixed a bug that caused asset checks defined with `@asset(check_specs=...` to not cooperate with the `key_prefix` argument of the `load_assets_from_modules` method and it’s compatriots.
- [asset-checks] Fixed a bug that caused errors when launching a job from the UI that excluded asset checks.
- [asset-checks] Fixed a bug that caused UI errors when a check run was deleted.

### Deprecations

- Marked the experimental Airbyte ingestion-as-code feature as deprecated, to be removed in a future release. We suggest users interested in managing their Airbyte connections in code use the [Airbyte terraform provider](https://reference.airbyte.com/reference/using-the-terraform-provider).

### Community Contributions

- `define_asset_job` now accepts an `op_retry_policy` argument, which specifies a default retry policies for all of the ops in the job. (thanks Eugenio Contreras!)
- Fix IOManager not being able to load assets with MultiPartitionsDefinition - thanks [@cyberosa](https://github.com/cyberosa)!
- [dagster-essentials] Three typo fixes in Lesson 8 - thanks Colton [@cmpadden](https://github.com/cmpadden)!

### Experimental

- The `observable_source_asset` decorator now accepts a `key` argument.
- [dagster pipes] an `implicit_materializations` argument has been added to `get_results` and `get_materialize_result` to control whether an implicit materialization event is created or not.
- [embedded-elt] Added a new builder and `SlingConnectionResource` to allow reusing sources and targets interoperably.
- [UI] Updated the experimental concurrency limits configuration page to show per-op runtime info and control.
- [UI] The Auto-materialize history tab for each asset now only includes rows for evaluations where the result of evaluating the policy has changed. Previously, it would also show a row in the table representing periods of time where nothing changed.
- [asset-checks, dbt] `build_dbt_asset_selection` now also selects asset checks based on their underlying dbt tests. E.g. `build_dbt_asset_selection([my_dbt_assets], dbt_select="tag:data_quality")` will select the assets and checks for any models and tests tagged with ‘data_quality’.

### Documentation

- Added information about `EnvVar` vs. `os.getenv` to the [Environment variables documentation](https://docs.dagster.io/guides/dagster/using-environment-variables-and-secrets).
- Updates to the [Asset selection syntax reference](https://docs.dagster.io/concepts/assets/asset-selection-syntax), including expanded examples for Python, the CLI, and the Dagster UI.
- Added Experimental tags to all Dagster Cloud Insights docs.
- Updated the [Helm - Migrating a Dagster instance while upgrading guide](https://docs.dagster.io/deployment/guides/kubernetes/how-to-migrate-your-instance) to include a prerequisites section.

### Dagster Cloud

- Branch deployments now use the same timeouts for starting and canceling runs that are set for their parent full deployment, instead of a fixed value of 10 minutes.
- [k8s agent] Setting labels on a code location will now apply those labels to the kubernetes deployment and service for that code location, rather than just applying them to the pod for that code location.

# 1.5.9 / 0.21.9 (libraries)

### New

- [ui] Enabled collapsing asset groups in the global asset view when the new experimental asset graph is turned on in User Settings
- [ui] The experimental asset graph sidebar now supports keyboard navigation via arrow keys
- [ui] You can now right click nodes in the asset graph to materialize them or filter the graph
- [ui] Jobs can now be searched by run ID
- [ui] You can now launch runs from the job actions menu
- [auto-materialize] A new `AutoMaterializeRule.materialize_on_cron()` rule makes it possible to create policies which materialize assets on a regular cadence.
- [auto-materialize] If a partition-mapping-related error occurs within the Asset Daemon, a more informative error message will be provided.
- [dagster-databricks] Extended the set of available config options to the Databricks step launcher - thanks [@zyd14](https://github.com/zyd14)!

### Bugfixes

- Fixed an issue where some schedules incorrectly skipped ticks during Daylight Savings Times transitions.
- Returning a `SensorResult` from a sensor no longer overwrites a cursor if it was set via the context.
- Fixed issue which could cause incorrect execution order when executing multi-assets with `can_subset=True` alongside assets which were upstream of some assets in the multi-asset, and downstream of others.
- Previously, when creating an `HourlyPartitionsDefinition` with a non-UTC timezone and the default format string (or any format string not including a UTC-offset), there was no way to disambiguate between the first and second instance of the repeated hour during a daylight saving time transition. Now, for the one hour per year in which this ambiguity exists, the partition key of the second instance of the hour will have the UTC offset automatically appended to it.
- [asset checks] Fixed a bug that caused an error when passing `check_specs` to `AssetsDefinition.from_graph`
- [dagster-dbt] Fixed a bug in `dagster-dbt` that caused some dbt tests to not be selected as asset checks.
- [dagster-dbt] Fixed an issue where multiple copies of the dbt manifest were held in memory when loading a dbt project as software-defined assets.
- The `email_on_failure` sensor called deprecated methods on the context. This has been fixed

### Community Contributions

- [dagster-deltalake] Added Delta Lake support along with support for pandas and polars. Thanks Robert Pack [@roeap](https://github.com/roeap)!
- [dagster-graphql] Fixed the asset cursor format to use a normalized format - thanks [@sisidra](https://github.com/sisidra)!
- [dagster-databricks] Extended the set of available config options to the Databricks step launcher - thanks [@zyd14](https://github.com/zyd14)!

### Experimental

- `DagsterInstance.report_runless_asset_event` is now public.
- `AutoMaterializeRule.materialize_on_parent_updated` now accepts an `updated_parents_filter` of type `AutoMaterializeAssetPartitionsFilter`, which allows only materializing based on updates from runs with a required set of tags.

### Documentation

- Added a new guide for using [Dagster Pipes with Kubernetes](https://docs.dagster.io/guides/dagster-pipes)
- Added all [OSS deployment guides](https://docs.dagster.io/deployment/guides) to the site’s side navigation (**Deployment > Open Source > Guides**)
- Updated formatting in the [Migrating your Dagster instance while upgrading Helm guide](https://docs.dagster.io/deployment/guides/kubernetes/how-to-migrate-your-instance)
- Added **Experimental** tags to [Dagster Cloud Insights docs](https://docs.dagster.io/dagster-cloud/insights)
- The [Transitioning Data Pipelines from Development to Production](https://docs.dagster.io/guides/dagster/transitioning-data-pipelines-from-development-to-production) and [Testing against production with Dagster Cloud Branch Deployments](https://docs.dagster.io/guides/dagster/branch_deployments) guides have been updated to use Pythonic Resources

### Dagster Cloud

- Reporting runless events and manually marking an asset as successfully materialized are no possible with “Launcher” level permissions
- [ui] Improved search and render performance of Users page, especially for large lists of users.
- [billing] Fixed issues with correctly displaying your tax ID

# 1.5.8 / 0.21.8 (libraries)

### Bugfixes

- Fixed an error when trying to directly invoke a run status sensor when passing resources.
- [dagster-airbyte][dagster-fivetran] Fixed an issue where `EnvVars` used in Airbyte or Fivetran resources would show up as their processed values in the launchpad when loading assets from a live Fivetran or Airbyte instance.

### Dagster Cloud

- Substantially improved performance of the Dagster insights DBT/Snowflake usage job.

# 1.5.7 / 0.21.7 (libraries)

### New

- The `OpExecutionContext` and `AssetExecutionContext` now have a `partition_keys` property
- [dagster-ui] The asset graph layout algorithm has been changed to a much faster one called “tight-tree”
- [dagster-ui] The Runs table filters has a top level filter for partitions
- [dagster-dbt] `dbt-core==1.7.*` is now supported.

### Bugfixes

- Fixed an issue where some schedules skipped a tick on the day after a fall Daylight Savings Time transition.
- Fixed a bug that caused backfill policies that execute multiple partitions in a single run not to work with dynamic partitions.
- Fixed a bug that caused an error when `build_schedule_from_partitioned_job` was used with a job with multi-partitioned assets and the `partitions_def` argument wasn’t provided to `define_asset_job`.
- We now raise an error early if the empty string is provided as an asset’s group name (Thanks Sierrra!)
- Fixed an issue where custom setup and teardown methods were not properly called on nested Pythonic resources.
- Added a warning message when op or asset config is passed as an argument not named `config`.
- [dagster-cloud] Fixed an issue where overriding the default I/O manager could break the Snowflake-dbt insights job.
- [auto-materialize] Fixed an issue where materializing an unpartitioned parent of a dynamic-partitioned asset would only result in the latest dynamic partition of that asset being requested. Now, all partitions will be requested.
- [dagster-embedded-elt] Fixed an issue in `dagster-embedded-elt` where sling’s `updated_at` parameter was set to the incorrect type
- [dagster-ui] Fixed an issue in the launchpad where selecting a partition wouldn’t correctly overwrite fields using the partition’s specific configuration

### Community Contributions

- A docs fix to the testing concepts page, thanks @NicolaiLolansen!
- The schema can now be overridden per asset in DB IO managers, thanks @jrstats!

### Experimental

- Improved failure recovery and retry behavior when the daemon that launches auto-materialization runs fails or crashes in the middle of a tick.
- [asset-checks] UI performance for displaying check results is improved
- [asset-checks] Removed noisy experimental warning about `AssetCheckKey`
- [op-concurrency] Fixed a bug where concurrency slots were not getting assigned if a run that was assigned a slot was deleted before the slot had actually been claimed during execution.
- [dagster-pipes] The `PipesSubprocessClient` now inherits the environment variables of the parent process in the launched subprocess.
- [dagster-pipes] Exceptions are now reported in the event log for framework components and from the external process.

### Documentation

- Added a guide for using [Dagster Pipes with Databricks](https://docs.dagster.io/guides/dagster-pipes/databricks)

# 1.5.6 / 0.21.6 (libraries)

### New

- [dagster-k8s] The `PipesK8sClient` will now attempt to load the appropriate kubernetes config, and exposes arguments for controlling this process.
- [ui] The launch asset backfill modal now offers a preview dialog showing the targeted asset partitions and their backfill policies when partition mapping or varying backfill policies are present.
- [asset-checks] New `load_asset_checks_from_modules` functions for loading asset checks in tandem with `load_assets_from_modules`.
- Previously, the daemon process would terminate with an error if it believed that a thread might be hanging, which sometimes caused undesirable terminations when doing large backfills or auto-materializing many assets. Now, the daemon process will emit a warning instead of terminate.
- [dagster-dbt] `dagster-dbt project scaffold` now uses `~/.dbt/profiles.yml` if a `profiles.yml` is not present in the dbt project directory.
- [dagster-dbt] `@dbt_assets` now support `PartitionMapping` using `DagsterDbtTranslator.get_partition_mapping`.
- [dagster-dbt] Self dependencies can now be enabled for dbt models that are represented by `@dbt_assets`. To enable this, add the following metadata to your dbt model’s metadata in your dbt project:

```
meta:
  dagster:
    has_self_dependency: True
```

### Bugfixes

- Fixed an issue where Dagster imports would throw errors when using `pydantic<2.0.0` but having `pydantic-core` installed.
- Previously, asset backfills that targeted partitioned assets with a `LastPartitionMapping` dependency would raise an error. This has been fixed.
- Fixed a multipartitions partition mapping bug where a `instance is not available to load partitions` error was raised.
- [asset-checks] Fixed an issue with conflicting op names when using `build_asset_with_blocking_check`
- [ui] Viewing run logs containing very large messages no longer causes the UI to crash in Safari on macOS
- [ui] Drilling into the graph of a graph-backed asset with 4+ inputs or outputs no longer causes the asset graph to crash with a rendering error.
- [ui] On the backfill details page, clicking to a specific asset correctly shows the partitions that were materialized for that asset when partition mapping is in use.
- [ui] The Asset > Partition page now loads partition details more quickly in cases where calculating the staleness of the partition took a significant amount of time.
- Fixed a bug introduced in `1.5.0` where instances that haven’t been migrated to the latest schema hit an error upon run deletion.
- [auto-materialize] Previously, if an asset partition was skipped on a tick for one reason, and then processed and skipped on a later tick for an additional reason, only the most recent skip reason would be tracked. Now, all skip reasons are tracked.
- [dagster-dbt] Fixed an issue where if an `exclude` that didn’t match any dbt nodes was used in `@dbt_assets`, an error would be raised. The error is now properly handled.
- [dagster-dbt] When invoking `DbtCliResource.cli(...)` in an `op`, `AssetMaterialization`'s instead of `Output` are now emitted.

### Experimental

- Global op concurrency slots are now released in between retries of op execution failures.

### Documentation

- Updated the tutorial to reflect best practices and APIs as of Dagster 1.5

### Dagster Cloud

- The `report_asset_observation` REST endpoint for reporting runless events is now available.

# 1.5.5 / 0.21.5 (libraries)

### New

- Dagster now supports using Pydantic 2 models for Config and Resources. Pydantic 1.10 continues to be supported.
- Added a `report_asset_observation` REST API endpoint for runless external asset observation events
- Dramatically improved the performance of partition-mapping, for basic hourly and daily partitions definitions
- [ui] When viewing a list of runs, you can quickly add the tag in the “Launched by” column as a filter on the list view. Hover over the tag to see the “Add to filter” button.
- [helm] The env vars `DAGSTER_K8S_PG_PASSWORD_SECRET` and `DAGSTER_K8S_INSTANCE_CONFIG_MAP` will no longer be set in all pods.
- [dagster-pyspark] `build_pyspark_zip` now takes an `exclude` parameter that can be used to customize the set of excluded files.
- [ui] Links beginning with http://, https:// in unstructured run logs (via context.log) are automatically converted to clickable links

### Bugfixes

- Fixed an asset backfill bug where certain asset partitions with no targeted parents would hang indefinitely.
- Fixed a bug where the `source_key_prefix` argument to `load_assets_from_current_module` and `load_assets_from_package_name` was ignored
- Fixed two bugs in `dagster_embedded_elt` where the mode parameter was not being passed to Sling, and only one asset could be created at a time
- Fixed a bug with handing default values for Pydantic validators on Windows
- [ui] Clicking an asset with checks shows them in the asset graph sidebar, even if live data on the page is still loading.
- [ui] Reported materialization events are presented more clearly in the asset graph sidebar and in other parts of the Dagster UI.

### Deprecations

- [helm] The `pipelineRun` configuration in the Helm chart is now deprecated. The same config can be set under `dagster-user-deployments`

### Community Contributions

- Added `setup_for_execution` and `teardown_after_execution` calls to the inner IOManagers of the `BranchingIOManager` - thank you @danielgafni!
- The `S3FakeResource.upload_fileobj()` signature is now consistent with `boto3 S3.Client.upload_fileobj()` - thank you @jeanineharb!
- `dbt_assets` now have an optional name parameter - thank you @AlexanderVR!

### Documentation

- Added a link to Dagster University to the [docs landing page](https://docs.dagster.io) 🎓
- Improved readability of [API docs landing page](https://docs.dagster.io/_apidocs)
- Removed straggling mention of Dagit from the [Kubernetes OSS deployment guide](https://docs.dagster.io/deployment/guides/kubernetes/deploying-with-helm)

# 1.5.4 / 0.21.4 (libraries)

### New

- Added a `report_asset_check` REST API endpoint for runless external asset check evaluation events. This is available in cloud as well.
- The `config` argument is now supported on `@graph_multi_asset`
- [ui] Improved performance for global search UI, especially for deployments with very large numbers of jobs or assets.
- [dagster-pipes] Add S3 context injector/reader.
- [dagster-dbt] When an exception when running a dbt command, error messages from the underlying dbt invocation are now properly surfaced to the Dagster exception.
- [dagster-dbt] The path to the dbt executable is now configurable in `DbtCliResource`.

### Bugfixes

- Fixed a bug introduced in 1.5.3 that caused errors when launching specific Ops in a Job.
- Fixed a bug introduced in 1.5.0 that prevented the `AssetExecutionContext` type annotation for the `context` parameter in `@asset_check` functions.
- Fixed an issue where the Dagster scheduler would sometimes fail to retry a tick if there was an error reloading a code location in the middle of the tick.
- [dagster-dbt] Fixed an issue where explicitly passing in `profiles_dir=None` into `DbtCliResource` would cause incorrect validation.
- [dagster-dbt] Fixed an issue where partial parsing was not working when reusing existing target paths in subsequent dbt invocations.
- [ui] Fixed an issue where the job partitions UI would show “0 total partitions” if the job consisted of more than 100 assets

### Community Contributions

- [dagster-duckdb] The `DuckDBResource` and `DuckDBIOManager` accept a `connection_config` configuration that will be passed as `config` to the DuckDB connection. Thanks @xjhc!

### Experimental

- Added events in the run log when a step is blocked by a global op concurrency limit.
- Added a backoff for steps querying for open concurrency slots.
- Auto-materialize logic to skip materializing when (1) a backfill is in progress or (2) parent partitions are required but nonexistent are now refactored to be skip rules.
- [ui] Added 2 new asset graph layout algorithms under user settings that are significantly faster for large graphs (1000+ assets).

### Documentation

- Added several pieces of documentation for Dagster Pipes, including:
  - [A high-level explanation of Pipes](https://docs.dagster.io/guides/dagster-pipes)
  - [A tutorial](https://docs.dagster.io/guides/dagster-pipes/subprocess) that demonstrates how to use Pipes with a local subprocess
  - [A reference](https://docs.dagster.io/guides/dagster-pipes/subprocess/reference) for using a local subprocess with Pipes
  - [A detailed explanation of Pipes](https://docs.dagster.io/guides/dagster-pipes/dagster-pipes-details-and-customization), including how to customize the process
  - API references for [Pipes](https://docs.dagster.io/_apidocs/pipes) (orchestration-side) and [dagster-pipes](https://docs.dagster.io/_apidocs/libraries/dagster-pipes) (external process)
- Added documentation for the new [experimental External Assets](https://docs.dagster.io/concepts/assets/external-assets) feature

### Dagster Cloud

- Running multiple agents is no longer considered experimental.
- When the agent spins up a new code server while updating a code location, it will now wait until the new code location uploads any changes to Dagster Cloud before allowing the new server to serve requests.

# 1.5.3 / 0.21.3 (libraries)

### New

- Alert policies can now be set on assets + asset checks (currently experimental). Check out the alerting [docs](https://docs.dagster.io/dagster-cloud/managing-deployments/setting-up-alerts#setting-up-alerts-in-dagster-cloud) for more information.
- Added a new flag `--live-data-poll-rate` that allows configuring how often the UI polls for new asset data when viewing the asset graph, asset catalog, or overview assets page. It defaults to 2000 ms.
- Added back the ability to materialize changed and missing assets from the global asset-graph. A dialog will open allowing you to preview and select which assets to materialize.
- Added an experimental AMP Timeline page to give more visibility into the automaterialization daemon. You can enable it under user settings
- Added a `report_asset_materialization` REST API endpoint for creating external asset materialization events. This is available in cloud as well.
- [dbt] The `@dbt_assets` decorator now accepts a `backfill_policy` argument, for controlling how the assets are backfilled.
- [dbt] The `@dbt_assets` decorator now accepts a `op_tags` argument, for passing tags to the op underlying the produced `AssetsDefinition`.
- [pipes] Added `get_materialize_result` & `get_asset_check_result` to `PipesClientCompletedInvocation`
- [dagster-datahub] The `acryl-datahub` pin in the `dagster-datahub` package has been removed.
- [dagster-databricks] The `PipesDatabricksClient` now performs stdout/stderr forwarding from the Databricks master node to Dagster.
- [dagster-dbt] The hostname of the dbt API can now be configured when executing the `dagster-dbt-cloud` CLI.
- [dagster-k8s] Added the ability to customize how raw k8s config tags set on an individual Dagster job are merged with raw k8s config set on the `K8sRunLauncher`. See [the docs](https://docs.dagster.io/deployment/guides/kubernetes/customizing-your-deployment#precedence-rules) for more information.

### Bugfixes

- Previously, the asset backfill page would display negative counts if failed partitions were manually re-executed. This has been fixed.
- Fixed an issue where the run list dialog for viewing the runs occupying global op concurrency slots did not expand to fit the content size.
- Fixed an issue where selecting a partition would clear the launchpad and typing in the launchpad would clear the partition selection
- Fixed various issues with the asset-graph displaying the wrong graph
- The IO manager’s `handle_output` method is no longer invoked when observing an observable source asset.

- [ui] Fixed an issue where the run config dialog could not be scrolled.
- [pipes] Fixed an issue in the `PipesDockerClient` with parsing logs fetched via the docker client.
- [external assets] Fixed an issue in `external_assets_from_specs` where providing multiple specs would error
- [external assets] Correct copy in tooltip to explain why Materialize button is disabled on an external asset.

### Breaking Changes

- [pipes] A change has been made to the environment variables used to detect if the external process has been launched with pipes. Update the `dagster-pipes` version used in the external process.
- [pipes] The top level function `is_dagster_pipes_process` has been removed from the `dagster-pipes` package.

### Community Contributions

- Override a method in the azure data lake IO manager (thanks @[0xfabioo](https://github.com/0xfabioo))!
- Add support of external launch types in ECS run launcher (thanks @[cuttius](https://github.com/cuttius))!

### Experimental

- The Python GraphQL client is considered stable and is no longer marked as experimental.

# 1.5.2 / 0.21.2 (libraries)

### Bugfixes

- Previously, asset backfills targeting assets with multi-run backfill policies would raise a "did not submit all run requests" error. This has been fixed.

### Dagster Cloud

- The experimental dagster-insights package has receieved some API surface area updates and bugfixes.

# 1.5.1 / 0.21.1 (libraries)

### New

- Dagster now automatically infers a dependency relationship between a time-partitioned asset and a multi-partitioned asset with a time dimension. Previously, this was only inferred when the time dimension was the same in each asset.
- The `EnvVar` utility will now raise an exception if it is used outside of the context of a Dagster resource or config class. The `get_value()` utility will retrieve the value outside of this context.
- [ui] The runs page now displays a “terminate all” button at the top, to bulk terminate in-progress runs.
- [ui] Asset Graph - Various performance improvements that make navigating large asset graphs smooth
- [ui] Asset Graph - The graph now only fetches data for assets within the viewport solving timeout issues with large asset graphs
- [ui] Asset Graph Sidebar - The sidebar now shows asset status
- [dagster-dbt] When executing dbt invocations using `DbtCliResource`, an explicit `target_path` can now be specified.
- [dagster-dbt] Asset checks can now be enabled by using `DagsterDbtTranslator` and `DagsterDbtTranslatorSettings`: see [the docs](https://docs.dagster.io/integrations/dbt/reference) for more information.
- [dagster-embedded-elt] Dagster library for embedded ELT

### Bugfixes

- [ui] Fixed various issues on the asset details page where partition names would overflow outside their containers
- [ui] Backfill notification - Fixed an issue where the backfill link didn’t take the —path-prefix option into account
- [ui] Fixed an issue where the instance configuration yaml would persist rendering even after navigating away from the page.
- [ui] Fixed issues where config yaml displays could not be scrolled.
- [dagster-webserver] Fixed a performance issue that caused the UI to load slowly

### Deprecations

- [dagster-dbt] Enabling asset checks using dbt project metadata has been deprecated.

# 1.5.0 (core) / 0.21.0 (libraries) "How Will I Know"

## **Major Changes since 1.4.0 (core) / 0.20.0 (libraries)**

### Core

- **Improved ergonomics for execution dependencies in assets**  - We introduced a set of APIs to simplify working with Dagster that don't use the I/O manager system for handling data between assets. I/O manager workflows will not be affected.
  - `AssetDep` type allows you to specify upstream dependencies with partition mappings when using the `deps` parameter of `@asset` and `AssetSpec`.
  - `MaterializeResult` can be optionally returned from an asset to report metadata about the asset when the asset handles any storage requirements within the function body and does not use an I/O manager.
  - `AssetSpec` has been added as a new way to declare the assets produced by `@multi_asset`. When using `AssetSpec`, the multi_asset does not need to return any values to be stored by the I/O manager. Instead, the multi_asset should handle any storage requirements in the body of the function.
- **Asset checks (experimental)** - You can now define, execute, and monitor data quality checks in Dagster [[docs](https://docs.dagster.io/concepts/assets/asset-checks)].

  - The `@asset_check` decorator, as well as the `check_specs` argument to `@asset` and `@multi_asset` enable defining asset checks.
  - Materializing assets from the UI will default to executing their asset checks. You can also execute individual checks.
  - When viewing an asset in the asset graph or the asset details page, you can see whether its checks have passed, failed, or haven’t run successfully.

- **Auto materialize customization (experimental)** - `AutoMaterializePolicies` can now be customized [[docs](https://docs.dagster.io/concepts/assets/asset-auto-execution#auto-materialize-policies)].
  - All policies are composed of a set of `AutoMaterializeRule`s which determine if an asset should be materialized or skipped.
  - To modify the default behavior, rules can be added to or removed from a policy to change the conditions under which assets will be materialized.

### dagster-pipes

- Dagster pipes is a new library that implements a protocol for launching compute into external execution environments and consuming streaming logs and Dagster metadata from those environments. See https://github.com/dagster-io/dagster/discussions/16319 for more details on the motivation and vision behind Pipes.
- Out-the-box integrations
  - Clients: local subprocess, Docker containers, Kubernetes, and Databricks
    - `PipesSubprocessClient`, `PipesDocketClient`, `PipesK8sClient`, `PipesDatabricksClient`
  - Transport: Unix pipes, Filesystem, s3, dbfs
  - Languages: Python
- Dagster pipes is composable with existing launching infrastructure via `open_pipes_session`. One can augment existing invocations rather than replacing them wholesale.

## **Since 1.4.17 (core) / 0.20.17 (libraries)**

### New

- [ui] Global Asset Graph performance improvement - the first time you load the graph it will be cached to disk and any subsequent load of the graph should load instantly.

### Bugfixes

- Fixed a bug where deleted runs could retain instance-wide op concurrency slots.

### Breaking Changes

- `AssetExecutionContext` is now a subclass of `OpExecutionContext`, not a type alias. The code

```python
def my_helper_function(context: AssetExecutionContext):
    ...

@op
def my_op(context: OpExecutionContext):
    my_helper_function(context)
```

will cause type checking errors. To migrate, update type hints to respect the new subclassing.

- `AssetExecutionContext` cannot be used as the type annotation for `@op`s run in `@jobs`. To migrate, update the type hint in `@op` to `OpExecutionContext`. `@op`s that are used in `@graph_assets` may still use the `AssetExecutionContext` type hint.

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

- [ui] We have removed the option to launch an asset backfill as a single run. To achieve this behavior, add `backfill_policy=BackfillPolicy.single_run()` to your assets.

### Community Contributions

- `has_dynamic_partition` implementation has been optimized. Thanks @edvardlindelof!
- [dagster-airbyte] Added an optional `stream_to_asset_map` argument to `build_airbyte_assets` to support the Airbyte prefix setting with special characters. Thanks @chollinger93!
- [dagster-k8s] Moved “labels” to a lower precedence. Thanks @jrouly!
- [dagster-k8s] Improved handling of failed jobs. Thanks @Milias!
- [dagster-databricks] Fixed an issue where `DatabricksPysparkStepLauncher` fails to get logs when `job_run` doesn’t have `cluster_id` at root level. Thanks @PadenZach!
- Docs type fix from @sethusabarish, thank you!

### Documentation

- Our Partitions documentation has gotten a facelift! We’ve split the original page into several smaller pages, as follows:
  - [Partitions](https://docs.dagster.io/concepts/partitions-schedules-sensors/partitions) - An overview of what a partition is, benefits, and how to use it
  - [Partitioning assets](https://docs.dagster.io/concepts/partitions-schedules-sensors/partitioning-assets) - Details about partitioning assets
  - [Partitioning ops](https://docs.dagster.io/concepts/partitions-schedules-sensors/partitioning-ops) - Details about partitioning ops
  - [Testing partitions](https://docs.dagster.io/concepts/partitions-schedules-sensors/testing-partitions) - As described

### Dagster Cloud

- **New dagster-insights sub-module** - We have released an experimental `dagster_cloud.dagster_insights` module that contains utilities for capturing and submitting external metrics about data operations to Dagster Cloud via an api. Dagster Cloud Insights is a soon-to-be released feature that shows improves visibility into usage and cost metrics such as run duration and Snowflake credits in the Cloud UI.

# 1.4.17 / 0.20.17 (libraries)

### New

- [dagster-dbt] `DbtCliResource` now enforces that the current installed version of `dbt-core` is at least version `1.4.0`.
- [dagster-dbt] `DbtCliResource` now properly respects `DBT_TARGET_PATH` if it is set by the user. Artifacts from dbt invocations using `DbtCliResource` will now be placed in unique subdirectories of `DBT_TARGET_PATH`.

### Bugfixes

- When executing a backfill that targets a range of time partitions in a single run, the `partition_time_window` attribute on `OpExecutionContext` and `AssetExecutionContext` now returns the time range, instead of raising an error.
- Fixed an issue where the asset backfill page raised a GraphQL error for backfills that targeted different partitions per-asset.
- Fixed `job_name` property on the result object of `build_hook_context`.

### Experimental

- `AssetSpec` has been added as a new way to declare the assets produced by `@multi_asset`.
- `AssetDep` type allows you to specify upstream dependencies with partition mappings when using the `deps` parameter of `@asset` and `AssetSpec`.
- [dagster-ext] `report_asset_check` method added to `ExtContext`.
- [dagster-ext] ext clients now must use `yield from` to forward reported materializations and asset check results to Dagster. Results reported from ext that are not yielded will raise an error.

### Documentation

- The [Dagster UI](https://docs.dagster.io/concepts/webserver/ui) documentation got an overhaul! We’ve updated all our screenshots and added a number of previously undocumented pages/features, including:
  - The Overview page, aka the Factory Floor
  - Job run compute logs
  - Global asset lineage
  - Overview > Resources
- The [Resources](https://docs.dagster.io/concepts/resources) documentation has been updated to include additional context about using resources, as well as when to use `os.getenv()` versus Dagster’s `EnvVar`.
- Information about custom loggers has been moved from the Loggers documentation to its own page, [Custom loggers](https://docs.dagster.io/concepts/logging/custom-loggers).

# 1.4.16 / 0.20.16 (libraries)

### New

- [ui] When using the search input within Overview pages, if the viewer’s code locations have not yet fully loaded into the app, a loading spinner will now appear to indicate that search results are pending.

### Bugfixes

- Fixed an asset backfill bug that caused occasionally caused duplicate runs to be kicked off in response to manual runs upstream.
- Fixed an issue where launching a run from the Launchpad that included many assets would sometimes raise an exception when trying to create the tags for the run.
- [ui] Fixed a bug where clicking to view a job from a run could lead to an empty page in situations where the viewer’s code locations had not yet loaded in the app.

### Deprecations

- Deprecated `ExpectationResult`. This will be made irrelevant by upcoming data quality features.

### Community Contributions

- Enabled chunked backfill runs to target more than one asset, thanks @ruizh22!

### Experimental

- Users can now emit arbitrary asset materializations, observations, and asset check evaluations from sensors via `SensorResult`.

# 1.4.15 / 0.20.15 (libraries)

### New

- The `deps` parameter for `@asset` and `@multi_asset` now supports directly passing `@multi_asset` definitions. If an `@multi_asset` is passed to `deps`, dependencies will be created on every asset produced by the `@multi_asset`.
- Added an optional data migration to convert storage ids to use 64-bit integers instead of 32-bit integers. This will incur some downtime, but may be required for instances that are handling a large number of events. This migration can be invoked using `dagster instance migrate --bigint-migration`.
- [ui] Dagster now allows you to run asset checks individually.
- [ui] The run list and run details page now show the asset checks targeted by each run.
- [ui] In the runs list, runs launched by schedules or sensors will now have tags that link directly to those schedules or sensors.
- [ui] Clicking the "N assets" tag on a run allows you to navigate to the filtered asset graph as well as view the full list of asset keys.
- [ui] Schedules, sensors, and observable source assets now appear on the resource “Uses” page.
- [dagster-dbt] The `DbtCliResource` now validates at definition time that its `project_dir` and `profiles_dir` arguments are directories that respectively contain a `dbt_project.yml` and `profiles.yml`.
- [dagster-databricks] You can now configure a `policy_id` for new clusters when using the `databricks_pyspark_step_launcher` (thanks @zyd14!)
- [ui] Added an experimental sidebar to the Asset lineage graph to aid in navigating large graphs. You can enable this feature under user settings.

### Bugfixes

- Fixed an issue where the `dagster-webserver` command was not indicating which port it was using in the command-line output.
- Fixed an issue with the quickstart_gcp example wasn’t setting GCP credentials properly when setting up its IOManager.
- Fixed an issue where the process output for Dagster run and step containers would repeat each log message twice in JSON format when the process finished.
- [ui] Fixed an issue where the config editor failed to load when materializing certain assets.
- [auto-materialize] Previously, rematerializing an old partition of an asset which depended on a prior partition of itself would result in a chain of materializations to propagate that change all the way through to the most recent partition of this asset. To prevent these “slow-motion backfills”, this behavior has been updated such that these updates are no longer propagated.

### Experimental

- `MaterializeResult` has been added as a new return type to be used in `@asset` / `@multi_asset` materialization functions
- [ui] The auto-materialize page now properly indicates that the feature is experimental and links to our documentation.

### Documentation

- The Concepts category page got a small facelift, to bring it line with how the side navigation is organized.

### Dagster Cloud

- Previously, when importing a dbt project in Cloud, naming the code location “dagster” would cause build failures. This is now disabled and an error is now surfaced.

# 1.4.14 / 0.20.14 (libraries)

### New

- Added a new tooltip to asset runs to either view the asset list or lineage

### Bugfixes

- [ui] Fixed an issue where re-executing a run from a particular run's page wouldn’t navigate to the newly created run

### Experimental

- [dagster-ext] An initial version of the `dagster-ext` module along with subprocess, docker, databricks, and k8s pod integrations are now available. Read more at https://github.com/dagster-io/dagster/discussions/16319. Note that the module is temporarily being published to PyPI under `dagster-ext-process`, but is available in python as `import dagster_ext`.
- [asset checks] Added an ‘execute’ button to run checks without materializing the asset. Currently this is only supported for checks defined with `@asset_check` or `AssetChecksDefinition`.
- [asset checks] Added `check_specs` argument to `@graph_multi_asset`
- [asset checks] Fixed a bug with checks on `@graph_asset` that would raise an error about nonexistant checks

# 1.4.13 / 0.20.13 (libraries)

### New

- `OpExecutionContext.add_output_metadata` can now be called multiple times per output.

### Bugfixes

- The double evaluation of log messages in sensor logging has been fixed (thanks `@janosroden` !)
- Cron schedules targeting leap day (ending with `29 2 *`) no longer cause exceptions in the UI or daemon.
- Previously, if multiple partitioned `observable_source_asset`s with different partition definitions existed in the same code location, runs targeting those assets could fail to launch. This has been fixed.
- When using AutoMaterializePolicies with assets that depended on prior partitions of themselves, updating the `start_date` of their underlying `PartitionsDefinition` could result in runs being launched for partitions that no longer existed. This has been fixed.
- Fixed an issue where auto-materilization could sometimes produce duplicate runs if there was an error in the middle of an auto-materialization tick.
- [dagster-census] A recent change to the Census API broke compatibility with
  this integration. This has been fixed (thanks `@ldnicolasmay`!)
- [dagster-dbt] Fixed an issue where `DagsterDbtTranslator` did not properly invoke `get_auto_materialize_policy` and `get_freshness_policy` for `load_assets_from_dbt_project`.
- [ui] Fixed a number of interaction bugs with the Launchpad config editor, including issues with newlines and multiple cursors.
- [ui] Asset keys and partitions presented in the asset checks UI are sorted to avoid flickering.
- [ui] Backfill actions (terminate backfill runs, cancel backfill submission) are now available from an actions menu on the asset backfill details page.

### Community Contributions

- Typo fix in run monitoring docs (thanks [c0dk](https://github.com/c0dk))!
- Grammar fixes in testing docs (thanks [sonnyarora](https://github.com/sonnyarora))!
- Typo fix in contribution docs (thanks [tab1tha](https://github.com/tab1tha))!

### Experimental

- [dagster-dbt][asset checks] Added support to model dbt tests as Dagster asset checks.
- [asset checks] Added `@graph_asset` support. This can be used to implement blocking checks, by raising an exception if the check fails.
- [asset checks] Fixed `@multi_asset` subsetting, so only checks which target assets in the subset will execute.
- [asset checks] `AssetCheckSpec`s will now cause an error at definition time if they target an asset other than the one they’re defined on.
- [asset checks] The status of asset checks now appears in the asset graph and asset graph sidebar.

### Dagster Cloud

- [Experimental] Added support for freeing global op concurrency slots after runs have finished, using the deployment setting: `run_monitoring > free_slots_after_run_end_seconds`

# 1.4.12 / 0.20.12 (libraries)

### New

- The `context` object now has an `asset_key` property to get the `AssetKey` of the current asset.
- Performance improvements to the auto-materialize daemon when running on large asset graphs.
- The `dagster dev` and `dagster-daemon run` commands now include a `--log-level` argument that allows you to customize the logger level threshold.
- [dagster-airbyte] `AirbyteResource` now includes a `poll_interval` key that allows you to configure how often it checks an Airbyte sync’s status.

### Bugfixes

- Fixed an issue where the dagster scheduler would sometimes raise an error if a schedule set its cron_schedule to a list of strings and also had its default status set to AUTOMATICALLY_RUNNING.
- Fixed an issue where the auto-materialize daemon would sometimes raise a RecursionError when processing asset graphs with long upstream dependency chains.
- [ui] Fixed an issue where the Raw Compute Logs dropdown on the Run page sometimes didn’t show the current step name or properly account for retried steps.

### Community Contributions

- [dagster-databricks] Fixed a regression causing `DatabricksStepLauncher` to fail. Thanks [@zyd14](https://github.com/zyd14)!
- Fixed an issue where Dagster raised an exception when combining observable source assets with multiple partitions definitions. Thanks [@aroig](https://github.com/aroig)!
- [dagster-databricks] Added support for client authentication with OAuth. Thanks [@zyd14](https://github.com/zyd14)!
- [dagster-databricks] Added support for `workspace` and `volumes` init scripts in the databricks client. Thanks [@zyd14](https://github.com/zyd14)!
- Fixed a missing import in our docs. Thanks [@C0DK](https://github.com/C0DK)!

### Experimental

- Asset checks are now displayed in the asset graph and sidebar.
- [Breaking] Asset check severity is now set at runtime on `AssetCheckResult` instead of in the `@asset_check` definition. Now you can define one check that either errors or warns depending on your check logic. `ERROR` severity no longer causes the run to fail. We plan to reintroduce this functionality with a different API.
- [Breaking] `@asset_check` now requires the `asset=` argument, even if the asset is passed as an input to the decorated function. Example:

  ```python
  @asset_check(asset=my_asset)
  def my_check(my_asset) -> AssetCheckResult:
      ...
  ```

- [Breaking] `AssetCheckSpec` now takes `asset=` instead of `asset_key=`, and can accept either a key or an asset definition.
- [Bugfix] Asset checks now work on assets with `key_prefix` set.
- [Bugfix] `Execution failure` asset checks are now displayed correctly on the checks tab.

### Documentation

- [dagster-dbt] Added example of invoking `DbtCliResource` in custom asset/op to API docs.
- [dagster-dbt] Added reference to explain how a dbt manifest can be created at run time or build time.
- [dagster-dbt] Added reference to outline the steps required to deploy a Dagster and dbt project in CI/CD.
- Miscellaneous fixes to broken links and typos.

# 1.4.11 / 0.20.11 (libraries)

### New

- Dagster code servers now wait to shut down until any calls that they are running have finished, preventing them from stopping while in the middle of executing sensor ticks or other long-running operations.
- The `dagster execute job` cli now accepts `—-op-selection` (thanks @silent-lad!)
- [ui] Option (Alt) + R now reloads all code locations (OSS only)

### Bugfixes

- Adds a check to validate partition mappings when directly constructing `AssetsDefinition` instances.
- Assets invoked in composition functions like `@graph` and `@job` now work again, fixing a regression introduced in 1.4.5.
- Fixed an issue where a race condition with parallel runs materializing the same asset could cause a run to raise a RecursionError during execution.
- Fixed an issue where including a resource in both a schedule and a job raised a “Cannot specify resource requirements” exception when the definitions were loaded.
- The `ins` argument to `graph_asset` is now respected correctly.
- Fixed an issue where the daemon process could sometimes stop with a heartbeat failure when the first sensor it ran took a long time to execute.
- Fixed an issue where `dagster dev` failed on startup when the `DAGSTER_GRPC_PORT` `environment variable was set in the environment.
- `deps` arguments for an asset can now be specified as an iterable instead of a sequence, allowing for sets to be passed.
- [dagster-aws] Fixed a bug where the S3PickleIOManager didn’t correctly handle missing partitions when allow_missing_partitions was set. Thanks @o-sirawat!
- [dagster-k8s] in the helm chart, the daemon `securityContext` setting now applies correctly to all init containers (thanks @maowerner!)

### Community Contributions

- [dagster-databricks] Migrated to use new official databricks Python SDK. Thanks @judahrand!

### Experimental

- New APIs for defining and executing checks on software-defined assets. These APIs are very early and subject to change. The corresponding UI has limited functionality. [Docs](https://docs.dagster.io/_apidocs/asset-checks)
- Adds a new auto-materialize skip rule `AutoMaterializeRule.skip_on_not_all_parents_updated` that enforces that an asset can only be materialized if all parents have been materialized since the asset's last materialization.
- Exposed an auto-materialize skip rule – `AutoMaterializeRule.skip_on_parent_missing` –which is already part of the behavior of the default auto-materialize policy.
- Auto-materialize evaluation history will now be stored for 1 month, instead of 1 week.
- The auto-materialize asset daemon now includes more logs about what it’s doing for each asset in each tick in the Dagster Daemon process output.

### Documentation

- [dagster-dbt] Added reference docs for `dagster-dbt project scaffold`.

### Dagster Cloud

- Fixed an issue where the Docker agent would sometimes fail to load code locations with long names with a hostname connection error.

# 1.4.10 / 0.20.10 (libraries)

### Bugfixes

- [dagster-webserver] Fixed an issue that broke loading static files on Windows.

# 1.4.9 / 0.20.9 (libraries)

### Bugfixes

- [dagster-webserver] Fixed an issue that caused some missing icons in the UI.

# 1.4.8 / 0.20.8 (libraries)

### New

- A new `@partitioned_config` decorator has been added for defined configuration for partitioned jobs. Thanks @danielgafni!
- [dagster-aws] The `ConfigurablePickledObjectS3IOManager` has been renamed `S3PickleIOManager` for simplicity. The `ConfigurablePickledObjecS3IOManager` will continue to be available but is considered deprecated in favor of `S3PickleIOManager`. There is no change in the functionality of the I/O manager.
- [dagster-azure] The `ConfigurablePickledObjectADLS2IOManager` has been renamed `ADLS2PickleIOManager` for simplicity. The `ConfigurablePickledObjectADLS2IOManager` will continue to be available but is considered deprecated in favor of `ADLS2PickleIOManager`. There is no change in the functionality of the I/O manager.
- [dagster-dbt] When an exception is raised when invoking a dbt command using `DbtCliResource`, the exception message now includes a link to the `dbt.log` produced. This log file can be inspected for debugging.
- [dagster-gcp] The `ConfigurablePickledObjectGCSIOManager` has been renamed `GCSPickleIOManager` for simplicity. The `ConfigurablePickledObjecGCSIOManager` will continue to be available but is considered deprecated in favor of `GCSPickleIOManager`. There is no change in the functionality of the I/O manager.

### Bugfixes

- Fixed a bug that caused a `DagsterInvariantViolationError` when executing a multi-asset where both assets have self-dependencies on earlier partitions.
- Fixed an asset backfill issue where some runs continue to be submitted after a backfill is requested for cancellation.
- [dagster-dbt] Fixed an issue where using the `--debug` flag raised an exception in the Dagster framework.
- [ui] “Launched run” and “Launched backfill” toasts in the Dagster UI behave the same way. To open in a new tab, hold the cmd/ctrl key when clicking “View”
- [ui] When opening step compute logs, the view defaults to `stderr` which aligns with Python’s logging defaults.
- [ui] When viewing a global asset graph with more than 100 assets, the “choose a subset to display” prompt is correctly aligned to the query input.

### Community Contributions

- Fix for loading assets with a `BackfillPolicy`, thanks @ruizh22!

### Experimental

- [dagster-graphql] The Dagster GraphQL Python client now includes a default timeout of 300 seconds for each query, to ensure that GraphQL requests don’t hang and never return a response. If you are running a query that is expected to take longer than 300 seconds, you can set the `timeout` argument when constructing a `DagsterGraphQLClient`.
- [ui] We are continuing to improve the new horizontal rendering of the asset graph, which you can enable in Settings. This release increases spacing between nodes and improves the traceability of arrows on the graph.

### Documentation

- Several Pythonic resources and I/O managers now have API docs entries.
- Updated the tutorial’s example project and content to be more explicit about resources.
- [dagster-dbt] Added API docs examples for `DbtCliResource` and `DbtCliResource.cli(...)`.
- Some code samples in API docs for `InputContext` and `OutputContext` have been fixed. Thanks @Sergey Mezentsev!

### Dagster Cloud

- When setting up a new organization by importing a dbt project, using GitLab is now supported.

# 1.4.7 / 0.20.7 (libraries)

### Experimental

- Added a `respect_materialization_data_versions` option to auto materialization. It can enabled in `dagster.yaml` with

  ```yaml
  auto_materialize:
    respect_materialization_data_versions: True
  ```

  This flag may be changed or removed in the near future.

# 1.4.6 / 0.20.6 (libraries)

### New

- ops or assets with multiple outputs that are all required and return type `None`/ `Nothing` will interpret an explicitly or implicitly returned value `None` to indicate that all outputs were successful.
- The `skip_reason` argument to the constructor of `SensorResult` now accepts a string in addition to a `SkipReason`.
- [dagster-k8s] Added a `step_k8s_config` field to `k8s_job_executor` that allows you to customize the raw Kubernetes config for each step in a job. See [the docs](https://docs.dagster.io/deployment/guides/kubernetes/customizing-your-deployment#kubernetes-configuration-on-every-step-in-a-run) for more information.
- [dagster-k8s] Launched run pods now have an additional code location label.
- [dagster-ui] The runs table now lets you toggle which tags are always visible.
- [dagster-dbt] `dagster-dbt project scaffold` now creates the scaffold in multiple files:
  - `constants.py` contains a reference to your manifest and dbt project directory
  - `assets.py` contains your initial dbt assets definitions
  - `definitions.py` contains the code to load your asset definitions into the Dagster UI
  - `schedules.py` contains an optional schedule to add for your dbt assets
- [dagster-dbt] Added new methods `get_auto_materialize_policy` and `get_freshness_policy` to `DagsterDbtTranslator`.
- [dagster-fivertran] Sync options can now be passed to `load_assets_from_fivetran_instance`.
- [dagster-wandb] W&B IO Manager now handles partitions natively. (Thanks [@chrishiste](https://github.com/chrishiste)!)

### Bugfixes

- Previously, canceling large asset backfills would cause the daemon to time out and display a “not running” error. This has been fixed.
- [dagster-ssh] Previously the `SSHResource` would warn when `allow_host_key_change` was set. Now known hosts are always loaded from the system hosts file, and the `allow_host_key_change` parameter is ignored.
- Previously, when using AutoMaterializePolicies, partitioned assets downstream of partitioned observable source assets could be materialized before their parent partitions were observed. This has been fixed.

### Documentation

- `@graph_multi_asset` now has an API docs entry.
- The `GCSComputeLogManager` example in the [Dagster Instance reference](https://docs.dagster.io/deployment/dagster-instance#gcscomputelogmanager) is now correct.
- Several outdated K8s documentation links have been removed from the [Customizing your Kubernetes deployment guide](https://docs.dagster.io/deployment/guides/kubernetes/customizing-your-deployment).
- Added callouts to the [GitHub](https://docs.dagster.io/dagster-cloud/managing-deployments/branch-deployments/using-branch-deployments-with-github) and [GitLab](https://docs.dagster.io/dagster-cloud/managing-deployments/branch-deployments/using-branch-deployments-with-gitlab) Branch Deployment guides specifying that some steps are optional for Serverless users.
- The “Graphs” page under the “Concepts” section has been renamed to “Op Graphs” and moved inside under the “Ops” heading.
- [dagster-dbt] Added API examples for `@dbt_assets` for the following use-cases:
  - Running dbt commands with flags
  - Running dbt commands with `--vars`
  - Running multiple dbt commands
  - Retrieving dbt artifacts after running a dbt command
  - Invoking other Dagster resouces alongside dbt
  - Defining and accessing Dagster config alongside dbt

### Dagster Cloud

- The viewer role now has permission to edit their own user tokens.

# 1.4.5 / 0.20.5 (libraries)

### New

- `@graph_asset` now takes a `config` parameter equivalent to the parameter on `@graph`.
- Added an optional `dynamic_partitions_store` argument to `DynamicPartitionsDefinition` for multi-partition run properly with dynamic partitions (Thanks @elzzz!).
- [dagster-grpahql] Added ` partitionsByAssets` to `backfillParams` for ranged partition backfill (Thanks @ruizh22!).
- [dagster-dbt] Support for `dbt-core==1.6` has been added.
- [dagster-dbt] `DbtCliResource` now supports configuring `profiles_dir`.
- [dagster-k8s] Allow specifying `restart_policy` on `k8s_job_op` (Thanks @Taadas!).
- [dagster-snowflake] Added `authenticator` to `SnowflakePandasIOManager`, which allows specifying the authentication mechanism to use (Thanks @pengw0048!).
- [ui] The Asset > Events page now allows you to filter by event type, making it easy to hide observations.
- [ui] The Asset > Partitions page checks to see if the selected partition is stale and displays stale causes in the details pane.
- [ui] Hovering over "Fresh" tags now provides detailed information about why the last materialization meets the asset's freshness policy.
- [ui] The global asset graph can now be filtered to display a subset of the available asset groups.

### Bugfixes

- In some situations, multiple materializations of the same asset could be kicked off when using a lazy `AutoMaterializePolicy` with assets that had at least one source asset parent and at least one non-source asset parent. This has been fixed.
- After applying an eager `AutoMaterializePolicy` to a time-partitioned asset downstream of an unpartitioned asset, the latest partition would only ever be materialized a single time, rather than updating in response to any parent updates. This has been fixed.
- Fixed an issue that would cause the creation of a `StaticPartitionsDefinition` containing many thousands of partitions could take a significant amount of time.
- The run coordinator daemon now uses a fresh request context on each iteration, fixing an issue where stale grpc server references could be used in certain high volume conditions.
- Automatically generated data versions for partitioned assets now correctly reflect the data versions of upstream partitions. Previously, they were computed using the data versions from the most recent materializations of upstream assets regardless of partition.
- [dagster-airbyte] Previously, attempting to load assets from an Airbyte instance in which some of the tables had hyphens in their name would result in an error. This has been fixed.
- [dagster-dbt] Previously, attempting to load assets from a dbt project in which some of the models had hyphens in their name would result in an error. This has been fixed.
- [dagstermill] Fixed a bug where known state for executing dagstermill ops was not correctly passed in (Thanks @motuzov!).
- [ui] Pressing the up or down arrow key without a selection in the asset graph no longer causes a page error.

### Documentation

- Added the starter project’s template for Dagster University.
- Fixed an incorrect method name in DagsterDbtTranslator Docs (Thanks @akan72!).

### Dagster Cloud

- When importing a dbt project on the Dagster Cloud setup page, an `Unexpected exception` error would be raised when scaffolding a pull request on a repository with no `profiles.yml`. This behavior has been updated to raise a more descriptive error message on the repo selection page.
- The running multiple agents guide has been revamped to discuss running agent replicas and zero-downtime deployment of the agent.
- The `agentReplicas` config setting on the helm chart has been renamed to `isolatedAgents`. In order to use this config setting, your user code dagster version needs to be `1.4.3` or greater.

# 1.4.4 / 0.20.4 (libraries)

### New

- [ui] When viewing a run for auto-materialized assets, show a tag with information about the assets that were materialized.
- [ui] In the Auto-materialize History view, when one or more of an asset’s parents have been updated, the set of updated parents will be viewable.
- [ui] Link to the auto-materialized history for an asset from the asset DAG view.
- [ui] For runs that were the result of auto-observation, show a tag for this in the Runs list view.
- Added warnings for storage incompatibility with the experimental global op concurrency.

### Bugfixes

- [dagster-dbt] Fixed an issue where `dagster-dbt project scaffold` didn’t create a project directory with all the scaffolded files.
- Fixed an issue which could cause errors when using the `SpecificPartitionsPartitionMapping` with auto-materialization.

### Breaking Change

- Previously, it was possible to set `max_materializations_per_minute` on an `AutoMaterializePolicy` to a non-positive number. This will now result in an error.

### Community Contributions

- Fix for loading multipartitions paths in `upath_io_manager` from @harrylojames; thank you!
- Docs typo fix from @C0DK; thank you!

### Documentation

- Revamped the dagster-dbt tutorial to take advantage of `dagster project scaffold` and the new dagster-dbt APIs.

# 1.4.3 / 0.20.3 (libraries)

### New

- [dagster-dbt] When invoking`dagster-dbt project scaffold` on a dbt project directory, if a `profiles.yml` exists in the root of the directory, its contents are used to add dbt adapter packages to the scaffolded `setup.py`.
- The default sentinel value for the multiprocessing executor’s `max_concurrent` field has been changed from `0` to `None` to more clearly signal its intent. A value of `0` is still interpreted as the sentinel value which dynamically allocates `max_concurrent` based on detected CPU count.

### Bugfixes

- IO managers defined on jobs will now be properly merged with resources defined in `Definitions`, so that jobs are able to override the IO manager used.
- [dagster-fivetran] Fixed an issue where `EnvVars` in a `FivetranResource` would not be evaluated when loading assets from the Fivetran instance.
- [dagster-airbyte] Fixed an issue where `EnvVars` in an `AirbyteResource` would not be evaluated when loading assets from the Airbyte resource.

### Documentation

- [dagster-dbt] Added API docs for `DbtCliResource`, `DbtCliInvocation`, `@dbt_assets`, `DagsterDbtTranslator`, `dagster-dbt project scaffold`
- [dagster-dbt] Expanded references for new APIs:
  - Added documentation to customize asset definition attributes for dbt assets
  - Added documentation to define upstream and downstream dependencies to dbt assets
  - Added documentation to define schedules for dbt assets

### Dagster Cloud

- The experimental agent config setting `agent_replicas`has been deprecated in favor of a new name `isolated_agents` (`agentReplicas` --> `isolatedAgents` in the helm chart). Upgrading to the new name requires all code locations to be on `1.4.3` or greater.

# 1.4.2 / 0.20.2 (libraries)

### Bugfixes

- Fixes a bug in `dagster-dbt` that was preventing it from correctly materializing subselections of dbt asset.

# 1.4.1 / 0.20.1 (libraries)

### Bugfixes

- Fixes a bug in `dagster-dbt` that was preventing it efficiently loading dbt projects from a manifest.

# 1.4.0 / 0.20.0 (libraries) "Material Girl"

## **Major Changes since 1.3.0 (core) / 0.19.0 (libraries)**

### Core

- **Auto-materialize history** – We’ve added a UI that tracks why assets were or were not materialized according to their`AutoMaterializePolicy`. It’s located under `Assets` → Select an asset with an `AutoMaterializePolicy` → `Auto-materialize history` tab.
- **Auto-materialize performance** – We’ve made significant performance improvements to the Asset Daemon, allowing it to keep up with asset graphs containing thousands of assets and assets with a large history of previously-materialized partitions.
- **Asset backfill cancellation** — Asset backfills can now be canceled, bring them to parity with job backfills. When an asset backfill is requested for cancellation, the daemon cancels runs until all runs are terminated, then marks the backfill as “canceled”.
- **non_argument_deps → deps** – We’ve deprecated the `non_argument_deps` parameter of `@asset` and `@multi_asset` in favor of a new `deps` parameter. The new parameter makes it clear that this is a first-class way of defining dependencies, makes code more concise, and accepts `AssetsDefinition` and `SourceAsset` objects, in addition to the `str`s and `AssetKey`s that the previous parameter accepted.
- **Group-level asset status UI** – the new Assets Overview dashboard, located underneath the Activity tab of the Overview page, shows the status all the assets in your deployment, rolled up by group.
- **Op concurrency (experimental)** — We’ve added a feature that allows limiting the number of concurrently executing ops across runs. [[docs](https://docs.dagster.io/guides/limiting-concurrency-in-data-pipelines#limiting-opasset-concurrency-across-runs)]
- `DynamicPartitionsDefinition` and `SensorResult` are no longer marked experimental.
- **Automatically observe source assets, without defining jobs (experimental** – The `@observable_source_asset` decorator now accepts an `auto_observe_interval_minutes` parameter. If the asset daemon is turned on, then the observation function will automatically be run at this interval. Downstream assets with eager auto-materialize policies will automatically run if the observation function indicates that the source asset has changed. [[docs](https://docs.dagster.io/concepts/assets/asset-auto-execution#auto-materialize-policies-and-data-versions)]
- **Dagit → Dagster UI** – To reduce the number of Dagster-specific terms that new users need to learn when learning Dagster, “Dagit” has been renamed to the “The Dagster UI”. The `dagit` package is deprecated in favor of the `dagster-webserver` package.
- **Default config in the Launchpad** - When you open the launchpad to kick off a job or asset materialization, Dagster will now automatically populate the default values for each field.

### dagster-dbt

- The **new `@dbt_assets` decorator** allows much more control over how Dagster runs your dbt project. [[docs](https://docs.dagster.io/_apidocs/libraries/dagster-dbt#dagster_dbt.dbt_assets)]
- The **new `dagster-dbt project scaffold` command line interface** makes it easy to create files and directories for a Dagster project that wraps an existing dbt project.
- **Improved APIs for defining asset dependencies** – The new `get_asset_key_for_model` and `get_asset_key_for_source` utilities make it easy to specify dependencies between upstream dbt assets and downstream non-dbt assets. And you can now more easily specify dependencies between dbt models and upstream non-dbt assets by specifying Dagster asset keys in the dbt metadata for dbt sources.

## **Since 1.3.14 (core) / 0.19.14 (libraries)**

### New

- The published Dagster Docker images now use Python 3.10, instead of 3.7.
- We’ve deprecated the `non_argument_deps` parameter of `@asset` and `@multi_asset` in favor of a new `deps` parameter. The new parameter makes it clear that this is a first-class way of defining dependencies, makes code more concise, and accepts `AssetsDefinition` and `SourceAsset` objects, in addition to the `str`s and `AssetKey`s that the previous parameter accepted.
- The `UPathIOManager` can now be extended to load multiple partitions asynchronously (Thanks Daniel Gafni!).
- By default, Dagster will now automatically load default config values into the launchpad. This behavior can be disabled in the user settings page.
- [dagster-k8s] The Helm chart now sets readiness probes on user code deployment servers by default. These can be disabled with `dagster-user-deployments.deployments.[...].readinessProbe.enabled=false`.
- [dagster-airbyte] In line with the deprecation of `non_argument_deps` in favor of `deps`, `build_airbyte_assets` now accepts a `deps` parameter.
- [dagstermill] In line with the deprecation of `non_argument_deps` in favor of `deps`, `define_dagstermill_asset` now accepts a `deps` parameter.
- [dagster-dbt] A new CLI utility `dagster-dbt project scaffold` has been provided to scaffold a Dagster code location for an existing dbt project.

### Bugfixes

- Duplicate partition keys passed to `StaticPartitionsDefinition` will now raise an error.
- Fixed a bug that caused lazy `AutoMaterializePolicy`'s to not materialize missing assets.
- [ui] Fixed an issue where global search and large DAGs were broken when using `--path-prefix`.
- Schedule and sensor run submissions are now kept up to date with the current workspace, fixing an issue where a stale reference to a server would be used in some conditions.
- [dagster-dbt] Fixed an issue where materializing dbt models with the same name as a dbt source would cause an error.

### Breaking Changes

- Support for Python 3.7 has been dropped.
- `build_asset_reconciliation_sensor` (Experimental) has been removed. It was deprecated in 1.3 in favor of `AutoMaterializePolicy`.
- `asset_key(s)` properties on `AssetIn` and `AssetDefinition` have been removed in favor of `key(s)`. These APIs were deprecated in 1.0.
- `root_input_manager` and `RootInputManagerDefinition` have been removed in favor of `input_manager` and `InputManagerDefinition`. These APIs were deprecated in 1.0.
- [dagster-pandas] The `event_metadata_fn` parameter on `create_dagster_pandas_dataframe_type` has been removed in favor of `metadata_fn`.
- [dagster-dbt] The library has been substantially revamped to support the new `@dbt_assets` and `DbtCliResource`. See the migration guide for details.
  - Group names for dbt assets are now taken from a dbt model's group. Before, group names were determined using the model's subdirectory path.
  - Support for `dbt-rpc` has been removed.
  - The class alias `DbtCloudResourceV2` has been removed.
  - `DbtCli` has been renamed to `DbtCliResource`. Previously, `DbtCliResource` was a class alias for `DbtCliClientResource`.
  - `load_assets_from_dbt_project` and `load_assets_from_dbt_manifest` now default to `use_build=True`.
  - The default assignment of groups to dbt models loaded from `load_assets_from_dbt_project` and `load_assets_from_dbt_manifest` has changed. Rather than assigning a group name using the model’s subdirectory, a group name will be assigned using the dbt model’s [dbt group](https://docs.getdbt.com/docs/build/groups).
  - The argument `node_info_to_definition_metadata_fn` for `load_assets_from_dbt_project` and `load_assets_from_dbt_manifest` now overrides metadata instead of adding to it.
  - The arguments for `load_assets_from_dbt_project` and `load_assets_from_dbt_manifest` now must be specified using keyword arguments.
  - When using the new `DbtCliResource` with `load_assets_from_dbt_project` and `load_assets_from_dbt_manifest`, stdout logs from the dbt process will now appear in the compute logs instead of the event logs.

### Deprecations

- The `dagit` python package is deprecated and will be removed in 2.0 in favor of `dagster-webserver`. See the migration guide for details.
- The following fields containing “dagit” in the Dagster helm chart schema have been deprecated in favor of “dagsterWebserver” equivalents (see migration guide for details):
  - `dagit` → `dagsterWebserver`
  - `ingress.dagit` → `ingress.dagsterWebserver`
  - `ingress.readOnlyDagit` → `ingress.readOnlyDagsterWebserver`
- [Dagster Cloud ECS Agent] We've introduced performance improvements that rely on the [AWS Resource Groups Tagging API](https://docs.aws.amazon.com/resourcegroupstagging/latest/APIReference/overview.html). To enable, grant your agent's IAM policy permission to `tag:GetResources`. Without this policy, the ECS Agent will log a deprecation warning and fall back to its old behavior (listing all ECS services in the cluster and then listing each service's tags).
- `DbtCliClientResource`, `dbt_cli_resource` and `DbtCliOutput` are now being deprecated in favor of `DbtCliResource`.
- A number of arguments on `load_assets_from_dbt_project` and `load_assets_from_dbt_manifest` are now deprecated in favor of other options. See the migration for details.

### Community Contributions

- Docs typo fix from @chodera, thank you!
- Run request docstring fix from @Jinior, thank you!

### Documentation

- All public methods in the Dagster API now have docstrings.
- The entirety of the documentation has been updated to now refer to the “Dagster webserver” or “Dagster UI” where “Dagit” was previously used for both entities.

# 1.3.14 (core) / 0.19.14 (libraries)

### New

- `DynamicPartitionsDefinition` and `SensorResult` are no longer marked experimental
- `DagsterInstance` now has a `get_status_by_partition` method, which returns the status of each partition for a given asset. Thanks renzhe-brian!
- `DagsterInstance` now has a `get_latest_materialization_code_versions` method, which returns the code version of the latest materialization for each of the provided (non-partitioned) assets.
- The error message for when an asset illegally depends on itself is now more informative.
- Further performance improvements for the Asset Daemon.
- Performance improvements in the asset graph view for large asset graphs.
- Pandas 2.x is now supported in all dagster packages.
- `build_asset_context` has been added as an asset focused replacement for `build_op_context`.
- `build_op_context` now accepts a `partition_key_range` parameter.
- New `AssetSelection.upstream_source_assets` method allows selecting source assets upstream of the current selection.
- `AssetSelection.key_prefixes` and `AssetSelection.groups` now accept an optional `include_sources` parameter.
- The AutoMaterialize evaluations UI now provides more details about partitions and waiting on upstream assets.
- [dbt] The `DbtCli` resource is no longer marked experimental.
- [dbt] The `global_config` parameter of the `DbtCli` resource has been renamed to `global_config_flags`
- [dbt] `load_assets_from_dbt_project` and `load_assets_from_dbt_manifest` now work with the `DbtCli` resource.
- [dbt] The `manifest` argument of the `@dbt_assets` decorator now additionally can accept a `Path` argument representing a path to the manifest file or dictionary argument representing the raw manifest blob.
- [dbt] When invoking `DbtCli.cli` from inside a `@dbt_assets`-decorated function, you no longer need to supply the manifest argument as long as you provide the context argument.
- [dbt] The `DbtManifest` object can now generate schedules using dbt selection syntax.

```python
dbt_manifest.build_schedule(
  job_name="materialize_dbt_models",
  cron_schedule="0 0 * * *",
  dbt_select="fqn:*"
)
```

- [dbt] When invoking `DbtCli.cli` and the underlying command fails, an exception will now be raised. To suppress the exception, run the `DbtCli.cli(..., raise_on_error=False`).
- [ui] You can now alphabetically sort your partitions on the asset partitions page
- [ui] A button in the “Run is materializing this asset” and “Run failed to materialize this asset” banners provides direct access to the relevant run logs

### Bugfixes

- Fixed a bug that caused asset metadata to not be available available on the `OutputContext` when using `with_attributes` or `AssetsDefinition.from_graph`.
- Previously, if a partitioned asset at the root of the graph had more missing partitions than its AutoMaterializePolicy’s `max_materializations_per_minute` parameter, those older partitions would not be properly discarded from consideration on subsequent ticks. This has been fixed.
- Fixed a bug that caused AutoMaterializePolicy.lazy() to not materialize missing assets that were downstream of assets without an AutoMaterializePolicy.
- In rare cases, the AssetDaemon could hit an exception when using a combination of freshness policies and observable source assets. This has been fixed.
- Previously, string type annotations (most commonly via modules containing `from __future__ import annotations`) would cause errors in most cases when used with Dagster definitions. This has been fixed for the vast majority of cases.
- `AssetExecutionContext` has returned to being a type alias for `OpExecutionContext`.
- [ui] Date filtering on the runs page now takes your timezone into consideration
- [ui] Fixed a bug where selecting partitions in the launchpad dialog cleared out your configuration
- [ui] In the run Gantt chart, executed steps that follow skipped steps no longer render off the far right of the visualization.
- [ui] Cancelling a running backfill no longer makes canceled partitions un-selectable on the job partitions page and backfill modal, and cancellation is shown in gray instead of red.

### Breaking Changes

- [experimental] The internal `time_window_partition_scope_minutes` parameter of the `AutoMaterializePolicy` class has been removed. Instead, `max_materializations_per_minute` should be used to limit the number of runs that may be kicked off for a partitioned asset.

### Deprecations

- [dbt] `DbtCliResource` has been deprecated in favor of `DbtCli`.
- The python package `dagit` has been deprecated in favor of a new package `dagster-webserver`.
- `OpExecutionContext.asset_partition_key_range` has been deprecated in favor of `partition_key_range`.

### Community Contributions

- The `databricks_pyspark_step_launcher` will no longer error when executing steps that target a single partition of a `DynamicPartitionsDefinition` (thanks @[weberdavid](https://github.com/weberdavid)!).
- Increased timeout on readinessProbe for example user code images, which prevents breakages in certain scenarios (thanks @[leehuwuj](https://github.com/leehuwuj))!
- Avoid creation of erroneous local directories by GCS IO manager (thanks @[peterjclaw](https://github.com/PeterJCLaw))!
- Fixed typo in intro docs (thanks @[adeboyed](https://github.com/adeboyed))!
- Fix typo in bigquery docs (thanks @[nigelainscoe](https://github.com/nigelainscoe))!
- Fix typing on run tag validation (thanks @[yuvalgimmunai](https://github.com/yuvalgimmunai))!
- Allow passing repositoryCredentials arn as config to ecs run launcher (thanks @[armandobelardo](https://github.com/armandobelardo))!

### Experimental

- The `@observable_source_asset` decorator now accepts an `auto_observe_interval_minutes` parameter. If the asset daemon is turned on, then the observation function will automatically be run at this interval.
- [dbt] `DbtCliTask` has been renamed to `DbtCliInvocation`
- [dbt] The `get_asset_key_by_output_name` and `get_node_info_by_output_name` methods of `DbtManifest` have been renamed to`get_asset_key_for_output_name` and `get_node_info_for_output_name`, respectively.
- [ui] A new feature flag allows you to switch Asset DAG rendering to a tighter horizontal layout, which may be preferable in some scenarios

### Documentation

- Many public methods that were missing in the API docs are now documented. Updated classes include `DagsterInstance`, `*MetadataValue`, `DagsterType`, and others.
- `dagster-pandera` now has an API docs page.
- Deprecated methods in the API docs now are marked with a special badge.

# 1.3.13 (core) / 0.19.13 (libraries)

### Bugfixes

- Fixes a bug in `dagster project from-example` that was preventing it from downloading examples correctly.

# 1.3.12 (core) / 0.19.12 (libraries)

### New

- The `--name` argument is now optional when running `dagster project from-example`.
- An asset key can now be directly specified via the asset decorator: `@asset(key=...)`.
- `AssetKey` now has a `with_prefix` method.
- Significant performance improvements when using `AutoMaterializePolicy`s with large numbers of partitions.
- `dagster instance migrate` now prints information about changes to the instance database schema.
- The [`dagster-cloud-agent` helm chart](https://artifacthub.io/packages/helm/dagster-cloud/dagster-cloud-agent) now supports setting K8s labels on the agent deployment.
- [ui] Step compute logs are shown under “Last Materialization” in the asset sidebar.
- [ui] Truncated asset names now show a tooltip when hovered in the asset graph.
- [ui] The “Propagate changes” button has been removed and replaced with “Materialize Stale and Missing” (which was the “Propagate changes” predecessor).

### Bugfixes

- [ui] Fixed an issue that prevented filtering by date on the job-specific runs tab.
- [ui] “F” key with modifiers (alt, ctrl, cmd, shift) no longer toggles the filter menu on pages that support filtering.
- [ui] Fix empty states on Runs table view for individual jobs, to provide links to materialize an asset or launch a run for the specific job, instead of linking to global pages.
- [ui] When a run is launched from the Launchpad editor while an editor hint popover is open, the popover remained on the page even after navigation. This has been fixed.

- [ui] Fixed an issue where clicking on the zoom controls on a DAG view would close the right detail panel for selected nodes.
- [ui] Fixed an issue shift-selecting assets with multi-component asset keys.
- [ui] Fixed an issue with the truncation of the asset stale causes popover.
- When using a `TimeWindowPartitionMapping` with a `start_offset` or `end_offset` specified, requesting the downstream partitions of a given upstream partition would yield incorrect results. This has been fixed.
- When using `AutoMaterializePolicy`s with observable source assets, in rare cases, a second run could be launched in response to the same version being observed twice. This has been fixed.

- When passing in `hook_defs` to `define_asset_job`, if any of those hooks had required resource keys, a missing resource error would surface when the hook was executed. This has been fixed.
- Fixed a typo in a documentation URL in `dagster-duckdb-polars` tests. The URL now works correctly.

### Experimental

- [dagster-dbt] Added methods to `DbtManifest` to fetch asset keys of sources and models: `DbtManifest.get_asset_key_for_model`, `DbtManifest.get_asset_key_for_source`. These methods are utilities for defining python assets as dependencies of dbt assets via `@asset(key=manifest.get_asset_key_for_model(...)`.
- [dagster-dbt] The use of the `state_path` parameter with `DbtManifestAssetSelection` has been deprecated, and will be removed in the next minor release.
- Added experimental support for limiting global op/asset concurrency across runs.

### Dependencies

- Upper bound on the `grpcio` package (for `dagster`) has been removed.

### Breaking Changes

- Legacy methods of `PartitionMapping` have been removed. Defining custom partition mappings has been unsupported since 1.1.7.

### Community Contributions

- [dagster-airbyte] Added the ability to specify asset groups to `build_airbyte_assets`. Thanks [@guy-rvvup](https://github.com/guy-rvvup)!

### Documentation

- For Dagster Cloud Serverless users, we’ve added our static IP addresses to [the Serverless docs](https://docs.dagster.io/dagster-cloud/deployment/serverless#whitelisting-dagsters-ip-addresses).

# 1.3.11 (core) / 0.19.11 (libraries)

### New

- Assets with lazy auto-materialize policies are no longer auto-materialized if they are missing but don’t need to be materialized in order to help downstream assets meet their freshness policies.
- [ui] The descriptions of auto-materialize policies in the UI now include their skip conditions along with their materialization conditions.
- [dagster-dbt] Customized asset keys can now be specified for nodes in the dbt project, using `meta.dagster.asset_key`. This field takes in a list of strings that are used as the components of the generated `AssetKey`.

```yaml
version: 2

models:
  - name: users
    config:
      meta:
        dagster:
          asset_key: ["my", "custom", "asset_key"]
```

- [dagster-dbt] Customized groups can now be specified for models in the dbt project, using `meta.dagster.group`. This field takes in a string that is used as the Dagster group for the generated software-defined asset corresponding to the dbt model.

```yaml
version: 2

models:
  - name: users
    config:
      meta:
        dagster:
          group: "my_group"
```

### Bugfixes

- Fixed an issue where the `dagster-msteams` and `dagster-mlflow` packages could be installed with incompatible versions of the `dagster` package due to a missing pin.
- Fixed an issue where the `dagster-daemon run` command sometimes kept code server subprocesses open longer than it needed to, making the process use more memory.
- Previously, when using `@observable_source_asset`s with AutoMaterializePolicies, it was possible for downstream assets to get “stuck”, not getting materialized when other upstream assets changed, or for multiple down materializations to be kicked off in response to the same version being observed multiple times. This has been fixed.
- Fixed a case where the materialization count for partitioned assets could be wrong.
- Fixed an error which arose when trying to request resources within run failure sensors.
- [dagster-wandb] Fixed handling for multi-dimensional partitions. Thanks @chrishiste

### Experimental

- [dagster-dbt] improvements to `@dbt_assets`
  - `project_dir` and `target_path` in `DbtCliTask` are converted from type `str` to type `pathlib.Path`.
  - In the case that dbt logs are not emitted as json, the log will still be redirected to be printed in the Dagster compute logs, under `stdout`.

### Documentation

- Fixed a typo in dagster_aws S3 resources. Thanks @akan72
- Fixed a typo in link on the Dagster Instance page. Thanks @PeterJCLaw

# 1.3.10 (core) / 0.19.10 (libraries)

### New

- [dagster-dbt] By default, freshness policies and auto materialize policies on dbt assets can now be specified using the `dagster` field under `+meta` configuration. The following are equivalent:

Before:

```yaml
version: 2

models:
  - name: users
    config:
      dagster_freshness_policy:
        maximum_lag_minutes: 60
        cron_schedule: "0 9 * * *"
      dagster_auto_materialize_policy:
        type: "lazy"
```

After:

```yaml
version: 2

models:
  - name: users
    config:
      meta:
        dagster:
          freshness_policy:
            maximum_lag_minutes: 60
            cron_schedule: "0 9 * * *"
          auto_materialize_policy:
            type: "lazy"
```

- Added support for Pythonic Config classes to the `@configured` API, which makes reusing op and asset definitions easier:

  ```python
  class GreetingConfig(Config):
      message: str

  @op
  def greeting_op(config: GreetingConfig):
      print(config.message)

  class HelloConfig(Config):
      name: str

  @configured(greeting_op)
  def hello_op(config: HelloConfig):
      return GreetingConfig(message=f"Hello, {config.name}!")
  ```

- Added `AssetExecutionContext` to replace `OpExecutionContext` as the context object passed in to `@asset` functions.
- `TimeWindowPartitionMapping` now contains an `allow_nonexistent_upstream_partitions` argument that, when set to `True`, allows a downstream partition subset to have nonexistent upstream parents.
- Unpinned the `alembic` dependency in the `dagster` package.
- [ui] A new “Assets” tab is available from the Overview page.
- [ui] The Backfills table now includes links to the assets that were targeted by the backfill.

### Bugfixes

- Dagster is now compatible with a breaking change introduced in `croniter==1.4.0`. Users of earlier versions of Dagster can pin `croniter<1.4`.
- Fixed an issue introduced in 1.3.8 which prevented resources from being bound to sensors when the specified job required late-bound resources.
- Fixed an issue which prevented specifying resource requirements on a `@run_failure_sensor`.
- Fixed an issue where the asset reconciliation sensor failed with a “invalid upstream partitions” error when evaluating time partitions definitions with different start times.
- [dagster-k8s] Fixed an issue where annotations are not included in the Dagster Helm chart for the pod that is created when configuring the Helm chart to run database migrations.
- [ui] Fixed an issue with filtering runs by created date on the Runs page.
- [ui] The “upstream partitions missing” warning no longer appears in the asset backfill dialog if the upstream partitioned asset is a source asset.
- [dagster-dbt] Fixed an issue where asset dependencies for dbt models with ephemeral models in between them would sometimes be improperly rendered.

### Community Contributions

- Added support for setting resources in asset and multi_asset sensors. Thanks [@plaflamme](https://github.com/plaflamme)!
- Fixed an issue where `py.typed` was missing in the `dagster-graphql` package. Thanks [@Tanguy-LeFloch](https://github.com/Tanguy-LeFloch)!

### Experimental

- Evaluation history for `AutoMaterializePolicy`s will now be cleared after 1 week.
- [dagster-dbt] Several improvements to `@dbt_assets`:
  - `profile` and `target` can now be customized on the `DbtCli` resource.
  - If a `partial_parse.msgpack` is detected in the target directory of your dbt project, it is now copied into the target directories created by `DbtCli` to take advantage of [partial parsing](https://docs.getdbt.com/reference/parsing).
  - The metadata of assets generated by `@dbt_assets` can now be customized by overriding `DbtManifest.node_info_to_metadata`.
  - Execution duration of dbt models is now added as default metadata to `AssetMaterialization`s.

### Documentation

- Added [a new tutorial section](https://docs.dagster.io/tutorial/connecting-to-external-services) about using resources.

### Dagster Cloud

- Fixed an issue where overriding the container name of a code server pod using `serverK8sConfig.containerConfig.name` did not actually change the container name.

# 1.3.9 (core) / 0.19.9 (libraries)

### Dagster Cloud

- Fixed an issue in the `1.3.8` release where the Dagster Cloud agent would sometimes fail to start up with an import error.

# 1.3.8 (core) / 0.19.8 (libraries)

### New

- Multipartitioned assets with one time dimension can now depend on earlier partitions of themselves.
- `define_asset_job` now accepts a `hooks` argument.
- Added support for `sqlalchemy==2.x`
- [ui] The Runs page has been revamped with better filtering support
- [ui] The automaterialize policy page for SDA’s using the experimental AutomaterializePolicy feature now indicates time periods where no materializations happened due to no materialization conditions being met
- [dagster-k8s] The Dagster Helm chart now includes an `additionalInstanceConfig` key that allows you to supply additional configuration to the [Dagster instance](https://docs.dagster.io/deployment/dagster-instance#dagster-instance).
- [dagster-aws] The `EcsRunLauncher` now uses a different task definition family for each job, instead of registering a new task definition revision each time a different job is launched.
- [dagster-aws] The `EcsRunLauncher` now includes a `run_ecs_tags` config key that lets you configure tags on the launched ECS task for each run.

### Bugfixes

- When a sensor had yield statement and also returned a `SkipReason`, the `SkipReason` would be ignored. This has been fixed.
- [dagster-cloud] Fixed a bug in the docker user code launcher that was preventing code location containers from being properly cleaned up.
- Fixed an issue where the Dagster UI would sometimes raise a ``RuntimeError: dictionary changed size during iteration` exception while code servers were being reloaded.
- Fixed an issue where the Dagster daemon reloaded your code server every 60 seconds when using the new experimental `dagster code-server start` CLI, instead of only reloading your code when you initiate a reload from the Dagster UI.
- Fixed a GraphQL error which would occur when loading the default config for jobs without config.
- [dagster-dbt] Fixed an error which would arise when trying to load assets from a DBT Cloud instance using the Pythonic-style resource.

### Community Contributions

- Added the ability to specify metadata on asset jobs, by adding the `metadata` parameter to `define_asset_job` (Thanks **[Elliot2718](https://github.com/Elliot2718)!)**
- [dagster-databricks] Connected databricks stdout to local stdout, to be handled by the compute log manager (Thanks **[loerinczy](https://github.com/loerinczy)!)**
- [dagster-census] Fixed `poll_sync_run` to handle the “preparing” status from the Census API (Thanks **[ldnicolasmay](https://github.com/ldnicolasmay)!)**

### Experimental

- `@observable_source_asset`-decorated functions can now return a `DataVersionsByPartition` to record versions for partitions.
- `@dbt_assets`
  - `DbtCliTask`'s created by invoking `DbtCli.cli(...)` now have a method `.is_successful()`, which returns a boolean representing whether the underlying CLI process executed the dbt command successfully.
  - Descriptions of assets generated by `@dbt_assets` can now be customized by overriding `DbtManifest.node_info_to_description`.
  - IO Managers can now be configured on `@dbt_assets`.

### Documentation

- New guide on using Dagster to manage machine learning pipelines

### Dagster Cloud

- Added support for streaming upload of compute logs to Dagster Cloud
- The ECS agent now supports setting `server_ecs_tags` and `run_ecs_tags` that apply to each service or task created by the agent. See [the docs](https://docs.dagster.io/dagster-cloud/deployment/agents/amazon-ecs/configuration-reference#amazon-ecs-agent-configuration-reference) for more information.
- Fixed run filtering for calls to `instance.get_run_partition_data` in Dagster Cloud.

# 1.3.7 (core) / 0.19.7 (libraries)

### New

- Adding a `.env` file in the working directory when running `dagster dev` can now be used for Dagster system variables like `DAGSTER_HOME` or environment variables referenced in your `dagster.yaml` file using an `env:` key. Previously, setting a `.env` file only worked for environment variables referenced in your Dagster code.
- When using the GraphQL Python client, `submit_job_execution` can now take in a `RunConfig` object. Previously, it could only take a Python dictionary with the run configuration.
- Asset backfills can now be canceled via a button in the UI. This will terminate unfinished runs and prevent new runs from being queued.
- Introduced a new user setting which allows automatically expanding default config for jobs in the launchpad.
- [dagit] Dagit now supports displaying a Polars tag on the asset graph.

### Bugfixes

- Fixed an issue where setting a resource in an op didn’t work if the Dagster job was only referenced within a schedule or sensor and wasn’t included in the `jobs` argument to `Definitions`.
- [dagster-slack][dagster-pagerduty][dagster-msteams][dagster-airflow] Fixed issue where pre-built sensors and hooks which created urls to the runs page in the UI would use the old `/instance/runs` path instead of the new `/runs`.

### Community Contributions

- [dagster-databricks] Added a configurable resource key to `create_databricks_run_now_op`, thanks @srggrs!

# 1.3.6 (core) / 0.19.6 (libraries)

### New

- Added an experimental `dagster code-server start` command that can be used to launch a code server, much like `dagster api grpc`. Unlike `dagster api grpc`, however, `dagster code-server start` runs the code in a subprocess, so it can reload code from the Dagster UI without needing to restart the command. This can be useful for jobs that load code from some external source and may want to reload job definitions without restarting the process.
- Added a new `sensors.num_submit_workers` key to `dagster.yaml` that can be used to decrease latency when a sensor emits multiple run requests within a single tick. See [the docs](https://docs.dagster.io/deployment/dagster-instance#sensor-evaluation) for more information.
- [dagster-k8s] The `k8s_job_executor` can now be used to launch each step of a job in its own Kubernetes, pod, even if the Dagster deployment is not using the `K8sRunLauncher` to launch each run in its own Kubernetes pod.
- [ui] When viewing a list of schedules or sensors in Overview or on individual code locations, it is now possible to filter by running state.
- [ui] A new experimental asset overview page is available via user settings.

### Bugfixes

- Fixed issue where asset jobs featuring a subset of a larger multi_asset could be rendered as an op-based job.
- Fixed an issue where Pythonic IO managers could not be passed to the `io_manager_def` param on an asset.
- Fixed an issue where late-binding an executor to a job, such as providing one to Definitions, would not correctly update the config schema.
- [dagster-k8s] Fixed an issue where setting `maxResumeRunAttempts` to null in the helm chart would cause it to be set to a default value of 3 instead of disabling run retries.
- [dagster-k8s] Fixed an issue where the `k8s_job_executor` would sometimes fail with a 409 Conflict error after retrying the creation of a Kubernetes pod for a step, due to the job having already been created during a previous attempt despite raising an error.
- [dagster-dbt] Fixed an issue where dbt logs were not being captured when invoking dbt commands using the resource.
- [dagster-dbt] Fixed an issue where if `op_name` was passed to `load_assets_from_dbt_manifest`, and a `select` parameter was specified, a suffix would be appended to the desired op name.
- [ui] Fixed an issue where using a path prefix for `dagit` would lead to JavaScript bundle loading errors.
- [ui] Resizing the viewport while viewing the Run timeline now correctly resizes the timeline and its contents.
- [ui] Ctrl-scroll to zoom the DAG view, and shift-scroll to pan horizontally now work on all platforms and an instructional tooltip explains the zoom interaction.

### Experimental

- [dagster-dbt] Added a new implementation of the dbt Resource, `DbtCli`, in `dagster_dbt.cli`. This new resource only support `dbt-core>=1.4.0`.
- [dagster-dbt] Added a new decorator `@dbt_assets` in `dagster_dbt.asset_decorator` that allows you to specify a compute function for a selected set of dbt assets that loaded as an `AssetsDefinition`.

### Documentation

- [dagster-duckdb] New guide and API reference page for the DuckDB I/O managers and resource
- [rbac] - Added documentation for the new [Dagster Cloud Teams feature](https://docs.dagster.io/dagster-cloud/account/managing-users/managing-teams) for role-based access control (RBAC). We’ve also revamped the documentation for Dagster Cloud user roles and permissions - [check it out here](https://docs.dagster.io/dagster-cloud/account/managing-users/managing-user-roles-permissions).
- Fixed a typo in the "Using Environment Variables and Secrets" guide (thanks **[snikch](https://github.com/snikch)!**)

### Dagster Cloud

- Fixed a bug in the multi-asset sensor where using context methods to fetch materializations by partition would cause a timeout.
- The ECS agent can now configure sidecars to be included with the tasks that the agent launches. See [the docs](https://docs.dagster.io/dagster-cloud/deployment/agents/amazon-ecs/configuration-reference#amazon-ecs-agent-configuration-reference) for more information.

# 1.3.5 (core) / 0.19.5 (libraries)

### New

- A new `max_materializations_per_minute` parameter (with a default of 1) to `AutoMaterializationPolicy.eager()` and `AutoMaterializationPolicy.lazy()` allows you to set bounds on the volume of work that may be automatically kicked off for each asset. To restore the previous behavior, you can explicitly set this limit to `None`.
- `DailyPartitionsDefinition`, `HourlyPartitionsDefinition`, `WeeklyPartitionsDefinition`, and `MonthlyPartitionsDefinition` now support and `end_date` attribute.
- [ui] When GraphQL requests time out with 504 errors, a toaster message is now shown indicating the error, instead of failing silently.
- [dagster-snowflake] The Snowflake I/O managers now support authentication via unencrypted private key.

### Bugfixes

- When using `AutoMaterializePolicy`s or `build_asset_reconciliation_sensor`, a single new data version from an observable source asset could trigger multiple runs of the downstream assets. This has been fixed.
- Fixed a bug with pythonic resources where raw run config provided to a resource would be ignored.
- We previously erroneously allowed the use of `EnvVar` and `IntEnvVar` within raw run config - although they just returned the name of the env var rather than retrieve its value. This has been fixed to error directly.
- [ui] Fixed an issue in the left navigation where code locations with names with URI-encodable characters (e.g. whitespace) could not be expanded.
- [ui] Fixed an issue where the time shown on the Runs page when a run was starting was shown in an incorrect timezone.
- [dagster-dbt] Fixed an issue where selecting models by `*` was being interpreted as glob pattern, rather than as a dbt selector argument. We now explicitly set the default selection pattern as `fqn:*`.
- [dagster-cloud cli] Fixed and issue where `dagster-cloud serverless deploy` did not create a unique image tag if the `--image` tag was not specified.

### Community Contributions

- Added an option to specify `op_name` on `load_assets_from_dbt_project` and `load_assets_from_dbt_manifest` (thanks @wkeifenheim!)
- [Helm] Added support for connecting to code servers over SSL (thanks @jrouly!)

### Documentation

- New tutorial section on how to manage your own I/O and control over dependencies

### Dagster Cloud

- Added the ability to assign users to teams. A team is a group of users with a shared set of permissions. See [the docs](https://docs.dagster.io/dagster-cloud/account/managing-users/managing-teams) for more information.

# 1.3.4 (core) / 0.19.4 (libraries)

### New

- Run monitoring will now detect runs that are stuck in a CANCELING state due to an error during termination and move them into CANCELED. See the [docs](https://docs.dagster.io/deployment/run-monitoring#run-cancelation-timeouts) for more information.
- `TimeWindowPartitionMapping` objects are now current-time aware. Subsequently, only upstream/downstream partitions existent at the current time are returned.
- `ExecuteJobResult` was renamed to `JobExecutionResult` (`ExecuteJobResult` remains a deprecated alias)
- New `AssetSelection.key_prefixes` method allows matching asset keys starting with a provided prefix.
- [dagster-airflow] persistent database URI can now be passed via environment variable
- [dagster-azure] New `ConfigurablePickledObjectADLS2IOManager` that uses pythonic config
- [dagster-fivetran] Fivetran connectors that are broken or incomplete are now ignored
- [dagster-gcp] New `DataProcResource` follows the Pythonic resource system. The existing `dataproc_resource` remains supported.
- [dagster-k8s] The K8sRunLauncher and k8s_job_executor will now retry the api call to create a Kubernetes Job when it gets a transient error code (500, 503, 504, or 401).
- [dagster-snowflake] The `SnowflakeIOManager` now supports `private_key`s that have been `base64` encoded to avoid issues with newlines in the private key. Non-base64 encoded keys are still supported. See the `SnowflakeIOManager` documentation for more information on `base64` encoded private keys.
- [ui] Unpartitioned assets show up on the backfill page
- [ui] On the experimental runs page you can open the “view all tags” dialog of a row by pressing the hotkey ‘t’ while hovering that row.
- [ui] The “scroll-to-pan” feature flag has been removed, and scroll-to-pan is now default functionality.

### Bugfixes

- The server side polling for events during a live run has had its rate adjusted and no longer uses a fixed interval.
- [dagster-postgres] Fixed an issue where primary key constraints were not being created for the `kvs`, `instance_info`, and `daemon_hearbeats` table for existing Postgres storage instances that were migrating from before `1.2.2`. This should unblock users relying on the existence of a primary key constraint for replication.
- Fixed a bug that could cause incorrect counts to be shown for missing asset partitions when partitions are in progress
- Fixed an issue within `SensorResult` evaluation where multipartitioned run requests containing a dynamic partition added in a dynamic partitions request object would raise an invalid partition key error.
- [ui] When trying to terminate a queued or in-progress run from a Run page, forcing termination was incorrectly given as the only option. This has been fixed, and these runs can now be terminated normally.
- [ui] Fixed an issue on the asset job partitions page where an infinite recursion error would be thrown when using `TimeWindowPartitionMapping`.
- [dagster-databricks] Polling for the status of skipped Databricks runs now properly terminates.

### Deprecations

- `ExecuteJobResult` is now a deprecated alias for the new name, `JobExecutionResult`.

### Community Contributions

- [dagster-airbyte] When supplying an `airbyte_resource` to `load_assets_from_connections` , you may now provide an instance of the `AirbyteResource` class, rather than just `airbyte_resource.configured(...)` (thanks **[@joel-olazagasti](https://github.com/joel-olazagasti)!)**
- [dagster-airbyte] Fixed an issue connecting to destinations that support normalization (thanks [@nina-j](https://github.com/nina-j)!)
- Fix an error in the docs code snippets for IO managers (thanks [out-running-27](https://github.com/out-running-27)!)
- Added [an example](https://github.com/dagster-io/dagster/tree/master/examples/project_analytics) to show how to build the Dagster's Software-Defined Assets for an analytics workflow with different deployments for a local and prod environment. (thanks [@PedramNavid](https://github.com/PedramNavid)!)
- [dagster-celery] Fixed an issue where the `dagster-celery` CLI accepted an inconsistent configuration format - it now matches the same format as the `celery_executor`. Thanks [@boenshao](https://github.com/boenshao)!

### Documentation

- New “Managing your own I/O” tutorial section and other minor tutorial improvements.

### Dagster Cloud

- The ECS agent will now display task logs and other debug information when a code location fails to start up.
- You can now set `ecs_timeout` in your ECS user code launcher config to extend how long the ECS agent polls for new code servers to start. Extending this timeout is useful if your code server takes an unusually long time to start up - for example, because it uses a very large image.
- Added support for running the Dagster Cloud Kubernetes agent in a cluster using istio.

# 1.3.3 (core) / 0.19.3 (libraries)

### New

- `load_assets_from_package_module` and the other core `load_assets_from_` methods now accept a `source_key_prefix` argument, which allows applying a key prefix to all the source assets that are loaded.
- `OpExecutionContext` now has an `asset_partitions_time_window_for_input` method.
- `RunFailureSensorContext` now has a `get_step_failure_events` method.
- The Pythonic resource system now supports a set of lifecycle hooks which can be used to manage setup and teardown:

  ```python
  class MyAPIClientResource(ConfigurableResource):
      api_key: str
      _internal_client: MyAPIClient = PrivateAttr()

      def setup_for_execution(self, context):
          self._internal_client = MyAPIClient(self.api_key)

      def get_all_items(self):
          return self._internal_client.items.get()
  ```

- Added support for specifying input and output config on `ConfigurableIOManager`.
- `QueuedRunCoordinator` and `SubmitRunContext` are now exposed as public dagster exports.
- [ui] Downstream cross-location dependencies of all source assets are now visible on the asset graph. Previously these dependencies were only displayed if the source asset was defined as a regular asset.
- [ui] A new filtering experience is available on the Runs page after enabling feature flag “Experimental Runs table view with filtering”.
- [dagster-aws] Allow the S3 compute log manager to specify a `show_url_only: true` config option, which will display a URL to the S3 file in dagit, instead of the contents of the log file.
- [dagster-aws] `PickledObjectS3IOManager` now fully supports loading partitioned inputs.
- [dagster-azure] `PickedObjectADLS2IOManager` now fully supports loading partitioned inputs.
- [dagster-gcp] New `GCSResource` and `ConfigurablePickledObjectGCSIOManager` follow the Pythonic resource system. The existing `gcs_resource` and `gcs_pickle_io_manager` remain supported.
- [dagster-gcp] New `BigQueryResource` follows the Pythonic resource system. The existing `bigquery_resource` remains supported.
- [dagster-gcp] `PickledObjectGCSIOManager` now fully supports loading partitioned inputs.
- [dagster-postgres] The event watching implementation has been moved from listen/notify based to the polling watcher used by MySQL and SQLite.
- [dagster-slack] Add `monitor_all_repositories` to `make_slack_on_run_failure_sensor`, thanks @danielgafni!
- [dagster-snowflake] New `SnowflakeResource` follows the Pythonic resource system. The existing `snowflake_resource` remains supported.

### Bugfixes

- Multi-asset sensor context methods for partitions now work when partitioned source assets are targeted.
- Previously, the asset backfill page would incorrectly display negative counts for assets with upstream failures. This has been fixed.
- In cases where there is an asset which is upstream of one asset produced by a subsettable multi-asset, but downstream of another, Dagster will automatically subset the multi-asset to resolve the underlying cycle in the op dependency graph. In some cases, this process could omit some of the op dependencies, resulting in incorrect execution order. This has been fixed.
- Fixed an issue with `AssetMetadataValue.value` that would cause an infinite recursion error.
- Fixed an issue where observable source assets would show up in the asset graph of jobs that did not include them.
- Fixed an issue with directly invoking an op or asset with a Pythonic config object with a discriminated union did not work properly.
- Fixes a bug where sensors attached to jobs that rely on resources from Definitions were not provided with the required resource definition.

### Dagster Cloud

- `volumes` and `volumeMounts` values have been added to the agent helm chart.

### Experimental

- [dagster-airbyte] `load_assets_from_airbyte_instance` and `load_assets_from_airbyte_project` now take a `connection_to_auto_materialize_policy_fn` for setting `AutoMaterializePolicy`s on Airbyte assets
- [dagster-airbyte] Introduced experimental support for Airbyte Cloud. See the [using Dagster with Airbyte Cloud docs for more information](https://docs.dagster.io/integrations/airbyte-cloud).

### Documentation

- Ever wanted to know more about the files in Dagster projects, including where to put them in your project? Check out the new [Dagster project files reference](https://docs.dagster.io/getting-started/project-file-reference) for more info!
- We’ve made some improvements to the sidenav / information architecture of our docs!
  - The **Guides** section now contains several new categories, including **Working with data assets** and **Working with tasks**
  - The **Community** section is now under **About**
- The Backfills concepts page now includes instructions on how to launch backfills that target ranges of partitions in a single run.

# 1.3.2 (core) / 0.19.2 (libraries)

### New

- Added performance improvements for yielding time-partitioned run requests.
- The asset backfill page now displays targeted assets in topological order.
- Replicas can now be specified on Hybrid ECS and K8s agents. In ECS, use the `NumReplicas` parameter on the agent template in CloudFormation, or the `dagsterCloudAgent.replicas` field in Helm.
- Zero-downtime agent updates can now be configured for the ECS agent. Just set the `enableZeroDowntimeDeploys` parameter to true in the CloudFormation stack for your agent.
- The `AssetsDefinition.from_graph`, as well as the`@graph_asset` and `@graph_multi_asset` decorators now support specifying `AutoMaterializePolicy`s.
- [dagstermill] Pythonic resource variant of the dagstermill I/O manager is now available.
- [dagster-duckdb] New DuckDBResource for connecting to and querying DuckDB databases.
- [ui] Sensor / Schedule overview pages now allow you to select and start/stop multiple sensors/schedules at once.
- [ui] Performance improvements to global search for big workspaces.

### Bugfixes

- `async def` ops/assets no longer prematurely finalize async generators during execution.
- In some cases, the AutoMaterialize Daemon (and the `build_asset_reconciliation_sensor`) could incorrectly launch new runs for partitions that already had an in-progress run. This has been fixed.

### Breaking Changes

- Yielding run requests for experimental dynamic partitions via `run_request_for_partition` now throws an error. Instead, users should yield directly instantiated run requests via `RunRequest(partition_key=...)`.
- `graph_asset` and `graph_multi_asset` now support specifying `resource_defs` directly (thanks [@kmontag42](https://github.com/KMontag42))!

### Community Contributions

- A new `node_info_to_auto_materialize_policy_fn` param added to `load_assets_from_dbt_*` functions. (thanks [@askvinni](https://github.com/askvinni))!
- Added `partition_key` field to `RunStatusSensorContext` (thanks [@pdstrnadJC](https://github.com/pdstrnadJC))!

### Experimental

- For multi-partitioned assets with a time dimension, the auto-materialize policy now only kicks off materializations for the latest time partition window. Previously, all partitions would be targeted.
- Added performance improvements to the multi-asset sensor context’s `latest_materialization_records_by_key` method.
- The GraphQL API for launching a backfill no longer errors when the backfill targets assets instead of a job and the `allPartitions` argument is provided.

### Documentation

- Fixed a few typos in various guides.
- Fixed a formatting issue in the Automating pipelines guide that was causing a 404.

# 1.3.1 (core) / 0.19.1 (libraries)

### New

- Performance improvements when evaluating time-partitioned run requests within sensors and schedules.
- [ui] Performance improvements when loading the asset catalog and launchpad for deployments with many time-partitioned assets.

### Bugfixes

- Fixed an issue where loading a Definitions object that included sensors attached to multiple jobs would raise an error.
- Fixed a bug in which Pythonic resources would produce underlying resource values that would fail reference equality checks. This would lead to a conflicting resource version error when using the same Pythonic resource in multiple places.

# 1.3.0 (core) / 0.19.0 (libraries) "Smooth Operator"

## **Major Changes since 1.2.0 (core) / 0.18.0 (libraries)**

### Core

- **Auto-materialize policies replace the asset reconciliation sensor** - We significantly renovated the APIs used for specifying which assets are scheduled declaratively. Compared to `build_asset_reconciliation_sensor`s , `AutoMaterializePolicy` works across code locations, as well as allow you to customize the conditions under which each asset is auto-materialized. [[docs](https://docs.dagster.io/concepts/assets/asset-auto-execution)]
- **Asset backfill page** - A new page in the UI for monitoring asset backfills shows the progress of each asset in the backfill.
- **Clearer labels for tracking changes to data and code** - Instead of the opaque “stale” indicator, Dagster’s UI now indicates whether code, upstream data, or dependencies have changed. When assets are in violation of their `FreshnessPolicy`s, Dagster’s UI now marks them as “overdue” instead of “late”.
- **Auto-materialization and observable source assets** - Assets downstream of an observable source asset now use the source asset observations to determine whether upstream data has changed and assets need to be materialized.
- **Pythonic Config and Resources** - The set of APIs [introduced in 1.2](#120-core--0180-libraries) is no longer experimental [[community memo](https://dagster.io/blog/pythonic-config-and-resources)]. Examples, integrations, and documentation have largely ported to the new APIs. Existing resources and config APIs will continue to be supported for the foreseeable future. Check out [migration guide](https://docs.dagster.io/guides/dagster/migrating-to-pythonic-resources-and-config) to learn how to incrementally adopt the new APIs.

### Docs

- **Improved run concurrency docs** - You asked (in support), and we answered! This [new guide](https://docs.dagster.io/guides/limiting-concurrency-in-data-pipelines) is a one-stop-shop for understanding and implementing run concurrency, whether you’re on Dagster Cloud or deploying to your own infrastructure.
- **Additions to the Intro to Assets tutorial** - We’ve added two new sections to the assets tutorial, focused on [scheduling](https://docs.dagster.io/tutorial/scheduling-your-pipeline) and [I/O](https://docs.dagster.io/tutorial/saving-your-data). While we’re close to wrapping things up for the tutorial revamp, we still have a few topics to cover - stay tuned!
- **New guide about building machine learning pipelines** - Many of our users learn best by example - [this guide](https://docs.dagster.io/guides/dagster/ml-pipeline) is one way we’re expanding our library of examples. In this guide, we walk you through building a simple machine learning pipeline using Dagster.
- **Re-organized Dagster Cloud docs** - We overhauled how the Dagster Cloud docs are organized, bringing them more in line with the UI.

## **Since 1.2.7 (core) / 0.18.7 (libraries)**

### New

- Long-running runs can now be terminated after going over a set runtime. See the [run termination docs](https://docs.dagster.io/deployment/run-monitoring#general-run-timeouts) to learn more.
- Adds a performance improvement to partition status caching for multi-partitioned assets containing a time dimension.
- [ui] Asset groups are now included in global search.
- [ui] Assets in the asset catalog have richer status information that matches what is displayed on the asset graph.
- [dagster-aws] New `AthenaClientResource`, `ECRPublicResource`, `RedshiftClientResource`, `S3Resource`, `S3FileManagerResource`, `ConfigurablePickledObjectS3IOManager`, `SecretsManagerResource` follow Pythonic resource system. The existing APIs remain supported.
- [dagster-datadog] New `DatadogResource` follows Pythonic resource system. The existing `datadog_resource` remains supported.
- [dagster-ge] New `GEContextResource` follows Pythonic resource system. The existing `ge_context_resource` remains supported.
- [dagster-github] New `GithubResource` follows Pythonic resource system. The existing `github_resource` remains supported.
- [dagster-msteams] New `MSTeamsResource` follows Pythonic resource system. The existing `msteams_resource` remains supported.
- [dagster-slack] New `SlackResource` follows Pythonic resource system. The existing `slack_resource` remains supported.

### Bugfixes

- Fixed an issue where using `pdb.set_trace` no longer worked when running Dagster locally using `dagster dev` or `dagit`.
- Fixed a regression where passing custom metadata on `@asset` or `Out` caused an error to be thrown.
- Fixed a regression where certain states of the asset graph would cause GQL errors.
- [ui] Fixed a bug where assets downstream of source assets would sometimes incorrectly display a “New data” (previously “stale”) tag for assets with materializations generated from ops (as opposed to SDA materializations).
- [ui] Fixed a bug where URLs for code locations named `pipelines` or `jobs` could lead to blank pages.
- [ui] When configuring a partition-mapped asset backfill, helpful context no longer appears nested within the “warnings” section
- [ui] For observable source assets,the asset sidebar now shows a “latest observation” instead of a “latest materialization”

### Breaking Changes

- By default, resources defined on `Definitions` are now automatically bound to jobs. This will only result in a change in behavior if you a) have a job with no "io_manager" defined in its `resource_defs` and b) have supplied an `IOManager` with key "io_manager" to the `resource_defs` argument of your `Definitions`. Prior to 1.3.0, this would result in the job using the default filesystem-based `IOManager` for the key "io_manager". In 1.3.0, this will result in the "io_manager" supplied to your `Definitions` being used instead. The `BindResourcesToJobs` wrapper, introduced in 1.2 to simulate this behavior, no longer has any effect.
- [dagster-celery-k8s] The default kubernetes namespace for run pods when using the Dagster Helm chart with the `CeleryK8sRunLauncher` is now the same namespace as the Helm chart, instead of the `default` namespace. To restore the previous behavior, you can set the `celeryK8sRunLauncher.jobNamespace` field to the string `default`.
- [dagster-snowflake-pandas] Due to a longstanding issue storing Pandas Timestamps in Snowflake tables, the `SnowflakePandasIOManager` has historically converted all timestamp data to strings before storing it in Snowflake. Now, it will instead ensure that timestamp data has a timezone, and if not, attach the UTC timezone. This allows the timestamp data to be stored as timestamps in Snowflake. If you have been storing timestamp data using the `SnowflakePandasIOManager` you can set the `store_timestamps_as_strings=True` configuration to continue storing timestamps as strings. For more information, and instructions for migrating Snowflake tables to use timestamp types, see the Migration Guide.

**Changes to experimental APIs**

- Pythonic Resources and Config
  - Enabled passing `RunConfig` to many APIs which previously would only accept a config dictionary.
  - Enabled passing raw Python objects as resources to many APIs which previously would only accept `ResourceDefinition`.
  - Added the ability to pass `execution` config when constructing a `RunConfig` object.
  - Introduced more clear error messages when trying to mutate state on a Pythonic config or resource object.
  - Improved direct invocation experience for assets, ops, schedules and sensors using Pythonic config and resources. Config and resources can now be passed directly as args or kwargs.
- The `minutes_late` and `previous_minutes_late` properties on the experimental `FreshnesPolicySensorContext` have been renamed to `minutes_overdue` and `previous_minutes_overdue`, respectively.

**Removal of deprecated APIs**

- [previously deprecated, 0.15.0] `metadata_entries` arguments to event constructors have been removed. While `MetadataEntry` still exists and will only be removed in 2.0, it is no longer passable to any Dagster public API — users should always pass a dictionary of metadata values instead.

### Experimental

- Adds a performance improvement to the multi-asset sensor context’s `latest_materialization_records_by_key` function.

### Documentation

- The Google BigQuery [tutorial](https://docs.dagster.io/integrations/bigquery/using-bigquery-with-dagster) and [reference](https://docs.dagster.io/integrations/bigquery/reference) pages have been updated to use the new `BigQueryPandasIOManager` and `BigQueryPySparkIOManager`.
- The Snowflake [tutorial](https://docs.dagster.io/integrations/snowflake/using-snowflake-with-dagster) and [reference](https://docs.dagster.io/integrations/snowflake/reference) pages have been updated to use the new `SnowflakePandasIOManager` and `SnowflakePySparkIOManager`.

### Dagster Cloud

- Previously, when deprovisioning an agent, code location servers were cleaned up in serial. Now, they’re cleaned up in parallel.

# 1.2.7 (core) / 0.18.7 (libraries)

### New

- Resource access (via both `required_resource_keys` and Pythonic resources) are now supported in observable source assets.
- [ui] The asset graph now shows how many partitions of each asset are currently materializing, and blue bands appear on the partition health bar.
- [ui] Added a new page to monitor an asset backfill.
- [ui] Performance improvement for Runs page for runs that materialize large numbers of assets.
- [ui] Performance improvements for Run timeline and left navigation for users with large numbers of jobs or assets.
- [ui] In the run timeline, consolidate “Ad hoc materializations” rows into a single row.
- [dagster-aws] The `EcsRunLauncher` now allows you to customize volumes and mount points for the launched ECS task. See [the API docs](https://docs.dagster.io/_apidocs/libraries/dagster-aws#dagster_aws.ecs.EcsRunLauncher) for more information.
- [dagster-duckdb, dagster-duckdb-pandas, dagster-duckdb-pyspark] New `DuckDBPandasIOManager` and `DuckDBPySparkIOManager` follow Pythonic resource system. The existing `duckdb_pandas_io_manager` and `duckdb_pyspark_io_manager` remain supported.
- [dagster-gcp, dagster-gcp-pandas, dagster-gcp-pyspark] New `BigQueryPandasIOManager` and `BigQueryPySparkIOManager` follow Pythonic resource system. The existing `bigquery_pandas_io_manager` and `bigquery_pyspark_io_manager` remain supported.
- [dagster-gcp] The BigQuery resource now accepts authentication credentials as configuration. If you pass GCP authentication credentials to `gcp_crentials` , a temporary file to store the credentials will be created and the `GOOGLE_APPLICATION_CREDENTIALS` environment variable will be set to the temporary file. When the BigQuery resource is garbage collected, the environment variable will be unset and the temporary file deleted.
- [dagster-snowflake, dagster-snowflake-pandas, dagster-snowflake-pyspark] New `SnowflakePandasIOManager` and `SnowflakePySparkIOManager` follow Pythonic resource system. The existing `snowflake_pandas_io_manager` and `snowflake_pyspark_io_manager` remain supported.

### Bugfixes

- Fixed an issue where `dagster dev` would periodically emit a harmless but annoying warning every few minutes about a gRPC server being shut down.
- Fixed a schedule evaluation error that occurred when schedules returned a `RunRequest(partition_key=...)` object.
- Fixed a bug that caused errors in the asset reconciliation sensor when the event log includes asset materializations with partitions that aren’t part of the asset’s `PartitionsDefinition`.
- Fixed a bug that caused errors in the asset reconciliation sensor when a partitioned asset is removed.
- Fixed an issue where `run_request_for_partition` would incorrectly raise an error for a job with a `DynamicPartitionsDefinition` that was defined with a function.
- Fixed an issue where defining a partitioned job with unpartitioned assets via `define_asset_job` would raise an error.
- Fixed a bug where source asset observations could not be launched from dagit when the asset graph contained partitioned assets.
- Fixed a bug that caused **`__ASSET_JOB has no op named ...`** errors when using automatic run retries.
- [ui] The asset partition health bar now correctly renders partial failed partitions of multi-dimensional assets in a striped red color.
- [ui] Fixed an issue where steps that were skipped due to an upstream dependency failure were incorrectly listed as “Preparing” in the right-hand column of the runs timeline.
- [ui] Fixed markdown base64 image embeds.
- [ui] Guard against localStorage quota errors when storing launchpad config tabs.
- [dagster-aws] Fixed an issue where the `EcsRunLauncher` would fail to launch runs if the `use_current_ecs_task_config` field was set to `False` but no `task_definition` field was set.
- [dagster-k8s] Fixed an issue introduced in 1.2.6 where older versions of the kubernetes Python package were unable to import the package.

### Community Contributions

- The `EcsRunLauncher` now allows you to set a capacity provider strategy and customize the ephemeral storage used for launched ECS tasks. See [the docs](https://docs.dagster.io/deployment/guides/aws#customizing-the-launched-runs-task) for details. Thanks [AranVinkItility](https://github.com/AranVinkItility)!
- Fixed an issue where freshness policies were not being correctly applied to assets with key prefixes defined via `AssetsDefinition.from_op`. Thanks @tghanken for the fix!
- Added the `minimum_interval_seconds` parameter to enable customizing the evaluation interval on the slack run failure sensor, thanks @ldnicolasmay!
- Fixed a docs example and updated references, thanks @NicolasPA!

### Experimental

- The `Resource` annotation for Pythonic resource inputs has been renamed to `ResourceParam` in preparation for the release of the feature in 1.3.
- When invoking ops and assets that request resources via parameters directly, resources can now be specified as arguments.
- Improved various error messages related to Pythonic config and resources.
- If the Resources Dagit feature flag is enabled, they will now show up in the overview page and search.

### Documentation

- Learn how to [limit concurrency in your data pipelines](https://docs.dagster.io/guides/limiting-concurrency-in-data-pipelines) with our new guide!
- Need some help managing a run queue? Check out the new [customizing run queue priority guide](https://docs.dagster.io/guides/customizing-run-queue-priority).
- New tutorial section that adds I/O managers to the tutorial project.

# 1.2.6 (core) / 0.18.6 (libraries)

### Bugfixes

- Fixed a GraphQL resolution error which occurred when retrieving metadata for step failures in the event log.

# 1.2.5 (core) / 0.18.5 (libraries)

### New

- `materialize` and `materialize_to_memory` now both accept a `selection` argument that allows specifying a subset of assets to materialize.
- `MultiPartitionsDefinition` is no longer marked experimental.
- Context methods to access time window partition information now work for `MultiPartitionsDefinition`s with a time dimension.
- Improved the performance of the asset reconciliation sensor when a non-partitioned asset depends on a partitioned asset.
- `load_assets_from_package_module` and similar methods now accept a `freshness_policy`, which will be applied to all loaded assets.
- When the asset reconciliation sensor is scheduling based on freshness policies, and there are observable source assets, the observed versions now inform the data time of the assets.
- `build_sensor_context` and `build_multi_asset_sensor_context` can now take a `Definitions` object in place of a `RepositoryDefinition`
- [UI] Performance improvement for loading asset partition statuses.
- [dagster-aws] `s3_resource` now accepts `use_ssl` and `verify` configurations.

### Bugfixes

- Fixed a bug that caused an error to be raised when passing a multi-asset into the `selection` argument on `define_asset_job`.
- Fixes a graphQL error that displays on Dagit load when an asset’s partitions definition is change from a single-dimensional partitions definition to a `MultiPartitionsDefinition`.
- Fixed a bug that caused backfills to fail when spanning assets that live in different code locations.
- Fixed an error that displays when a code location with a `MultiPartitionsMapping` (experimental) is loaded.
- Fixed a bug that caused errors with invalid `TimeWindowPartitionMapping`s to not be bubbled up to the UI.
- Fixed an issue where the scheduler would sometimes incorrectly handle spring Daylight Savings Time transitions for schedules running at 2AM in a timezone other than UTC.
- Fixed an issue introduced in the 1.2.4 release where running `pdb` stopped working when using dagster dev.
- Fixed an issue where it is was possible to create `AssetMaterialization` objects with a null `AssetKey`.
- Previously, if you had a `TimeWindowPartitionsDefinition` with a non-standard cron schedule, and also provided a `minute_of_hour` or similar argument in `build_schedule_from_partitioned_job`. Dagster would silently create the wrong cron expression. It now raises an error.
- The asset reconciliation sensor now no longer fails when the event log contains materializations that contain partitions that aren’t contained in the asset’s `PartitionsDefinition`. These partitions are now ignored.
- Fixed a regression that prevented materializing dynamically partitioned assets from the UI (thanks [@planvin](https://github.com/planvin)!)
- [UI] On the asset graph, the asset health displayed in the sidebar for the selected asset updates as materializations and failures occur.
- [UI] The asset partitions page has been adjusted to make materialization and observation event metadata more clear.
- [UI] Large table schema metadata entries now display within a modal rather than taking up considerable space on the page.
- [UI] Launching a backfill of a partitioned asset with unpartitioned assets immediately upstream no longer shows the “missing partitions” warning.
- [dagster-airflow] fixed a bug in the `PersistentAirflowDatabase` where versions of airflow from 2.0.0 till 2.3.0 would not use the correct connection environment variable name.
- [dagster-census] fixed a bug with the `poll_sync_run` function of`dagster-census` that prevented polling from working correctly (thanks [@ldincolasmay](https://github.com/ldnicolasmay)!)

### Deprecations

- The `run_request_for_partition` method on `JobDefinition` and `UnresolvedAssetJobDefinition` is now deprecated and will be removed in 2.0.0. Instead, directly instantiate a run request with a partition key via `RunRequest(partition_key=...)`.

### Documentation

- Added a missing link to next tutorial section (Thanks Mike Kutzma!)

# 1.2.4 (core) / 0.18.4 (libraries)

### New

- Further performance improvements to the asset reconciliation sensor.
- Performance improvements to asset backfills with large numbers of partitions.
- New `AssetsDefinition.to_source_assets` to method convert a set of assets to `SourceAsset` objects.
- (experimental) Added partition mapping that defines dependency relationships between different `MultiPartitionsDefinitions`.
- [dagster-mlflow] Removed the `mlflow` pin from the `dagster-mlflow` package.
- [ui] Syntax highlighting now supported in rendered markdown code blocks (from metadata).

### Bugfixes

- When using `build_asset_reconciliation_sensor`, in some cases duplicate runs could be produced for the same partition of an asset. This has been fixed.
- When using Pythonic configuration for resources, aliased field names would cause an error. This has been fixed.
- Fixed an issue where `context.asset_partitions_time_window_for_output` threw an error when an asset was directly invoked with `build_op_context`.
- [dagster-dbt] In some cases, use of ephemeral dbt models could cause the dagster representation of the dbt dependency graph to become incorrect. This has been fixed.
- [celery-k8s] Fixed a bug that caused JSON deserialization errors when an Op or Asset emitted JSON that doesn't represent a `DagsterEvent`.
- Fixed an issue where launching a large backfill while running `dagster dev` would sometimes fail with a connection error after running for a few minutes.
- Fixed an issue where `dagster dev` would sometimes hang when running Dagster code that attempted to read in input via stdin.
- Fixed an issue where runs that take a long time to import code would sometimes continue running even after they were stopped by [run monitoring](https://docs.dagster.io/deployment/run-monitoring#run-monitoring) for taking too long to start.
- Fixed an issue where `AssetSelection.groups()` would simultaneously select both source and regular assets and consequently raise an error.
- Fixed an issue where `BindResourcesToJobs` would raise errors encapsulating jobs which had config specified at definition-time.
- Fixed Pythonic config objects erroring when omitting optional values rather than specifying `None`.
- Fixed Pythonic config and resources not supporting Enum values.
- `DagsterInstance.local_temp` and `DagsterInstance.ephemeral` now use object instance scoped local artifact storage temporary directories instead of a shared process scoped one, removing a class of thread safety errors that could manifest on initialization.
- Improved direct invocation behavior for ops and assets which specify resource dependencies as parameters, for instance:

  ```python
  class MyResource(ConfigurableResource):
      pass

  @op
  def my_op(x: int, y: int, my_resource: MyResource) -> int:
      return x + y

  my_op(4, 5, my_resource=MyResource())
  ```

- [dagster-azure] Fixed an issue with an AttributeError being thrown when using the async `DefaultAzureCredential` (thanks [@mpicard](https://github.com/mpicard))
- [ui] Fixed an issue introduced in 1.2.3 in which no log levels were selected by default when viewing Run logs, which made it appear as if there were no logs at all.

### Deprecations

- The `environment_vars` argument to `ScheduleDefinition` is deprecated (the argument is currently non-functional; environment variables no longer need to be whitelisted for schedules)

### Community Contributions

- Typos fixed in [CHANGES.md](http://CHANGES.md) (thanks [@fridiculous](https://github.com/fridiculous))
- Links to telemetry docs fixed (thanks [@Abbe98](https://github.com/Abbe98))
- `--path-prefix` can now be supplied via Helm chart (thanks [@mpicard](https://github.com/mpicard))

### Documentation

- New machine learning pipeline with Dagster guide
- New example of multi-asset conditional materialization
- New tutorial section about scheduling
- New images on the Dagster README

# 1.2.3 (core) / 0.18.3 (libraries)

### New

- Jobs defined via `define_asset_job` now auto-infer their partitions definitions if not explicitly defined.
- Observable source assets can now be run as part of a job via `define_asset_job`. This allows putting them on a schedule/sensor.
- Added an `instance` property to the `HookContext` object that is passed into [Op Hook](https://docs.dagster.io/concepts/ops-jobs-graphs/op-hooks#op-hooks) functions, which can be used to access the current `DagsterInstance` object for the hook.
- (experimental) Dynamic partitions definitions can now exist as dimensions of multi-partitions definitions.
- [dagster-pandas] New `create_table_schema_metadata_from_dataframe` function to generate a `TableSchemaMetadataValue` from a Pandas DataFrame. Thanks [@AndyBys](https://github.com/AndyBys)!
- [dagster-airflow] New option for setting `dag_run` configuration on the integration’s database resources.
- [ui] The asset partitions page now links to the most recent failed or in-progress run for the selected partition.
- [ui] Asset descriptions have been moved to the top in the asset sidebar.
- [ui] Log filter switches have been consolidated into a single control, and selected log levels will be persisted locally so that the same selections are used by default when viewing a run.
- [ui] You can now customize the hour formatting in timestamp display: 12-hour, 24-hour, or automatic (based on your browser locale). This option can be found in User Settings.

### Bugfixes

- In certain situations a few of the first partitions displayed as “unpartitioned” in the health bar despite being materialized. This has now been fixed, but users may need to run `dagster asset wipe-partitions-status-cache` to see the partitions displayed.
- Starting `1.1.18`, users with a gRPC server that could not access the Dagster instance on user code deployments would see an error when launching backfills as the instance could not instantiate. This has been fixed.
- Previously, incorrect partition status counts would display for static partitions definitions with duplicate keys. This has been fixed.
- In some situations, having SourceAssets could prevent the `build_asset_reconciliation_sensor` from kicking off runs of downstream assets. This has been fixed.
- The `build_asset_reconciliation_sensor` is now much more performant in cases where unpartitioned assets are upstream or downstream of static-partitioned assets with a large number of partitions.
- [dagster-airflow] Fixed an issue were the persistent Airflow DB resource required the user to set the correct Airflow database URI environment variable.
- [dagster-celery-k8s] Fixed an issue where run monitoring failed when setting the `jobNamespace` field in the Dagster Helm chart when using the `CeleryK8sRunLauncher`.
- [ui] Filtering on the asset partitions page no longer results in keys being presented out of order in the left sidebar in some scenarios.
- [ui] Launching an asset backfill outside an asset job page now supports partition mapping, even if your selection shares a partition space.
- [ui] In the run timeline, date/time display at the top of the timeline was sometimes broken for users not using the `en-US` browser locale. This has been fixed.

# 1.2.2 (core) / 0.18.2 (libraries)

### New

- Dagster is now tested on Python 3.11.
- Users can now opt in to have resources provided to `Definitions` bind to their jobs. Opt in by wrapping your job definitions in `BindResourcesToJobs`. This will become the default behavior in the future.

  ```python
  @op(required_resource_keys={"foo"})
  def my_op(context)
      print(context.foo)

  @job
  def my_job():
    my_op()

  defs = Definitions(
      jobs=BindResourcesToJobs([my_job])
      resources={"foo": foo_resource}
  ```

- Added `dagster asset list` and `dagster asset materialize` commands to Dagster’s command line interface, for listing and materializing software-defined assets.
- `build_schedule_from_partitioned_job` now accepts jobs partitioned with a `MultiPartitionsDefinition` that have a time-partitioned dimension.
- Added `SpecificPartitionsPartitionMapping`, which allows an asset, or all partitions of an asset, to depend on a specific subset of the partitions in an upstream asset.
- `load_asset_value` now supports `SourceAsset`s.
- [ui] Ctrl+K has been added as a keyboard shortcut to open global search.
- [ui] Most pages with search bars now sync the search filter to the URL, so it’s easier to bookmark views of interest.
- [ui] In the run logs table, the timestamp column has been moved to the far left, which will hopefully allow for better visual alignment with op names and tags.
- [dagster-dbt] A new `node_info_to_definition_metadata_fn` to `load_assets_from_dbt_project` and `load_assets_from_dbt_manifest` allows custom metadata to be attached to the asset definitions generated from these methods.
- [dagster-celery-k8s] The Kubernetes namespace that runs using the `CeleryK8sRunLauncher` are launched in can now be configured by setting the `jobNamespace` field in the Dagster Helm chart under `celeryK8sRunLauncherConfig`.
- [dagster-gcp] The BigQuery I/O manager now accepts `timeout` configuration. Currently, this configuration will only be applied when working with Pandas DataFrames, and will set the number of seconds to wait for a request before using a retry.
- [dagster-gcp] [dagster-snowflake] [dagster-duckdb] The BigQuery, Snowflake, and DuckDB I/O managers now support self-dependent assets. When a partitioned asset depends on a prior partition of itself, the I/O managers will now load that partition as a DataFrame. For the first partition in the dependency sequence, an empty DataFrame will be returned.
- [dagster-k8s] `k8s_job_op` now supports running Kubernetes jobs with more than one pod (Thanks @Taadas).

### Bugfixes

- Fixed a bug that causes backfill tags that users set in the UI to not be included on the backfill runs, when launching an asset backfill.
- Fixed a bug that prevented resume from failure re-execution for jobs that contained assets and dynamic graphs.
- Fixed an issue where the asset reconciliation sensor would issue run requests for assets that were targeted by an active asset backfill, resulting in duplicate runs.
- Fixed an issue where the asset reconciliation sensor could issue runs more frequently than necessary for assets with FreshnessPolicies having intervals longer than 12 hours.
- Fixed an issue where `AssetValueLoader.load_asset_value()` didn’t load transitive resource dependencies correctly.
- Fixed an issue where constructing a `RunConfig` object with optional config arguments would lead to an error.
- Fixed the type annotation on `ScheduleEvaluationContext.scheduled_execution_time` to not be `Optional`.
- Fixed the type annotation on `OpExecutionContext.partition_time_window` \*\*\*\*(thanks @elben10).
- `InputContext.upstream_output.log` is no longer `None` when loading a source asset.
- [Pydantic type constraints](https://docs.pydantic.dev/usage/types/#constrained-types) are now supported by the [Pythonic config](https://docs.dagster.io/guides/dagster/pythonic-config) API.
- An input resolution bug that occurred in certain conditions when composing graphs with same named ops has been fixed.
- Invoking an op with collisions between positional args and keyword args now throws an exception.
- `async def` ops are now invoked with `asyncio.run`.
- `TimeWindowPartitionDefinition` now throws an error at definition time when passed an invalid cron schedule instead of at runtime.
- [ui] Previously, using dynamic partitions with assets that required config would raise an error in the launchpad. This has been fixed.
- [ui] The lineage tab loads faster and flickers less as you navigate between connected assets in the lineage graph
- [ui] The config YAML editor no longer offers incorrect autcompletion context when you’re beginning a new indented line.
- [ui] When viewing the asset details page for a source asset, the button in the top right correctly reads “Observe” instead of “Materialize”
- [dagster-dbt] Previously, setting a `cron_schedule_timezone` inside of the config for a dbt model would not result in that property being set on the generated `FreshnessPolicy`. This has been fixed.
- [dagster-gcp] Added a fallback download url for the `GCSComputeLogManager` when the session does not have permissions to generate signed urls.
- [dagster-snowflake] In a previous release, functionality was added for the Snowflake I/O manager to attempt to create a schema if it did not already exist. This caused an issue when the schema already existed but the account did not have permission to create the schema. We now check if a schema exists before attempting to create it so that accounts with restricted permissions do not error, but schemas can still be created if they do not exist.

### Breaking Changes

- `validate_run_config` no longer accepts `pipeline_def` or `mode` arguments. These arguments refer to legacy concepts that were removed in Dagster 1.0, and since then there have been no valid values for them.

### Experimental

- Added experimental support for resource requirements in sensors and schedules. Resources can be specified using `required_resource_keys` and accessed through the context or specified as parameters:

  ```python
  @sensor(job=my_job, required_resource_keys={"my_resource"})
  def my_sensor(context):
      files_to_process = context.my_resource.get_files()
  		...

  @sensor(job=my_job)
  def my_sensor(context, my_resource: MyResource):
      files_to_process = my_resource.get_files()
  		...
  ```

### Documentation

- Added a page on asset selection syntax to the Concepts documentation.

# 1.2.1 (core) / 0.18.1 (libraries)

### Bugfixes

- Fixed a bug with postgres storage where daemon heartbeats were failing on instances that had not been migrated with `dagster instance migrate` after upgrading to `1.2.0`.

# 1.2.0 (core) / 0.18.0 (libraries)

## **Major Changes since 1.1.0 (core) / 0.17.0 (libraries)**

### Core

- Added a new `dagster dev` command that can be used to run both Dagit and the Dagster daemon in the same process during local development. [[docs](https://docs.dagster.io/deployment/guides/running-locally)]
- Config and Resources
  - Introduced new Pydantic-based APIs to make defining and using [config](https://docs.dagster.io/guides/dagster/pythonic-config) and [resources](https://docs.dagster.io/guides/dagster/pythonic-resources) easier (experimental). [[Github discussion](https://github.com/dagster-io/dagster/discussions/12510)]
- Repository > Definitions [[docs](https://docs.dagster.io/concepts/code-locations#definitions-versus-repositories)]
- Declarative scheduling
  - The asset reconciliation sensor is now 100x more performant in many situations, meaning that it can handle more assets and more partitions.
  - You can now set **freshness policies on time-partitioned assets**.
  - You can now hover over a stale asset to learn why that asset is considered stale.
- Partitions
  - `DynamicPartitionsDefinition` allows **partitioning assets dynamically** - you can add and remove partitions without reloading your definitions (experimental). [[docs](https://docs.dagster.io/concepts/partitions-schedules-sensors/partitions#dynamically-partitioned-assets)]
  - The asset graph in the UI now displays the number of materialized, missing, and failed partitions for each partitioned asset.
  - Asset partitions can now **depend on earlier time partitions of the same asset**. Backfills and the asset reconciliation sensor respect these dependencies when requesting runs [[example](https://github.com/dagster-io/dagster/discussions/11829)].
  - `TimeWindowPartitionMapping` now accepts `start_offset` and `end_offset` arguments that allow specifying that time partitions depend on earlier or later time partitions of upstream assets [[docs](https://docs.dagster.io/_apidocs/partitions#dagster.TimeWindowPartitionMapping)].
- Backfills
  - Dagster now allows **backfills that target assets with different partitions**, such as a daily asset which rolls up into a weekly asset, as long as the root assets in the selection are partitioned in the same way.
  - You can now choose to pass a **range of asset partitions to a single run** rather than launching a backfill with a run per partition [[instructions](https://github.com/dagster-io/dagster/discussions/11653)].

### Integrations

- **Weights and Biases** - A new integration `dagster-wandb` with [Weights & Biases](https://wandb.ai/site) allows you to orchestrate your MLOps pipelines and maintain ML assets with Dagster. [[docs](https://docs.dagster.io/_apidocs/libraries/dagster-wandb)]
- **Snowflake + PySpark** - A new integration `dagster-snowflake-pyspark` allows you to store and load PySpark DataFrames as Snowflake tables using the `snowflake_pyspark_io_manager`. [[docs](https://docs.dagster.io/integrations/snowflake/reference#storing-and-loading-pyspark-dataframes-in-snowflake)]
- **Google BigQuery** - A new BigQuery I/O manager and new integrations `dagster-gcp-pandas` and `dagster-gcp-pyspark` allow you to store and load Pandas and PySpark DataFrames as BigQuery tables using the `bigquery_pandas_io_manager` and `bigquery_pyspark_io_manager`. [[docs](https://docs.dagster.io/integrations/bigquery)]
- **Airflow** The `dagster-airflow` integration library was bumped to 1.x.x, with that major bump the library has been refocused on enabling migration from Airflow to Dagster. Refer to the docs for an [in-depth migration guide](https://docs.dagster.io/integrations/airflow/migrating-to-dagster).
- **Databricks -** Changes:
  - Added op factories to create ops for running existing Databricks jobs (`create_databricks_run_now_op`), as well as submitting one-off Databricks jobs (`create_databricks_submit_run_op`).
  - Added a [new Databricks guide](https://docs.dagster.io/master/integrations/databricks).
  - The previous `create_databricks_job_op` op factory is now deprecated.

### Docs

- [Automating pipelines guide](https://docs.dagster.io/guides/dagster/automating-pipelines) - Check out the best practices for automating your Dagster data pipelines with this new guide. Learn when to use different Dagster tools, such as schedules and sensors, using this guide and its included cheatsheet.
- [Structuring your Dagster project guide](https://docs.dagster.io/guides/dagster/recommended-project-structure) - Need some help structuring your Dagster project? Learn about our recommendations for getting started and scaling sustainably.
- [Tutorial revamp](https://docs.dagster.io/tutorial) - Goodbye cereals and hello HackerNews! We’ve overhauled our intro to assets tutorial to not only focus on a more realistic example, but to touch on more Dagster concepts as you build your first end-to-end pipeline in Dagster. [Check it out here.](https://docs.dagster.io/tutorial)

Stay tuned, as this is only the first part of the overhaul. We’ll be adding more chapters - including automating materializations, using resources, using I/O managers, and more - in the next few weeks.

## Since 1.1.21 (core) / 0.17.21 (libraries)

### New

- Freshness policies can now be assigned to assets constructed with `@graph_asset` and `@graph_multi_asset`.
- The `project_fully_featured` example now uses the built in DuckDB and Snowflake I/O managers.
- A new “failed” state on asset partitions makes it more clear which partitions did not materialize successfully. The number of failed partitions is shown on the asset graph and a new red state appears on asset health bars and status dots.
- Hovering over “Stale” asset tags in the Dagster UI now explains why the annotated assets are stale. Reasons can include more recent upstream data, changes to code versions, and more.
- [dagster-airflow] support for persisting airflow db state has been added with `make_persistent_airflow_db_resource` this enables support for Airflow features like pools and cross-dagrun state sharing. In particular retry-from-failure now works for jobs generated from Airflow DAGs.
- [dagster-gcp-pandas] The `BigQueryPandasTypeHandler` now uses `google.bigquery.Client` methods `load_table_from_dataframe` and `query` rather than the `pandas_gbq` library to store and fetch DataFrames.
- [dagster-k8s] The Dagster Helm chart now only overrides `args` instead of both `command` and `args` for user code deployments, allowing to include a custom ENTRYPOINT in your the Dockerfile that loads your code.
- The `protobuf<4` pin in Dagster has been removed. Installing either protobuf 3 or protobuf 4 will both work with Dagster.
- [dagster-fivetran] Added the ability to specify op_tags to build_fivetran_assets (thanks @Sedosa!)
- `@graph_asset` and `@graph_multi_asset` now support passing metadata (thanks [@askvinni](https://github.com/askvinni))!

### Bugfixes

- Fixed a bug that caused descriptions supplied to `@graph_asset` and `@graph_multi_asset` to be ignored.
- Fixed a bug that serialization errors occurred when using `TableRecord`.
- Fixed an issue where partitions definitions passed to `@multi_asset` and other functions would register as type errors for mypy and other static analyzers.
- [dagster-aws] Fixed an issue where the EcsRunLauncher failed to launch runs for Windows tasks.
- [dagster-airflow] Fixed an issue where pendulum timezone strings for Airflow DAG `start_date` would not be converted correctly causing runs to fail.
- [dagster-airbyte] Fixed an issue when attaching I/O managers to Airbyte assets would result in errors.
- [dagster-fivetran] Fixed an issue when attaching I/O managers to Fivetran assets would result in errors.

### Database migration

- Optional database schema migrations, which can be run via `dagster instance migrate`:
  - Improves Dagit performance by adding a database index which should speed up job run views.
  - Enables dynamic partitions definitions by creating a database table to store partition keys. This feature is experimental and may require future migrations.
  - Adds a primary key `id` column to the `kvs`, `daemon_heartbeats` and `instance_info` tables, enforcing that all tables have a primary key.

### Breaking Changes

- The minimum `grpcio` version supported by Dagster has been increased to 1.44.0 so that Dagster can support both `protobuf` 3 and `protobuf` 4. Similarly, the minimum `protobuf` version supported by Dagster has been increased to 3.20.0. We are working closely with the gRPC team on resolving the upstream issues keeping the upper-bound `grpcio` pin in place in Dagster, and hope to be able to remove it very soon.
- Prior to 0.9.19, asset keys were serialized in a legacy format. This release removes support for querying asset events serialized with this legacy format. Contact #dagster-support for tooling to migrate legacy events to the supported version. Users who began using assets after 0.9.19 will not be affected by this change.
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

- [dagster-k8s] The experimental [`k8s_job_op`](https://docs.dagster.io/_apidocs/libraries/dagster-k8s#dagster_k8s.k8s_job_op) op and [`execute_k8s_job`](https://docs.dagster.io/_apidocs/libraries/dagster-k8s#dagster_k8s.execute_k8s_job) functions no longer automatically include configuration from a `dagster-k8s/config` tag on the Dagster job in the launched Kubernetes job. To include raw Kubernetes configuration in a `k8s_job_op`, you can set the `container_config`, `pod_template_spec_metadata`, `pod_spec_config`, or `job_metadata` config fields on the `k8s_job_op` (or arguments to the `execute_k8s_job` function).
- [dagster-databricks] The integration has now been refactored to support the official Databricks API.
  - `create_databricks_job_op` is now deprecated. To submit one-off runs of Databricks tasks, you must now use the `create_databricks_submit_run_op`.
  - The Databricks token that is passed to the `databricks_client` resource must now begin with `https://`.

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

### Community Contributions

- Deprecated `iteritems` usage was removed and changed to the recommended `items` within `dagster-snowflake-pandas` (thanks [@sethkimmel3](https://github.com/sethkimmel3))!
- Refactor to simply the new `@asset_graph` decorator (thanks [@simonvanderveldt](https://github.com/simonvanderveldt))!

### Experimental

- User-computed `DataVersions` can now be returned on `Output`
- Asset provenance info can be accessed via `OpExecutionContext.get_asset_provenance`

### Documentation

- The [Asset Versioning and Caching Guide](https://docs.dagster.io/guides/dagster/asset-versioning-and-caching) now includes a section on user-provided data versions
- The community contributions doc block `Picking a github issue` was not correctly rendering, this has been fixed (thanks [@Sedosa](https://github.com/Sedosa))!

# 1.1.21 (core) / 0.17.21 (libraries)

### New

- Further performance improvements for `build_asset_reconciliation_sensor`.
- Dagster now allows you to backfill asset selections that include mapped partition definitions, such as a daily asset which rolls up into a weekly asset, as long as the root assets in your selection share a partition definition.
- Dagit now includes information about the cause of an asset’s staleness.
- Improved the error message for non-matching cron schedules in `TimeWindowPartitionMapping`s with offsets. (Thanks Sean Han!)
- [dagster-aws] The EcsRunLauncher now allows you to configure the `runtimePlatform` field for the task definitions of the runs that it launches, allowing it to launch runs using Windows Docker images.
- [dagster-azure] Add support for DefaultAzureCredential for adls2_resource (Thanks Martin Picard!)
- [dagster-databricks] Added op factories to create ops for running existing Databricks jobs (`create_databricks_run_now_op`), as well as submitting one-off Databricks jobs (`create_databricks_submit_run_op`). See the [new Databricks guide](https://docs.dagster.io/master/integrations/databricks) for more details.
- [dagster-duckdb-polars] Added a dagster-duckdb-polars library that includes a `DuckDBPolarsTypeHandler` for use with `build_duckdb_io_manager`, which allows loading / storing Polars DataFrames from/to DuckDB. (Thanks Pezhman Zarabadi-Poor!)
- [dagster-gcp-pyspark] New PySpark TypeHandler for the BigQuery I/O manager. Store and load your PySpark DataFrames in BigQuery using `bigquery_pyspark_io_manager`.
- [dagster-snowflake] [dagster-duckdb] The Snowflake and DuckDB IO managers can now load multiple partitions in a single step - e.g. when a non-partitioned asset depends on a partitioned asset or a single partition of an asset depends on multiple partitions of an upstream asset. Loading occurs using a single SQL query and returns a single `DataFrame`.
- [dagster-k8s] The Helm chart now supports the full kubernetes env var spec for user code deployments. Example:

  ```yaml
  dagster-user-deployments:
    deployments:
      - name: my-code
        env:
          - name: FOO
            valueFrom:
              fieldFre:
                fieldPath: metadata.uid
  ```

  If `includeConfigInLaunchedRuns` is enabled, these env vars will also be applied to the containers for launched runs.

### Bugfixes

- Previously, if an `AssetSelection` which matched no assets was passed into `define_asset_job`, the resulting job would target all assets in the repository. This has been fixed.
- Fixed a bug that caused the UI to show an error if you tried to preview a future schedule tick for a schedule built using `build_schedule_from_partitioned_job`.
- When a non-partitioned non-asset job has an input that comes from a partitioned SourceAsset, we now load all partitions of that asset.
- Updated the `fs_io_manager` to store multipartitioned materializations in directory levels by dimension. This resolves a bug on windows where multipartitioned materializations could not be stored with the `fs_io_manager`.
- Schedules and sensors previously timed out when attempting to yield many multipartitioned run requests. This has been fixed.
- Fixed a bug where `context.partition_key` would raise an error when executing on a partition range within a single run via Dagit.
- Fixed a bug that caused the default IO manager to incorrectly raise type errors in some situations with partitioned inputs.
- [ui] Fixed a bug where partition health would fail to display for certain time window partitions definitions with positive offsets.
- [ui] Always show the “Reload all” button on the code locations list page, to avoid an issue where the button was not available when adding a second location.
- [ui] Fixed a bug where users running multiple replicas of dagit would see repeated `Definitions reloaded` messages on fresh page loads.
- [ui] The asset graph now shows only the last path component of linked assets for better readability.
- [ui] The op metadata panel now longer capitalizes metadata keys
- [ui] The asset partitions page, asset sidebar and materialization dialog are significantly smoother when viewing assets with a large number of partitions (100k+)
- [dagster-gcp-pandas] The Pandas TypeHandler for BigQuery now respects user provided `location` information.
- [dagster-snowflake] `ProgrammingError` was imported from the wrong library, this has been fixed. Thanks @herbert-allium!

### Experimental

- You can now set an explicit logical version on `Output` objects rather than using Dagster’s auto-generated versions.
- New `get_asset_provenance` method on `OpExecutionContext` allows fetching logical version provenance for an arbitrary asset key.
- [ui] - you can now create dynamic partitions from the partition selection UI when materializing a dynamically partitioned asset

### Documentation

- Added an example of how to use dynamic asset partitions - in the `examples/assets_dynamic_partitions` folder
- New [tutorial](https://docs.dagster.io/master/integrations/bigquery/using-bigquery-with-dagster) for using the BigQuery I/O manager.
- New [reference page](https://docs.dagster.io/master/integrations/bigquery/reference) for BigQuery I/O manager features.
- New [automating data pipelines guide](https://legacy-versioned-docs.dagster.dagster-docs.io/1.1.21/guides/dagster/automated_pipelines)

# 1.1.20 (core) / 0.17.20 (libraries)

### New

- The new `@graph_asset` and `@graph_multi_asset` decorators make it more ergonomic to define graph-backed assets.
- Dagster will auto-infer dependency relationships between single-dimensionally partitioned assets and multipartitioned assets, when the single-dimensional partitions definition is a dimension of the `MultiPartitionsDefinition`.
- A new `Test sensor` / `Test schedule` button that allows you to perform a dry-run of your sensor / schedule. Check out the docs on this functionality [here](https://docs.dagster.io/master/concepts/partitions-schedules-sensors/sensors#via-dagit) for sensors and [here](https://docs.dagster.io/master/concepts/partitions-schedules-sensors/sensors#via-dagit) for schedules.
- [dagit] Added (back) tag autocompletion in the runs filter, now with improved query performance.
- [dagit] The Dagster libraries and their versions that were used when loading definitions can now be viewed in the actions menu for each code location.
- New `bigquery_pandas_io_manager` can store and load Pandas dataframes in BigQuery.
- [dagster-snowflake, dagster-duckdb] SnowflakeIOManagers and DuckDBIOManagers can now default to loading inputs as a specified type if a type annotation does not exist for the input.
- [dagster-dbt] Added the ability to use the “state:” selector
- [dagster-k8s] The Helm chart now supports the full kubernetes env var spec for Dagit and the Daemon. E.g.

  ```yaml
  dagit:
    env:
      - name: “FOO”
        valueFrom:
          fieldRef:
            fieldPath: metadata.uid
  ```

### Bugfixes

- Previously, graphs would fail to resolve an input with a custom type and an input manager key. This has been fixed.
- Fixes a bug where negative partition counts were displayed in the asset graph.
- Previously, when an asset sensor did not yield run requests, it returned an empty result. This has been updated to yield a meaningful message.
- Fix an issue with a non-partitioned asset downstream of a partitioned asset with self-dependencies causing a GQL error in dagit.
- [dagster-snowflake-pyspark] Fixed a bug where the PySparkTypeHandler was incorrectly loading partitioned data.
- [dagster-k8s] Fixed an issue where [run monitoring](https://docs.dagster.io/deployment/run-monitoring#run-monitoring) sometimes failed to detect that the kubernetes job for a run had stopped, leaving the run hanging.

### Documentation

- Updated contributor docs to reference our new toolchain (`ruff`, `pyright`).
- (experimental) Documentation for the dynamic partitions definition is now added.
- [dagster-snowflake] The Snowflake I/O Manager reference page now includes information on working with partitioned assets.

# 1.1.19 (core) / 0.17.19 (libraries)

### New

- The `FreshnessPolicy` object now supports a `cron_schedule_timezone` argument.
- `AssetsDefinition.from_graph` now supports a `freshness_policies_by_output_name` parameter.
- The `@asset_sensor` will now display an informative `SkipReason` when no new materializations have been created since the last sensor tick.
- `AssetsDefinition` now has a `to_source_asset` method, which returns a representation of this asset as a `SourceAsset`.
- You can now designate assets as inputs to ops within a graph or graph-based job. E.g.

```python
from dagster import asset, job, op

@asset
def emails_to_send():
    ...

@op
def send_emails(emails) -> None:
    ...

@job
def send_emails_job():
    send_emails(emails_to_send.to_source_asset())
```

- Added a `--dagit-host/-h` argument to the `dagster dev` command to allow customization of the host where Dagit runs.
- [dagster-snowflake, dagster-duckdb] Database I/O managers (Snowflake, DuckDB) now support static partitions, multi-partitions, and dynamic partitions.

### Bugfixes

- Previously, if a description was provided for an op that backed a multi-asset, the op’s description would override the descriptions in Dagit for the individual assets. This has been fixed.
- Sometimes, when applying an `input_manager_key` to an asset’s input, incorrect resource config could be used when loading that input. This has been fixed.
- Previously, the backfill page errored when partitions definitions changed for assets that had been backfilled. This has been fixed.
- When displaying materialized partitions for multipartitioned assets, Dagit would error if a dimension had zero partitions. This has been fixed.
- [dagster-k8s] Fixed an issue where setting `runK8sConfig` in the Dagster Helm chart would not pass configuration through to pods launched using the `k8s_job_executor`.
- [dagster-k8s] Previously, using the `execute_k8s_job` op downstream of a dynamic output would result in k8s jobs with duplicate names being created. This has been fixed.
- [dagster-snowflake] Previously, if the schema for storing outputs didn’t exist, the Snowflake I/O manager would fail. Now it creates the schema.

### Breaking Changes

- Removed the experimental, undocumented `asset_key`, `asset_partitions`, and `asset_partitions_defs` arguments on `Out`.
- `@multi_asset` no longer accepts `Out` values in the dictionary passed to its `outs` argument. This was experimental and deprecated. Instead, use `AssetOut`.
- The experimental, undocumented `top_level_resources` argument to the `repository` decorator has been renamed to `_top_level_resources` to emphasize that it should not be set manually.

### Community Contributions

- `load_asset_values` now accepts resource configuration (thanks @Nintorac!)
- Previously, when using the `UPathIOManager`, paths with the `"."` character in them would be incorrectly truncated, which could result in multiple distinct objects being written to the same path. This has been fixed. (Thanks @spenczar!)

### Experimental

- [dagster-dbt] Added documentation to our dbt Cloud integration to cache the loading of software-defined assets from a dbt Cloud job.

### Documentation

- Revamped the introduction to the Partitions concepts page to make it clear that non-time-window partitions are equally encouraged.
- In Navigation, moved the Partitions and Backfill concept pages to their own section underneath Concepts.
- Moved the Running Dagster locally guide from **Deployment** to **Guides** to reflect that OSS and Cloud users can follow it.
- Added [a new guide](https://docs.dagster.io/guides/dagster/asset-versioning-and-caching) covering asset versioning and caching.

# 1.1.18 (core) / 0.17.18 (libraries)

### New

- Assets with time-window `PartitionsDefinition`s (e.g. `HourlyPartitionsDefinition`, `DailyPartitionsDefinition`) may now have a `FreshnessPolicy`.
- [dagster-dbt] When using `load_assets_from_dbt_project` or `load_assets_from_dbt_manifest` with `dbt-core>=1.4`, `AssetMaterialization` events will be emitted as the dbt command executes, rather than waiting for dbt to complete before emitting events.
- [dagster-aws] When [run monitoring](https://docs.dagster.io/deployment/run-monitoring#run-monitoring) detects that a run unexpectedly crashed or failed to start, an error message in the run’s event log will include log messages from the ECS task for that run to help diagnose the cause of the failure.
- [dagster-airflow] added `make_ephemeral_airflow_db_resource` which returns a `ResourceDefinition` for a local only airflow database for use in migrated airflow DAGs
- Made some performance improvements for job run queries which can be applied by running `dagster instance migrate`.
- [dagit] System tags (code + logical versions) are now shown in the asset sidebar and on the asset details page.
- [dagit] Source assets that have never been observed are presented more clearly on the asset graph.
- [dagit] The number of materialized and missing partitions are shown on the asset graph and in the asset catalog for partitioned assets.
- [dagit] Databricks-backed assets are now shown on the asset graph with a small “Databricks” logo.

### Bugfixes

- Fixed a bug where materializations of part of the asset graph did not construct required resource keys correctly.
- Fixed an issue where `observable_source_asset` incorrectly required its function to have a `context` argument.
- Fixed an issue with serialization of freshness policies, which affected cacheable assets that included these policies such as those from `dagster-airbyte`
- [dagster-dbt] Previously, the `dagster-dbt` integration was incompatible with `dbt-core>=1.4`. This has been fixed.
- [dagster-dbt] `load_assets_from_dbt_cloud_job` will now avoid unnecessarily generating docs when compiling a manifest for the job. Compile runs will no longer be kicked off for jobs not managed by this integration.
- Previously for multipartitioned assets, `context.asset_partition_key` returned a string instead of a `MultiPartitionKey`. This has been fixed.
- [dagster-k8s] Fixed an issue where pods launched by the `k8s_job_executor` would sometimes unexpectedly fail due to transient 401 errors in certain kubernetes clusters.
- Fix a bug with nth-weekday-of-the-month handling in cron schedules.

### Breaking Changes

- [dagster-airflow] `load_assets_from_airflow_dag` no longer creates airflow db resource definitions, as a user you will need to provide them on `Definitions` directly

### Deprecations

- The `partitions_fn` argument of the `DynamicPartitionsDefinition` class is now deprecated and will be removed in 2.0.0.

### Community Contributions

- [dagster-wandb] A new integration with [Weights & Biases](https://wandb.ai/site) allows you to orchestrate your MLOps pipelines and maintain ML assets with Dagster.
- Postgres has been updated to 14.6 for Dagster’s helm chart. Thanks [@DustyShap](https://github.com/DustyShap)!
- Typo fixed in docs. Thanks [@C0DK](https://github.com/C0DK)!
- You can now pass a callable directly to `asset` (rather than using `@asset` in decorator form) to create an asset. Thanks [@ns-finkelstein](https://github.com/nsfinkelstein)!

### Documentation

- New “Asset versioning and caching” guide
- [dagster-snowflake] The Snowflake guide has been updated to include PySpark dataframes
- [dagster-snowflake] The Snowflake guide has been updated to include private key authentication
- [dagster-airflow] The Airflow migration guide has been update to include more detailed instructions and considerations for making a migration

# 1.1.17 (core) / 0.17.17 (libraries)

### New

- The `dagster-airflow` library as been moved to 1.x.x to denote the stability of its api's going forward.
- [dagster-airflow] `make_schedules_and_jobs_from_airflow_dag_bag` has been added to allow for more fine grained composition of your transformed airflow DAGs into Dagster.
- [dagster-airflow] Airflow dag task `retries` and `retry_delay` configuration are now converted to op [RetryPolicies](https://docs.dagster.io/concepts/ops-jobs-graphs/op-retries#retrypolicy) with all `make_dagster_*` apis.

### Bugfixes

- Fixed an issue where cron schedules using a form like `0 5 * * mon#1` to execute on a certain day of the week each month executed every week instead.
- [dagit] Fixed an issue where the asset lineage page sometimes timed out while loading large asset graphs.
- Fixed an issue where the partitions page sometimes failed to load for partitioned asset jobs.

### Breaking Changes

- [dagster-airflow] The `use_airflow_template_context`, `mock_xcom` and `use_ephemeral_airflow_db` params have been dropped, by default all `make_dagster_*` apis now use a run-scoped airflow db, similiar to how `use_ephemeral_airflow_db` worked.
- [dagster-airflow] `make_airflow_dag` has been removed.
- [dagster-airflow] `make_airflow_dag_for_operator` has been removed.
- [dagster-airflow] `make_airflow_dag_containerized` has been removed.
- [dagster-airflow] `airflow_operator_to_op` has been removed.
- [dagster-airflow] `make_dagster_repo_from_airflow_dags_path` has been removed.
- [dagster-airflow] `make_dagster_repo_from_airflow_dag_bag` has been removed.
- [dagster-airflow] `make_dagster_repo_from_airflow_example_dags` has been removed.
- [dagster-airflow] The naming convention for ops generated from airflow tasks has been changed to `${dag_id}__${task_id}` from `airflow_${task_id}_${unique_int}`.
- [dagster-airflow] The naming convention for jobs generated from airflow dags has been changed to `${dag_id}` from `airflow_${dag_id}`.

# 1.1.15 (core) / 0.17.15 (libraries)

### New

- Definitions now accepts Executor instances in its executor argument, not just ExecutorDefinitions.
- `@multi_asset_sensor` now accepts a `request_assets` parameter, which allows it to directly request that assets be materialized, instead of requesting a run of a job.
- Improved the performance of instantiating a `Definitions` when using large numbers of assets or many asset jobs.
- The job passed to `build_schedule_from_partitioned_job` no longer needs to have a `partitions_def` directly assigned to it. Instead, Dagster will infer from the partitions from the assets it targets.
- `OpExecutionContext.asset_partition_keys_for_output` no longer requires an argument to specify the default output.
- The “Reload all” button on the Code Locations page in Dagit will now detect changes to a `pyproject.toml` file that were made while Dagit was running. Previously, Dagit needed to be restarted in order for such changes to be shown.
- `get_run_record_by_id` has been added to `DagsterInstance` to provide easier access to `RunRecord` objects which expose the `start_time` and `end_time` of the run.
- [dagit] In the “Materialize” modal, you can now choose to pass a range of asset partitions to a single run rather than launching a backfill.
- [dagster-docker] Added a `docker_container_op` op and `execute_docker_container_op` helper function for running ops that launch arbitrary Docker containers. See [the docs](https://docs.dagster.io/_apidocs/libraries/dagster-docker#ops) for more information.
- [dagster-snowflake-pyspark] The Snowflake I/O manager now supports PySpark DataFrames.
- [dagster-k8s] The Docker images include in the Dagster Helm chart are now built on the most recently released `python:3.x-slim` base image.

### Bugfixes

- Previously, the `build_asset_reconciliation_sensor` could time out when evaluating ticks over large selections of assets, or assets with many partitions. A series of performance improvements should make this much less likely.
- Fixed a bug that caused a failure when using `run_request_for_partition` in a sensor that targeted multiple jobs created via `define_asset_job`.
- The cost of importing `dagster` has been reduced.
- Issues preventing “re-execute from failure” from working correctly with dynamic graphs have been fixed.
- [dagit] In Firefox, Dagit no longer truncates text unnecessarily in some cases.
- [dagit] Dagit’s asset graph now allows you to click “Materialize” without rendering the graph if you have too many assets to display.
- [dagit] Fixed a bug that stopped the backfill page from loading when assets that had previously been backfilled no longer had a `PartitionsDefinition`.
- [dagster-k8s] Fixed an issue where `k8s_job_op` raised an Exception when running pods with multiple containers.
- [dagster-airbyte] Loosened credentials masking for Airbyte managed ingestion, fixing the Hubspot source, thanks @[joel-olazagasti](https://github.com/joel-olazagasti)!
- [dagster-airbyte] When using managed ingestion, Airbyte now pulls all source types available to the instance rather than the workspace, thanks @[emilija-omnisend](https://github.com/emilija-omnisend)!
- [dagster-airbyte] Fixed an issue which arose when attaching freshness policies to Airbyte assets and using the multiprocessing executor.
- [dagster-fivetran] Added the ability to force assets to be output for all specified Fivetran tables during a sync in the case that a sync’s API outputs are missing one or more tables.

### Breaking Changes

- The `asset_keys` and `asset_selection` parameters of the experimental `@multi_asset_sensor` decorator have been replaced with a `monitored_assets` parameter. This helps disambiguate them from the new `request_assets` parameter.

### Community Contributions

- A broken docs link in snowflake_quickstart has been fixed, thanks @[clayheaton](https://github.com/clayheaton)!
- Troubleshooting help added to helm deployment guide, thanks @adam-bloom!
- `StaticPartitionMapping` is now serializable, thanks @[AlexanderVR](https://github.com/AlexanderVR)!
- [dagster-fivetran] `build_fivetran_assets` now supports `group_name` , thanks @[toddy86](https://github.com/toddy86)!
- [dagster-azure] `AzureBlobComputeManager` now supports authentication via `DefaultAzureCredential`, thanks @[mpicard](https://github.com/mpicard)!

### Experimental

- [dagster-airflow] added a new api `load_assets_from_airflow_dag` that creates graph-backed, partitioned, assets based on the provided Airflow DAG.

# 1.1.14 (core) / 0.17.14 (libraries)

### New

- Large asset graphs can now be materialized in Dagit without needing to first enter an asset subset. Previously, if you wanted to materialize every asset in such a graph, you needed to first enter `*` as the asset selection before materializing the assets.
- Added a pin of the `sqlalchemy` package to `<2.0.0` due to a breaking change in that version.
- Added a pin of the `dbt-core` package to `<1.4.0` due to breaking changes in that release that affected the Dagster dbt integration. We plan to remove this pin in the next release.
- Added a pin of the `jupyter-client` package to `<8.0` due to an issue with the most recent release causing hangs while running dagstermill ops.

### Bugfixes

- Fixed an issue where the Backfills page in Dagit didn't show partition status for some backfills.
- [dagster-aws] Fixed an issue where the `EcsRunLauncher` sometimes waited much longer than intended before retrying after a failure launching a run.
- [dagster-mysql] Fixed an issue where some implementations of MySQL storage were raising invalid version errors.

# 1.1.13 (core) / 0.17.13 (libraries)

### Bugfixes

- The `nux` section of `dagster.yaml` config has been fixed.
- Changes when heartbeats occur in the daemon to avoid crashes in certain conditions.
- Fixed an issue where passing a workspace file as an argument into the `dagster dev` command raised an error
- [dagit] Fixes an issue with asset names being truncated by long asset descriptions in the asset catalog, making them impossible to click.
- [dagit] The backfill page no longer fails to load if any of the asset backfills had assets that were partitioned at the time of the backfill but are no longer partitioned.

# 1.1.12 (core) / 0.17.12 (libraries)

### Bugfixes

- [dagit] Fixes a "maximum call stack size exceeded" error when viewing a materialization of a root asset in Asset Details

# 1.1.11 (core) / 0.17.11 (libraries)

### New

- Added a new `dagster dev` command that can be used to run both Dagit and the Dagster daemon in the same process during local development. See the new [Running Dagster Locally guide](https://docs.dagster.io/deployment/guides/running-locally) in the docs for more information.
- Added instructions for installing the `dagster` package on M1 and M2 Macs that avoids installation errors when building the `grpcio` package. See [the Installing Dagster guide in the docs](https://docs.dagster.io/getting-started/install) for more information.
- `create_repository_using_definitions_args` has been added for users to backport their repository definitions to the new `Definitions` API
- When running Dagit on your local machine, a prompt will now appear that allows you to optionally enter an email address to receive Dagster security updates or subscribe to the Dagster newsletter. This prompt can be dismissed in the UI, or permanently disabled by adding the following to your `dagster.yaml` file:

```
nux:
  enabled: false
```

- The `grpcio` pin in Dagster to <1.48.1 has been restored for Python versions 3.10 and 3.11, due to [upstream issues](https://github.com/grpc/grpc/issues/31885) in the grpcio package causing hangs in Dagster.
- [dagit] Improved query performance on Scheduled Runs page.
- [dagit] The "Materialize" button now allows you to add tags to asset materialization runs. If your assets do not require config or partitions, you may need to shift-click "Materialize".
- [dagit] The kind tags and logos shown on assets in the Asset Graph now appear in other parts of Dagit so it's easier to understand your assets.
- [dagit] Selecting a materialization event on the Asset Details page now shows links to the upstream materialzations ("Source Data") that were incorporated into that version of the asset.
- [dagit] Added or improved document (browser tab) titles throughout Dagit.
- [dagster-snowflake] Snowflake resource and IO manager now support private key authentication with unencrypted keys
- [dagster-dbt] The op created when using `load_assets_from_dbt*` is now configurable, allowing you to pass in specific parameters to the underlying dbt command (such as `--full-refresh`). To do so, supply config of the form `{"ops": {"run_dbt_<abcde>": {"config": {"full_refresh": True}}}}` when defining your asset job, or in Dagit.

### Bugfixes

- For time-partitioned assets, the `build_asset_reconciliation_sensor` will now only materialize partitions from the past day. Previously, if a new asset was added with a large number of missing partitions, a run for each of the missing partitions would be launched immediately.
- A variety of performance improvements to the `build_asset_reconciliation_sensor`, which should help significantly speed up sensor evaluation in cases where there is a large number of assets or partitions.
- [dagit] Fixed broken code location names in the “Definitions” filter dialog accessible from the left navigation.
- [dagit] The Backfills pages in Dagit no longer crash when your backfills span tens of thousands of partition keys
- [dagit] The asset graph now links to the failed run, not the last successful materialization, when assets are shown in a "Failed" state.

### Breaking Changes

- Strings with escaped characters are now invalid substrings of partition keys.

### Experimental

- [dagster-dbt] Added a utility to cache compilations from dbt Cloud jobs, allowing software-defined assets to be loaded faster from dbt Cloud jobs.

### Community Contributions

- In dagster-airbyte, keys containing credentials are now considered a secret (thanks [joel-olazagasti](https://github.com/joel-olazagasti))!

### Documentation

- A new example of using the branching IO manager has been added.

# 1.1.10 (core) / 0.17.10 (libraries)

### New

- The `selection` argument of `define_asset_job` now accepts lists of `AssetKey`s or `AssetsDefinitions`.
- `RunRequest` now takes a `stale_assets_only` flag that filters the full set of assets that would be materialized by a job to stale assets only. This can be used in schedules and sensors.
- Dagit will now choose a different open port on the local machine to run on when no port is specified to the `dagit` command and the default port 3000 is already in use.
- The `grpcio` pin in Dagster to <1.48.1 has been removed for Python versions 3.10 and 3.11. Python 3.7, 3.8, and 3.9 are still pinned to <1.48.1 due to a bug in the grpc library that is causing the process to sometimes hang.
- When it is likely that an op process was killed due to running out of memory, a clearer error message is now displayed in Dagit.
- When a sensor tick fails due to taking longer than 60 seconds to execute, a clearer error message is displayed on the sensor timeline in Dagit.
- When you view compute logs on a run in Dagit, we now locally track whether you choose the `stdout` or `stderr` tab. The next time you view compute logs, you will see that tab first by default.
- The `executor` and `loggers` arguments on `Definitions` are no longer experimental.
- [dagster-dbt] When `json_log_format` is set to `False` when using the `dbt_cli_resource`, logs will be emitted at the appropriate log level in some situations. Previously, all logs would be emitted at the `INFO` level.
- [dagster-snowflake] The Snowflake IO Manager and Snowflake Resource now support private key authentication. Thanks Josh Taylor!
- [dagster-airbyte] Users can now specify freshness policies when generating Airbyte assets.
- [dagster-airbyte] When using managed Airbyte ingestion, users can now specify a destination table prefix.

### Bugfixes

- Fixed a bug that caused backfills launched from the asset graph page not to work with code locations running versions of Dagster less than 1.1.8.
- Fixed a bug that reverted to the default partition mappings in situations where asset dependencies were resolved based on group instead of asset key.
- The way skips are propagate through the graph when using dynamic outputs are used has been fixed.
- Fixed a bug affecting the download link for cloud-based compute log manager implementations (e.g. `dagster-azure` / `dagster-aws` / `dagster-gcp`)
- Fixed a bug that would cause errors when using `build_asset_reconciliation_sensor` with asset graphs that contained references to source assets without the associated `SourceAsset` objects (which may happen when using `load_assets_from_dbt_*`).
- [dagit] Fixed an issue where an error appeared in dagit when a code server stopped and restarted.
- [dagit] Previously, when restarting the dagit process, the Dagit frontend kept cached versions of certain queries even after the code location finished loading. This could lead to display of stale versions of jobs or other code objects. These objects will now be correctly retrieved anew from the backend.
- [dagster-dbt] Fixed a bug with the `DbtManifestAssetSelection` which could result in `KeyErrors` when selecting from projects with sources defined.
- [dagster-k8s] Fixed a bug where disabling run worker crash recovery by setting maxResumeRunAttempts to 0 in the Helm chart had no effect.
- [dagster-airflow] Fixed a bug where transformed Airflow DAG schedules would always use UTC for their timezone.

### Breaking Changes

- [dagit] The `/instance` and `/workspace` path prefixes were removed in previous version, but redirects were left in place. These redirects have now been removed.

### Community Contributions

- The new `StaticPartitionMapping` enables explicitly defining the dependencies between partitions in two `StaticPartitionsDefinition`s. Thanks Alexander VR!
- Fixed a typo in the Dagster Instance documentation header - thanks Cushnir Grigore!
- Fixed a typo in the Dagster Instance documentation body - thanks Chris Zubak-Skees!
- Fixed docstring for static_partitioned_config - thanks Sylvain Lesage!
- Fix dead link in the docs to the Slack community - thanks Emil Christensen!

### Documentation

- The [Ops and jobs tutorial](https://docs.dagster.io/master/guides/dagster/intro-to-ops-jobs) has been moved to the Guides section. Clicking "Tutorial" in the sidenav will open the Assets tutorial.

# 1.1.9 (core) / 0.17.9 (libraries)

### Bugfixes

- Fixed an issue which would cause errors when using built-in generic types in annotations for asset and op parameters.
- Fixed an unintentional dependency on Pydantic >=1.8 which lacked a pin, now older versions of the package may be used.

# 1.1.8 (core) / 0.17.8 (libraries)

### New

- Asset backfills launched from the asset graph now respect partition mappings. For example, if partition N of asset2 depends on partition N-1 of asset1, and both of those partitions are included in a backfill, asset2’s partition N won’t be backfilled until asset1’s partition N-1 has been materialized.
- Asset backfills launched from the asset graph will now only materialize each non-partitioned asset once - after all upstream partitions within the backfill have been materialized.
- Executors can now be configured with a `tag_concurrency_limits` key that allows you to specify limits on the number of ops with certain tags that can be executing at once within a single run. See the [docs](https://docs.dagster.io/concepts/ops-jobs-graphs/job-execution#op-concurrency-limits) for more information.
- `ExecuteInProcessResult`, the type returned by `materialize`, `materialize_to_memory`, and `execute_in_process`, now has an `asset_value` method that allows you to fetch output values by asset key.
- `AssetIn`s can now accept `Nothing` for their `dagster_type`, which allows omitting the input from the parameters of the `@asset`- or `@multi_asset`- decorated function. This is useful when you want to specify a partition mapping or metadata for a non-managed input.
- The `start_offset` and `end_offset` arguments of `TimeWindowPartitionMapping` now work across `TimeWindowPartitionsDefinitions` with different start dates and times.
- If `add_output_metadata` is called multiple times within an op, asset, or IO manager `handle_output`, the values will now be merged, instead of later dictionaries overwriting earlier ones.
- `materialize` and `materialize_to_memory` now both accept a `tags` argument.
- Added `SingleDimensionDependencyMapping`, a `PartitionMapping` object that defines a correspondence between an upstream single-dimensional partitions definition and a downstream `MultiPartitionsDefinition`.
- The `RUN_DEQUEUED` event has been removed from the event log, since it was duplicative with the `RUN_STARTING` event.
- When an Exception is raised during the execution of an op or asset, Dagit will now include the original Exception that was raised, even if it was caught and another Exception was raised instead. Previously, Dagit would only show exception chains if the Exception was included using the `raise Exception() from e` syntax.
- [dagit] The Asset Catalog table in Dagit is now a virtualized infinite-scroll table. It is searchable and filterable just as before, and you can now choose assets for bulk materialization without having to select across pages.
- [dagit] Restored some metadata to the Code Locations table, including image, python file, and module name.
- [dagit] Viewing a partition on the asset details page now shows both the latest materialization and also all observations about that materialization.
- [dagit] Improved performance of the loading time for the backfills page
- [dagit] Improved performance when materializing assets with very large partition sets
- [dagit] Moving around asset and op graphs while selecting nodes is easier - drag gestures no longer clear your selection.
- [dagster-k8s] The Dagster Helm chart now allows you to set an arbitrary kubernetes config dictionary to be included in the launched job and pod for each run, using the `runK8sConfig` key in the `k8sRunLauncher` section. See the [docs](https://docs.dagster.io/deployment/guides/kubernetes/customizing-your-deployment#instance-level-kubernetes-configuration) for more information.
- [dagster-k8s] `securityContext` can now be set in the `k8sRunLauncher` section of the Dagster Helm chart.
- [dagster-aws] The `EcsRunLauncher` can now be configured with cpu and memory resources for each launched job. Previously, individual jobs needed to be tagged with CPU and memory resources. See the [docs](https://docs.dagster.io/master/deployment/guides/aws#customizing-cpu-and-memory-in-ecs) for more information.
- [dagster-aws] The `S3ComputeLogManager` now takes in an argument `upload_extra_args` which are passed through as the `ExtraArgs` parameter to the file upload call.
- [dagster-airflow] added `make_dagster_definitions_from_airflow_dags_path` and **`make_dagster_definitions_from_airflow_dag_bag`** which are passed through as the `ExtraArgs` parameter to the file upload call.

### Bugfixes

- Fixed a bug where ad-hoc materializations of assets were not correctly retrieving metadata of upstream assets.
- Fixed a bug that caused `ExperimentalWarning`s related to `LogicalVersions` to appear even when version-based staleness was not in use.
- Fixed a bug in the asset reconciliation sensor that caused multi-assets to be reconciled when some, but not all, of the assets they depended on, were reconciled.
- Fixed a bug in the asset reconciliation sensor that caused it to only act on one materialization per asset per tick, even when multiple partitions of an asset were materialized.
- Fixed a bug in the asset reconciliation sensor that caused it to never attempt to rematerialize assets which failed in their last execution. Now, it will launch the next materialization for a given asset at the same time that it would have if the original run had completed successfully.
- The `load_assets_from_modules` and `load_assets_from_package_module` utilities now will also load cacheable assets from the specified modules.
- The `dequeue_num_workers` config setting on `QueuedRunCoordinator`is now respected.
- [dagit] Fixed a bug that caused a “Maximum recursion depth exceeded” error when viewing partitioned assets with self-dependencies.
- [dagit] Fixed a bug where “Definitions loaded” notifications would constantly show up in cases where there were multiple dagit hosts running.
- [dagit] Assets that are partitioned no longer erroneously appear "Stale" in the asset graph.
- [dagit] Assets with a freshness policy no longer appear stale when they are still meeting their freshness policy.
- [dagit] Viewing Dagit in Firefox no longer results in erroneous truncation of labels in the left sidebar.
- [dagit] Timestamps on the asset graph are smaller and have an appropriate click target.
- [dagster-databricks] The `databricks_pyspark_step_launcher` will now cancel the relevant databricks job if the Dagster step execution is interrupted.
- [dagster-databricks] Previously, the `databricks_pyspark_step_launcher` could exit with an unhelpful error after receiving an HTTPError from databricks with an empty message. This has been fixed.
- [dagster-snowflake] Fixed a bug where calling `execute_queries` or `execute_query` on a `snowflake_resource` would raise an error unless the `parameters` argument was explicitly set.
- [dagster-aws] Fixed a bug in the `EcsRunLauncher` when launching many runs in parallel. Previously, each run risked hitting a `ClientError` in AWS for registering too many concurrent changes to the same task definition family. Now, the `EcsRunLauncher` recovers gracefully from this error by retrying it with backoff.
- [dagster-airflow] Added `make_dagster_definitions_from_airflow_dags_path` and `make_dagster_definitions_from_airflow_dag_bag` for creating Dagster definitions from a given airflow Dag file path or DagBag

### Community Contributions

- Fixed a metadata loading error in `UPathIOManager`, thanks @danielgafni!
- [dagster-aws]`FakeS3Session` now includes additional functions and improvements to align with the boto3 S3 client API, thanks @asharov!
- Typo fix from @vpicavet, thank you!
- Repository license file year and company update, thanks @vwbusguy!

### Experimental

- Added experimental `BranchingIOManager` to model use case where you wish to read upstream assets from production environments and write them into a development environment.
- Add `create_repository_using_definitions_args` to allow for the creation of named repositories.
- Added the ability to use Python 3 typing to define and access op and asset config.
- [dagster-dbt] Added `DbtManifestAssetSelection`, which allows you to define selections of assets loaded from a dbt manifest using dbt selection syntax (e.g. `tag:foo,path:marts/finance`).

### Documentation

- There’s now only one [Dagster Cloud Getting Started guide](https://docs.dagster.io/dagster-cloud/getting-started), which includes instructions for both Hybrid and Serverless deployment setups.
- Lots of updates throughout the docs to clean up remaining references to `@repository`, replacing them with `Definitions`.
- Lots of updates to the dagster-airflow documentation, a tutorial for getting started with Dagster from an airflow background, a migration guide for going to Dagster from Airflow and a terminology/concept map for Airflow onto Dagster.

# 1.1.7 (core) / 0.17.7 (libraries)

### New

- `Definitions` is no longer marked as experimental and is the preferred API over `@repository` for new users of Dagster. Examples, tutorials, and documentation have largely ported to this new API. No migration is needed. Please see GitHub discussion for more details.
- The “Workspace” section of Dagit has been removed. All definitions for your code locations can be accessed via the “Deployment” section of the app. Just as in the old Workspace summary page, each code location will show counts of its available jobs, assets, schedules, and sensors. Additionally, the code locations page is now available at `/locations`.
- Lagged / rolling window partition mappings: `TimeWindowPartitionMapping` now accepts `start_offset` and `end_offset` arguments that allow specifying that time partitions depend on earlier or later time partitions of upstream assets.
- Asset partitions can now depend on earlier time partitions of the same asset. The asset reconciliation sensor will respect these dependencies when requesting runs.
- `dagit` can now accept multiple arguments for the `-m` and `-f` flags. For each argument a new code location is loaded.
- Schedules created by `build_schedule_from_partitioned_job` now execute more performantly - in constant time, rather than linear in the number of partitions.
- The `QueuedRunCoordinator` now supports options `dequeue_use_threads` and `dequeue_num_workers` options to enable concurrent run dequeue operations for greater throughput.
- [dagster-dbt] `load_assets_from_dbt_project`, `load_assets_from_dbt_manifest`, and `load_assets_from_dbt_cloud_job` now support applying freshness policies to loaded nodes. To do so, you can apply `dagster_freshness_policy` config directly in your dbt project, i.e. `config(dagster_freshness_policy={"maximum_lag_minutes": 60})` would result in the corresponding asset being assigned a `FreshnessPolicy(maximum_lag_minutes=60)`.
- The `DAGSTER_RUN_JOB_NAME` environment variable is now set in containerized environments spun up by our run launchers and executor.
- [dagster-airflow] `make_dagster_repo_from_airflow_dags_path` ,`make_dagster_job_from_airflow_dag` and `make_dagster_repo_from_airflow_dag_bag` have a new `connections` parameter which allows for configuring the airflow connections used by migrated dags.

### Bugfixes

- Fixed a bug where the `log` property was not available on the `RunStatusSensorContext` context object provided for run status sensors for sensor logging.
- Fixed a bug where the re-execute button on runs of asset jobs would incorrectly show warning icon, indicating that the pipeline code may have changed since you last ran it.
- Fixed an issue which would cause metadata supplied to graph-backed assets to not be viewable in the UI.
- Fixed an issue where schedules often took up to 5 seconds to start after their tick time.
- Fixed an issue where Dagster failed to load a dagster.yaml file that specified the folder to use for sqlite storage in the `dagster.yaml` file using an environment variable.
- Fixed an issue which would cause the k8s/docker executors to unnecessarily reload CacheableAssetsDefinitions (such as those created when using `load_assets_from_dbt_cloud_job`) on each step execution.
- [dagster-airbyte] Fixed an issue where Python-defined Airbyte sources and destinations were occasionally recreated unnecessarily.
- Fixed an issue with `build_asset_reconciliation_sensor` that would cause it to ignore in-progress runs in some cases.

- Fixed a bug where GQL errors would be thrown in the asset explorer when a previously materialized asset had its dependencies changed.
- [dagster-airbyte] Fixed an error when generating assets for normalization table for connections with non-object streams.
- [dagster-dbt] Fixed an error where dbt Cloud jobs with `dbt run` and `dbt run-operation` were incorrectly validated.
- [dagster-airflow] `use_ephemeral_airflow_db` now works when running within a PEX deployment artifact.

### Documentation

- New documentation for [Code locations](https://docs.dagster.io/concepts/code-locations) and how to define one using `Definitions`
- Lots of updates throughout the docs to reflect the recommended usage of `Definitions`. Any content not ported to `Definitions` in this release is in the process of being updated.
- New documentation for dagster-airflow on how to start writing dagster code from an airflow background.

# 1.1.6 (core) / 0.17.6 (libraries)

### New

- [dagit] Throughout Dagit, when the default repository name `__repository__` is used for a repo, only the code location name will be shown. This change also applies to URL paths.
- [dagster-dbt] When attempting to generate software-defined assets from a dbt Cloud job, an error is now raised if none are created.
- [dagster-dbt] Software-defined assets can now be generated for dbt Cloud jobs that execute multiple commands.

### Bugfixes

- Fixed a bug that caused `load_asset_value` to error with the default IO manager when a `partition_key` argument was provided.
- Previously, trying to access `context.partition_key` or `context.asset_partition_key_for_output` when invoking an asset directly (e.g. in a unit test) would result in an error. This has been fixed.
- Failure hooks now receive the original exception instead of `RetryRequested` when using a retry policy.
- The LocationStateChange GraphQL subscription has been fixed (thanks @\***\*[roeij](https://github.com/roeij) !)**
- Fixed a bug where a `sqlite3.ProgrammingError` error was raised when creating an ephemeral `DagsterInstance`, most commonly when `build_resources` was called without passing in an instance parameter.
- [dagstermill] Jupyter notebooks now correctly render in Dagit on Windows machines.
- [dagster-duckdb-pyspark] New `duckdb_pyspark_io_manager` helper to automatically create a DuckDB I/O manager that can store and load PySpark DataFrames.
- [dagster-mysql] Fixed a bug where versions of mysql < `8.0.31` would raise an error on some run queries.
- [dagster-postgres] connection url param “options“ are no longer overwritten in dagit.
- [dagit] Dagit now allows backfills to be launched for asset jobs that have partitions and required config.
- [dagit] Dagit no longer renders the "Job in repo@location" label incorrectly in Chrome v109.
- [dagit] Dagit's run list now shows improved labels on asset group runs of more than three assets
- [dagit] Dagit's run gantt chart now renders per-step resource initialization markers correctly.
- [dagit] In op and asset descriptions in Dagit, rendered markdown no longer includes extraneous escape slashes.
- Assorted typos and omissions fixed in the docs — thanks @[C0DK](https://github.com/C0DK) and @[akan72](https://github.com/akan72)!

### Experimental

- As an optional replacement of the workspace/repository concepts, a new `Definitions` entrypoint for tools and the UI has been added. A single `Definitions` object per code location may be instantiated, and accepts typed, named arguments, rather than the heterogenous list of definitions returned from an `@repository`-decorated function. To learn more about this feature, and provide feedback, please refer to the [Github Discussion](https://github.com/dagster-io/dagster/discussions/10772).
- [dagster-slack] A new `make_slack_on_freshness_policy_status_change_sensor` allows you to create a sensor to alert you when an asset is out of date with respect to its freshness policy (and when it’s back on time!)

### Documentation

- Refreshed `dagstermill` guide and reference page [https://docs.dagster.io/integrations/dagstermill](https://docs.dagster.io/integrations/dagstermill)
- New declarative scheduling guide: [https://docs.dagster.io/guides/dagster/scheduling-assets](https://docs.dagster.io/guides/dagster/scheduling-assets)
- New `dagster-snowflake` guide: [https://docs.dagster.io/integrations/snowflake](https://docs.dagster.io/integrations/snowflake)
- Added docs for asset code versioning: [https://docs.dagster.io/concepts/assets/software-defined-assets#asset-code-versions](https://docs.dagster.io/concepts/assets/software-defined-assets#asset-code-versions)
- Added docs for observable source assets: [https://docs.dagster.io/concepts/assets/asset-observations#observable-source-assets](https://docs.dagster.io/concepts/assets/asset-observations#observable-source-assets)

# 1.1.5 (core) / 0.17.5 (libraries)

### Bugfixes

- [dagit] Fixed an issue where the Partitions tab sometimes failed to load for asset jobs.

# 1.1.4 (core) / 0.17.4 (libraries)

### Community Contributions

- Fixed a typo in GCSComputeLogManager docstring (thanks [reidab](https://github.com/reidab))!
- [dagster-airbyte] job cancellation on run termination is now optional. (Thanks [adam-bloom](https://github.com/adam-bloom))!
- [dagster-snowflake] Can now specify snowflake role in config to snowflake io manager (Thanks [binhnefits](https://github.com/binhnefits))!
- [dagster-aws] A new AWS systems manager resource (thanks [zyd14](https://github.com/zyd14))!
- [dagstermill] Retry policy can now be set on dagstermill assets (thanks [nickvazz](https://github.com/nickvazz))!
- Corrected typo in docs on metadata (thanks [C0DK](https://github.com/C0dk))!

### New

- Added a `job_name` parameter to `InputContext`
- Fixed inconsistent io manager behavior when using `execute_in_process` on a `GraphDefinition` (it would use the `fs_io_manager` instead of the in-memory io manager)
- Compute logs will now load in Dagit even when websocket connections are not supported.
- [dagit] A handful of changes have been made to our URLs:
  - The `/instance` URL path prefix has been removed. E.g. `/instance/runs` can now be found at `/runs`.
  - The `/workspace` URL path prefix has been changed to `/locations`. E.g. the URL for job `my_job` in repository `foo@bar` can now be found at `/locations/foo@bar/jobs/my_job`.
- [dagit] The “Workspace” navigation item in the top nav has been moved to be a tab under the “Deployment” section of the app, and is renamed to “Definitions”.
- [dagstermill] Dagster events can now be yielded from asset notebooks using `dagstermill.yield_event`.
- [dagstermill] Failed notebooks can be saved for inspection and debugging using the new `save_on_notebook_failure` parameter.
- [dagster-airflow] Added a new option `use_ephemeral_airflow_db` which will create a job run scoped airflow db for airflow dags running in dagster
- [dagster-dbt] Materializing software-defined assets using dbt Cloud jobs now supports partitions.
- [dagster-dbt] Materializing software-defined assets using dbt Cloud jobs now supports subsetting. Individual dbt Cloud models can be materialized, and the proper filters will be passed down to the dbt Cloud job.
- [dagster-dbt] Software-defined assets from dbt Cloud jobs now support configurable group names.
- [dagster-dbt] Software-defined assets from dbt Cloud jobs now support configurable `AssetKey`s.

### Bugfixes

- Fixed regression starting in `1.0.16` for some compute log managers where an exception in the compute log manager setup/teardown would cause runs to fail.
- The S3 / GCS / Azure compute log managers now sanitize the optional `prefix` argument to prevent badly constructed paths.
- [dagit] The run filter typeahead no longer surfaces key-value pairs when searching for `tag:`. This resolves an issue where retrieving the available tags could cause significant performance problems. Tags can still be searched with freeform text, and by adding them via click on individual run rows.
- [dagit] Fixed an issue in the Runs tab for job snapshots, where the query would fail and no runs were shown.
- [dagit] Schedules defined with cron unions displayed “Invalid cron string” in Dagit. This has been resolved, and human-readable versions of all members of the union will now be shown.

### Breaking Changes

- You can no longer set an output’s asset key by overriding `get_output_asset_key` on the `IOManager` handling the output. Previously, this was experimental and undocumented.

### Experimental

- Sensor and schedule evaluation contexts now have an experimental `log` property, which log events that can later be viewed in Dagit. To enable these log views in dagit, navigate to the user settings and enable the `Experimental schedule/sensor logging view` option. Log links will now be available for sensor/schedule ticks where logs were emitted. Note: this feature is not available for users using the `NoOpComputeLogManager`.

# 1.1.3 (core) / 0.17.3 (libraries)

### Bugfixes

- Fixed a bug with the asset reconciliation sensor that caused duplicate runs to be submitted in situations where an asset has a different partitioning than its parents.
- Fixed a bug with the asset reconciliation sensor that caused it to error on time-partitioned assets.
- [dagster-snowflake] Fixed a bug when materializing partitions with the Snowflake I/O manager where sql `BETWEEN` was used to determine the section of the table to replace. `BETWEEN` included values from the next partition causing the I/O manager to erroneously delete those entries.
- [dagster-duckdb] Fixed a bug when materializing partitions with the DuckDB I/O manager where sql `BETWEEN` was used to determine the section of the table to replace. `BETWEEN` included values from the next partition causing the I/O manager to erroneously delete those entries.

# 1.1.2 (core) / 0.17.2 (libraries)

### Bugfixes

- In Dagit, assets that had been materialized prior to upgrading to 1.1.1 were showing as "Stale". This is now fixed.
- Schedules that were constructed with a list of cron strings previously rendered with an error in Dagit. This is now fixed.
- For users running dagit version >= 1.0.17 (or dagster-cloud) with dagster version < 1.0.17, errors could occur when hitting "Materialize All" and some other asset-related interactions. This has been fixed.

# 1.1.1 (core) / 0.17.1 (libraries)

## Major Changes since 1.0.0 (core) / 0.16.0 (libraries)

### Core

- You can now create **multi-dimensional partitions definitions** for software-defined assets, through the `MultiPartitionsDefinition` API. In Dagit, you can filter and materialize certain partitions by providing ranges per-dimension, and view your materializations by dimension.
- The new **asset reconciliation sensor** automatically materializes assets that have never been materialized or whose upstream assets have changed since the last time they were materialized. It works with partitioned assets too. You can construct it using `build_asset_reconciliation_sensor`.
- You can now add a `FreshnessPolicy` to any of your software-defined assets, to specify how up-to-date you expect that asset to be. You can view the freshness status of each asset in Dagit, alert when assets are missing their targets using the `@freshness_policy_sensor`, and use the `build_asset_reconciliation_sensor` to make a sensor that automatically kick off runs to materialize assets based on their freshness policies.
- You can now **version your asset ops and source assets** to help you track which of your assets are stale. You can do this by assigning `op_version` s to software-defined assets or `observation_fn` s to `SourceAsset`s. When a set of assets is versioned in this way, their “Upstream Changed” status will be based on whether upstream versions have changed, rather than on whether upstream assets have been re-materialized. You can launch runs that materialize only stale assets.
- The new `@multi_asset_sensor` decorator enables defining custom sensors that trigger based on the materializations of multiple assets. The context object supplied to the decorated function has methods to fetch latest materializations by asset key, as well as built-in cursor management to mark specific materializations as “consumed”, so that they won’t be returned in future ticks. It can also fetch materializations by partition and mark individual partitions as consumed.
- `RepositoryDefinition` now exposes a `load_asset_value` method, which accepts an asset key and invokes the asset’s I/O manager’s `load_input` function to load the asset as a Python object. This can be used in notebooks to do exploratory data analysis on assets.
- With the new `asset_selection` parameter on `@sensor` and `SensorDefinition`, you can now define a sensor that directly targets a selection of assets, instead of targeting a job.
- When running `dagit` or `dagster-daemon` locally, **environment variables included in a `.env` file** in the form `KEY=value` in the same folder as the command will be automatically included in the environment of any Dagster code that runs, allowing you to easily use environment variables during local development.

### Dagit

- The Asset Graph has been redesigned to make better use of color to communicate asset health. New status indicators make it easy to spot missing and stale assets (even on large graphs!) and the UI updates in real-time as displayed assets are materialized.
- The Asset Details page has been redesigned and features a new side-by-side UI that makes it easier to inspect event metadata. A color-coded timeline on the partitions view allows you to drag-select a time range and inspect the metadata and status quickly. The new view also supports assets that have been partitioned across multiple dimensions.
- The new Workspace page helps you quickly find and navigate between all your Dagster definitions. It’s also been re-architected to load significantly faster when you have thousands of definitions.
- The Overview page is the new home for the live run timeline and helps you understand the status of all the jobs, schedules, sensors, and backfills across your entire deployment. The timeline is now grouped by repository and shows a run status rollup for each group.

### Integrations

- `dagster-dbt` now supports generating software-defined assets from your dbt Cloud jobs.
- `dagster-airbyte` and `dagster-fivetran` now support automatically generating assets from your ETL connections using `load_assets_from_airbyte_instance` and `load_assets_from_fivetran_instance`.
- New `dagster-duckdb` integration: `build_duckdb_io_manager` allows you to build an I/O manager that stores and loads Pandas and PySpark DataFrames in DuckDB.

### Database migration

- Optional database schema migration, which can be run via `dagster instance migrate`:
  - Improves Dagit performance by adding database indexes which should speed up the run view as well as a range of asset-based queries.
  - Enables multi-dimensional asset partitions and asset versioning.

### Breaking Changes and Deprecations

- `define_dagstermill_solid`, a legacy API, has been removed from `dagstermill`. Use `define_dagstermill_op` or `define_dagstermill_asset` instead to create an `op` or `asset` from a Jupyter notebook, respectively.
- The internal `ComputeLogManager` API is marked as deprecated in favor of an updated interface: `CapturedLogManager`. It will be removed in `1.2.0`. This should only affect dagster instances that have implemented a custom compute log manager.

### Dependency Changes

- `dagster-graphql` and `dagit` now use version 3 of `graphene`

## Since 1.0.17

### New

- The new `UPathIOManager` base class is now a top-level Dagster export. This enables you to write a custom I/O manager that plugs stores data in any filesystem supported by `universal-pathlib` and uses different serialization format than `pickle` (Thanks Daniel Gafni!).
- The default `fs_io_manager` now inherits from the `UPathIOManager`, which means that its `base_dir` can be a path on any filesystem supported by `universal-pathlib` (Thanks Daniel Gafni!).
- `build_asset_reconciliation_sensor` now works with support partitioned assets.
- `build_asset_reconciliation_sensor` now launches runs to keep assets in line with their defined FreshnessPolicies.
- The `FreshnessPolicy` object is now exported from the top level dagster package.
- For assets with a `FreshnessPolicy` defined, their current freshness status will be rendered in the asset graph and asset details pages.
- The AWS, GCS, and Azure compute log managers now take an additional config argument `upload_interval` which specifies in seconds, the interval in which partial logs will be uploaded to the respective cloud storage. This can be used to display compute logs for long-running compute steps.
- When running `dagit` or `dagster-daemon` locally, environment variables included in a `.env` file in the form `KEY=value` in the same folder as the command will be automatically included in the environment of any Dagster code that runs, allowing you to easily test environment variables during local development.
- `observable_source_asset` decorator creates a `SourceAsset` with an associated `observation_fn` that should return a `LogicalVersion`, a new class that wraps a string expressing a version of an asset’s data value.
- [dagit] The asset graph now shows branded compute_kind tags for dbt, Airbyte, Fivetran, Python and more.
- [dagit] The asset details page now features a redesigned event viewer, and separate tabs for Partitions, Events, and Plots. This UI was previously behind a feature flag and is now generally available.
- [dagit] The asset graph UI has been revamped and makes better use of color to communicate asset status, especially in the zoomed-out view.
- [dagit] The asset catalog now shows freshness policies in the “Latest Run” column when they are defined on your assets.
- [dagit] The UI for launching backfills in Dagit has been simplified. Rather than selecting detailed ranges, the new UI allows you to select a large “range of interest” and materialize only the partitions of certain statuses within that range.
- [dagit] The partitions page of asset jobs has been updated to show per-asset status rather than per-op status, so that it shares the same terminology and color coding as other asset health views.
- [dagster-k8s] Added an `execute_k8s_job` function that can be called within any op to run an image within a Kubernetes job. The implementation is similar to the build-in `k8s_job_op` , but allows additional customization - for example, you can incorporate the output of a previous op into the launched Kubernetes job by passing it into `execute_k8s_job`. See the [dagster-k8s API docs](https://docs.dagster.io/_apidocs/libraries/dagster-k8s#ops) for more information.
- [dagster-databricks] Environment variables used by dagster cloud are now automatically set when submitting databricks jobs if they exist, thank you @zyd14!
- [dagstermill] `define_dagstermill_asset` now supports `RetryPolicy` . Thanks @**[nickvazz](https://github.com/dagster-io/dagster/commits?author=nickvazz)!**
- [dagster-airbyte] When loading assets from an Airbyte instance using `load_assets_from_airbyte_instance`, users can now optionally customize asset names using `connector_to_asset_key_fn`.
- [dagster-fivetran] When loading assets from a Fivetran instance using `load_assets_from_fivetran_instance`, users can now alter the IO manager using `io_manager_key` or `connector_to_io_manager_key_fn`, and customize asset names using `connector_to_asset_key_fn`.

### Bugfixes

- Fixed a bug where terminating runs from a backfill would fail without notice.
- Executing a subset of ops within a job that specifies its config value directly on the job, it no longer attempts to use that config value as the default. The default is still presented in the editable interface in dagit.
- [dagit] The partition step run matrix now reflects historical step status instead of just the last run’s step status for a particular partition.

### Documentation

- Updated [Environment variables and secrets docs](https://docs.dagster.io/guides/dagster/using-environment-variables-and-secrets) with info/instructions for using local `.env` files
- Added [a new example test to the Testing docs](https://docs.dagster.io/concepts/testing#testing-loading-repository-definitions). This test verifies if Dagster code loads correctly by loading a Dagster repository and its definitions.

# 1.0.17 (core) / 0.16.17 (libraries)

### New

- With the new `asset_selection` parameter on `@sensor` and `SensorDefinition`, you can now define a sensor that directly targets a selection of assets, instead of targeting a job.
- `materialize` and `materialize_to_memory` now accept a `raise_on_error` argument, which allows you to determine whether to raise an Error if the run hits an error or just return as failed.
- (experimental) Dagster now supports multi-dimensional asset partitions, through a new `MultiPartitionsDefinition` object. An optional schema migration enables support for this feature (run via `dagster instance migrate`). Users who are not using this feature do not need to run the migration.
- You can now launch a run that targets a range of asset partitions, by supplying the "dagster/asset_partition_range_start" and "dagster/asset_partition_range_end" tags.
- [dagit] Asset and op graphs in Dagit now show integration logos, making it easier to identify assets backed by notebooks, DBT, Airbyte, and more.
- [dagit] a `-db-pool-recycle` cli flag (and dbPoolRecycle helm option) have been added to control how long the pooled connection dagit uses persists before recycle. The default of 1 hour is now respected by postgres (mysql previously already had a hard coded 1hr setting). Thanks **[@adam-bloom](https://github.com/adam-bloom)**!
- [dagster-airbyte] Introduced the ability to specify output IO managers when using `load_assets_from_airbyte_instance` and `load_assets_from_airbyte_project`.
- [dagster-dbt] the `dbt_cloud_resource` resource configuration `account_id` can now be sourced from the environment. Thanks **[@sowusu-ba](https://github.com/sowusu-ba)**!
- [dagster-duckdb] The DuckDB integration improvements: PySpark DataFrames are now fully supported, “schema” can be specified via IO Manager config, and API documentation has been improved to include more examples
- [dagster-fivetran] Introduced experimental `load_assets_from_fivetran_instance` helper which automatically pulls assets from a Fivetran instance.
- [dagster-k8s] Fixed an issue where setting the `securityContext` configuration of the Dagit pod in the Helm chart didn’t apply to one of its containers. Thanks **[@jblawatt](https://github.com/jblawatt)**!

### Bugfixes

- Fixed a bug that caused the `asset_selection` parameter of `RunRequest` to not be respected when used inside a schedule.
- Fixed a bug with health checks during delayed Op retries with the k8s_executor and docker_executor.
- [dagit] The asset graph now live-updates when assets fail to materialize due to op failures.
- [dagit] The "Materialize" button now respects the backfill permission for multi-run materializations.
- [dagit] Materializations without metadata are padded correctly in the run logs.
- [dagster-aws] Fixed an issue where setting the value of `task_definition` field in the `EcsRunLauncher` to an environment variable stopped working.
- [dagster-dbt] Add exposures in `load_assets_from_dbt_manifest`. This fixed then error when `load_assets_from_dbt_manifest` failed to load from dbt manifest with exposures. Thanks **[@sowusu-ba](https://github.com/sowusu-ba)**!
- [dagster-duckdb] In some examples, the duckdb config was incorrectly specified. This has been fixed.

### Breaking Changes

- The behavior of the experimental asset reconciliation sensor, which is accessible via `build_asset_reconciliation_sensor` has changed to be more focused on reconciliation. It now materializes assets that have never been materialized before and avoids materializing assets that are “Upstream changed”. The `build_asset_reconciliation_sensor` API no longer accepts `wait_for_in_progress_runs` and `wait_for_all_upstream` arguments.

### Documentation

- Added documentation outlining [environment variable declaration and usage in Dagster code](https://docs.dagster.io/guides/dagster/using-environment-variables-and-secrets), including how to pass secrets.
- Fixed a typo on Dagster Instance page. Thanks **[@domsj](https://github.com/domsj)**!

# 1.0.16 (core) / 0.16.16 (libraries)

### New

- [dagit] The new Overview and Workspace pages have been enabled for all users, after being gated with a feature flag for the last several releases. These changes include design updates, virtualized tables, and more performant querying.
  - The top navigation has been updated to improve space allocation, with main nav links moved to the left.
  - “Overview” is the new Dagit home page and “factory floor” view, were you can find the run timeline, which now offers time-based pagination. The Overview section also contains pages with all of your jobs, schedules, sensors, and backfills. You can filter objects by name, and collapse or expand repository sections.
  - “Workspace” has been redesigned to offer a better summary of your repositories, and to use the same performant table views, querying, and filtering as in the Overview pages.
- `@asset` and `@multi_asset` now accept a `retry_policy` argument. (Thanks @adam-bloom!)
- When loading an input that depends on multiple partitions of an upstream asset, the `fs_io_manager` will now return a dictionary that maps partition keys to the stored values for those partitions. (Thanks @andrewgryan!).
- `JobDefinition.execute_in_process` now accepts a `run_config` argument even when the job is partitioned. If supplied, the run config will be used instead of any config provided by the job’s `PartitionedConfig`.
- The `run_request_for_partition` method on jobs now accepts a `run_config` argument. If supplied, the run config will be used instead of any config provided by the job’s `PartitionedConfig`.
- The new `NotebookMetadataValue` can be used to report the location of executed jupyter notebooks, and Dagit will be able to render the notebook.
- Resolving asset dependencies within a group now works with multi-assets, as long as all the assets within the multi-asset are in the same group. (Thanks @peay!)
- UPathIOManager, a filesystem-agnostic IOManager base class has been added - (Thanks @danielgafni!)
- A threadpool option has been added for the scheduler daemon. This can be enabled via your `dagster.yaml` file; check out the [docs](https://docs.dagster.io/deployment/dagster-instance#schedule-evaluation).
- The default LocalComputeLogManager will capture compute logs by process instead of by step. This means that for the `in_process` executor, where all steps are executed in the same process, the captured compute logs for all steps in a run will be captured in the same file.
- [dagstermill] Added `define_dagstermill_asset` which loads a notebook as an asset.
- [dagster-airflow] `make_dagster_job_from_airflow_dag` now supports airflow 2, there is also a new mock_xcom parameter that will mock all calls to made by operators to xcom.
- [helm] volume and volumeMount sections have been added for the dagit and daemon sections of the helm chart.

### Bugfixes

- For partitioned asset jobs whose config is a hardcoded dictionary (rather than a `PartitionedConfig`), previously `run_request_for_partition` would produce a run with no config. Now, the run has the hardcoded dictionary as its config.
- Previously, asset inputs would be resolved to upstream assets in the same group that had the same name, even if the asset input already had a key prefix. Now, asset inputs are only resolved to upstream assets in the same group if the input path only has a single component.
- Previously, asset inputs could get resolved to outputs of the same `AssetsDefinition`, through group-based asset dependency resolution, which would later error because of a circular dependency. This has been fixed.
- Previously, the “Partition Status” and “Backfill Status” fields on the Backfill page in dagit were always incomplete and showed missing partitions. This has been fixed to accurately show the status of the backfill runs.
- Executors now compress step worker arguments to avoid CLI length limits with large DAGs.
- [dagit] When viewing the config dialog for a run with a very long config, scrolling was broken and the “copy” button was not visible. This has been fixed.
- [dagster-msteams] Longer messages can now be used in Teams HeroCard - thanks `@jayhale`

### Documentation

- API docs for InputContext have been improved - (Thanks @peay!)
- [dagster-snowflake] Improved documentation for the Snowflake IO manager

# 1.0.15 (core) / 0.16.15 (libraries)

### New

- [dagit] The run timeline now shows all future schedule ticks for the visible time window, not just the next ten ticks.
- [dagit] Asset graph views in Dagit refresh as materialization events arrive, making it easier to watch your assets update in real-time.
- [dagster-airbyte] Added support for basic auth login to the Airbyte resource.
- [Configuring a Python Log Level](https://docs.dagster.io/concepts/logging/python-logging#configuring-a-python-log-level-) will now also apply to system logs created by Dagster during a run.

### Bugfixes

- Fixed a bug that broke asset partition mappings when using the `key_prefix` with methods like `load_assets_from_modules`.
- [dagster-dbt] When running dbt Cloud jobs with the dbt_cloud_run_op, the op would emit a failure if the targeted job did not create a run_results.json artifact, even if this was the expected behavior. This has been fixed.
- Improved performance by adding database indexes which should speed up the run view as well as a range of asset-based queries. These migrations can be applied by running `dagster instance migrate`.
- An issue that would cause schedule/sensor latency in the daemon during workspace refreshes has been resolved.
- [dagit] Shift-clicking Materialize for partitioned assets now shows the asset launchpad, allowing you to launch execution of a partition with config.

### Community Contributions

- Fixed a bug where asset keys with `-` were not being properly sanitized in some situations. Thanks @peay!
- [dagster-airbyte] A list of connection directories can now be specified in `load_assets_from_airbyte_project`. Thanks @adam-bloom!
- [dagster-gcp] Dagster will now retry connecting to GCS if it gets a `ServiceUnavailable` error. Thanks @cavila-evoliq!
- [dagster-postgres] Use of SQLAlchemy engine instead of psycopg2 when subscribing to PostgreSQL events. Thanks @peay!

### Experimental

- [dagster-dbt] Added a `display_raw_sql` flag to the dbt asset loading functions. If set to False, this will remove the raw sql blobs from the asset descriptions. For large dbt projects, this can significantly reduce the size of the generated workspace snapshots.
- [dagit] A “New asset detail pages” feature flag available in Dagit’s settings allows you to preview some upcoming changes to the way historical materializations and partitions are viewed.

# 1.0.14 (core) / 0.16.14 (libraries)

### New

- Tags can now be provided to an asset reconciliation sensor and will be applied to all RunRequests returned by the sensor.
- If you don’t explicitly specify a DagsterType on a graph input, but all the inner inputs that the graph input maps to have the same DagsterType, the graph input’s DagsterType will be set to the the DagsterType of the inner inputs.
- [dagster-airbyte] `load_assets_from_airbyte_project` now caches the project data generated at repo load time so it does not have to be regenerated in subprocesses.
- [dagster-airbyte] Output table schema metadata is now generated at asset definition time when using `load_assets_from_airbyte_instance` or `load_assets_from_airbyte_project`.
- [dagit] The run timeline now groups all jobs by repository. You can collapse or expand each repository in this view by clicking the repository name. This state will be preserved locally. You can also hold `Shift` while clicking the repository name, and all repository groups will be collapsed or expanded accordingly.
- [dagit] In the launchpad view, a “Remove all” button is now available once you have accrued three or more tabs for that job, to make it easier to clear stale configuration tabs from view.
- [dagit] When scrolling through the asset catalog, the toolbar is now sticky. This makes it simpler to select multiple assets and materialize them without requiring you to scroll back to the top of the page.
- [dagit] A “Materialize” option has been added to the action menu on individual rows in the asset catalog view.
- [dagster-aws] The `EcsRunLauncher` now allows you to pass in a dictionary in the `task_definition` config field that specifies configuration for the task definition of the launched run, including role ARNs and a list of sidecar containers to include. Previously, the task definition could only be configured by passing in a task definition ARN or by basing the the task definition off of the task definition of the ECS task launching the run. See the [docs](https://docs.dagster.io/_apidocs/libraries/dagster-aws#dagster_aws.ecs.EcsRunLauncher) for the full set of available config.

### Bugfixes

- Previously, yielding a `SkipReason` within a multi-asset sensor (experimental) would raise an error. This has been fixed.
- [dagit] Previously, if you had a partitioned asset job and supplied a hardcoded dictionary of config to `define_asset_job`, you would run into a `CheckError` when launching the job from Dagit. This has been fixed.
- [dagit] When viewing the Runs section of Dagit, the counts displayed in the tabs (e.g. “In progress”, “Queued”, etc.) were not updating on a poll interval. This has been fixed.

# 1.0.13 (core) / 0.16.13 (libraries)

### New

- `AssetMaterialization` now has a `metadata` property, which allows accessing the materialization’s metadata as a dictionary.
- `DagsterInstance` now has a `get_latest_materialization_event` method, which allows fetching the most recent materialization event for a particular asset key.
- `RepositoryDefinition.load_asset_value` and `AssetValueLoader.load_asset_value` now work with IO managers whose `load_input` implementation accesses the `op_def` and `name` attributes on the `InputContext`.
- `RepositoryDefinition.load_asset_value` and `AssetValueLoader.load_asset_value` now respect the `DAGSTER_HOME` environment variable.
- `InMemoryIOManager`, the `IOManager` that backs `mem_io_manager`, has been added to the public API.
- The `multi_asset_sensor` (experimental) now supports marking individual partitioned materializations as “consumed”. Unconsumed materializations will appear in future calls to partitioned context methods.
- The `build_multi_asset_sensor_context` testing method (experimental) now contains a flag to set the cursor to the newest events in the Dagster instance.
- `TableSchema` now has a static constructor that enables building it from a dictionary of column names to column types.
- Added a new CLI command `dagster run migrate-repository` which lets you migrate the run history for a given job from one repository to another. This is useful to preserve run history for a job when you have renamed a repository, for example.
- [dagit] The run timeline view now shows jobs grouped by repository, with each repository section collapsible. This feature was previously gated by a feature flag, and is now turned on for everyone.
- [dagster-airbyte] Added option to specify custom request params to the Airbyte resource, which can be used for auth purposes.
- [dagster-airbyte] When loading Airbyte assets from an instance or from YAML, a filter function can be specified to ignore certain connections.
- [dagster-airflow] `DagsterCloudOperator` and `DagsterOperator` now support Airflow 2. Previously, installing the library on Airflow 2 would break due to an import error.
- [dagster-duckdb] A new integration with DuckDB allows you to store op outputs and assets in an in-process database.

### Bugfixes

- Previously, if retries were exceeded when running with `execute_in_process`, no error would be raised. Now, a `DagsterMaxRetriesExceededError` will be launched off.
- [dagster-airbyte] Fixed generating assets for Airbyte normalization tables corresponding with nested union types.
- [dagster-dbt] When running assets with `load_assets_from_...(..., use_build=True)`, AssetObservation events would be emitted for each test. These events would have metadata fields which shared names with the fields added to the AssetMaterialization events, causing confusing historical graphs for fields such as Compilation Time. This has been fixed.
- [dagster-dbt] The name for the underlying op for `load_assets_from_...` was generated in a way which was non-deterministic for dbt projects which pulled in external packages, leading to errors when executing across multiple processes. This has been fixed.

### Dependency changes

- [dagster-dbt] The package no longer depends on pandas and dagster-pandas.

### Community Contributions

- [dagster-airbyte] Added possibility to change request timeout value when calling Airbyte. Thanks @FransDel!
- [dagster-airflow] Fixed an import error in `dagster_airflow.hooks`. Thanks @bollwyvl!
- [dagster-gcp] Unpin Google dependencies. `dagster-gcp` now supports google-api-python-client 2.x. Thanks @amarrella!
- [dagstermill] Fixed an issue where DagsterTranslator was missing an argument required by newer versions of papermill. Thanks @tizz98!

### Documentation

- Added an example, underneath examples/assets_smoke_test, that shows how to write a smoke test that feeds empty data to all the transformations in a data pipeline.
- Added documentation for `build_asset_reconciliation_sensor`.
- Added documentation for monitoring partitioned materializations using the `multi_asset_sensor` and kicking off subsequent partitioned runs.
- [dagster-cloud] Added documentation for running the Dagster Cloud Docker agent with Docker credential helpers.
- [dagster-dbt] The class methods of the dbt_cli_resource are now visible in the API docs for the dagster-dbt library.
- [dagster-dbt] Added a step-by-step tutorial for using dbt models with Dagster software-defined assets

# 1.0.12 (core) / 0.16.12 (libraries)

### New

- The `multi_asset_sensor` (experimental) now accepts an `AssetSelection` of assets to monitor. There are also minor API updates for the multi-asset sensor context.
- `AssetValueLoader`, the type returned by `RepositoryDefinition.get_asset_value_loader` is now part of Dagster’s public API.
- `RepositoryDefinition.load_asset_value` and `AssetValueLoader.load_asset_value` now support a `partition_key` argument.
- `RepositoryDefinition.load_asset_value` and `AssetValueLoader.load_asset_value` now work with I/O managers that invoke `context.upstream_output.asset_key`.
- When running Dagster locally, the default amount of time that the system waits when importing user code has been increased from 60 seconds to 180 seconds, to avoid false positives when importing code with heavy dependencies or large numbers of assets. This timeout can be configured in `dagster.yaml` as follows:

```yaml
code_servers:
  local_startup_timeout: 120
```

- [dagit] The “Status” section has been renamed to “Deployment”, to better reflect that this section of the app shows deployment-wide information.
- [dagit] When viewing the compute logs for a run and choosing a step to filter on, there is now a search input to make it easier to find the step you’re looking for.
- [dagster-aws] The EcsRunLauncher can now launch runs in ECS clusters using both Fargate and EC2 capacity providers. See the [Deploying to ECS docs](http://docs.dagster.io/deployment/guides/aws#customizing-the-launched-runs-task) for more information.
- [dagster-airbyte] Added the `load_assets_from_airbyte_instance` function which automatically generates asset definitions from an Airbyte instance. For more details, see the [new Airbyte integration guide](https://docs.dagster.io/integrations/airbyte).
- [dagster-airflow] Added the `DagsterCloudOperator` and `DagsterOperator` , which are airflow operators that enable orchestrating dagster jobs, running on either cloud or OSS dagit instances, from Apache Airflow.

### Bugfixes

- Fixed a bug where if resource initialization failed for a dynamic op, causing other dynamic steps to be skipped, those skipped dynamic steps would be ignored when retrying from failure.
- Previously, some invocations within the Dagster framework would result in warnings about deprecated metadata APIs. Now, users should only see warnings if their code uses deprecated metadata APIs.
- How the daemon process manages its understanding of user code artifacts has been reworked to improve memory consumption.
- [dagit] The partition selection UI in the Asset Materialization modal now allows for mouse selection and matches the UI used for partitioned op jobs.
- [dagit] Sidebars in Dagit shrink more gracefully on small screens where headers and labels need to be truncated.
- [dagit] Improved performance for loading runs with >10,000 logs
- [dagster-airbyte] Previously, the `port` configuration in the `airbyte_resource` was marked as not required, but if it was not supplied, an error would occur. It is now marked as required.
- [dagster-dbt] A change made to the manifest.json schema in dbt 1.3 would result in an error when using `load_assets_from_dbt_project` or `load_assets_from_manifest_json`. This has been fixed.
- [dagster-postgres] connections that fail due to **`sqlalchemy.exc.TimeoutError`** now retry

### Breaking Changes

- [dagster-aws] The `redshift_resource` no longer accepts a `schema` configuration parameter. Previously, this parameter would error whenever used, because Redshift connections do not support this parameter.

### Community Contributions

- We now reference the correct method in the "loading asset values outside of Dagster runs" example (thank you Peter A. I. Forsyth!)
- We now reference the correct test directory in the “Create a New Project” documentation (thank you Peter A. I. Forsyth!)
- [dagster-pyspark] dagster-pyspark now contains a `LazyPysparkResource` that only initializes a spark session once it’s accessed (thank you @zyd14!)

### Experimental

- The new `build_asset_reconciliation_sensor` function accepts a set of software-defined assets and returns a sensor that automatically materializes those assets after their parents are materialized.
- [dagit] A new "groups-only" asset graph feature flag allows you to zoom way out on the global asset graph, collapsing asset groups into smaller nodes you can double-click to expand.

# 1.0.11 (core) / 0.16.11 (libraries)

### New

- `RepositoryDefinition` now exposes a `load_asset_value` method, which accepts an asset key and invokes the asset’s I/O manager’s `load_input` function to load the asset as a Python object. This can be used in notebooks to do exploratory data analysis on assets.
- Methods to fetch a list of partition keys from an input/output `PartitionKeyRange` now exist on the op execution context and input/output context.
- [dagit] On the Instance Overview page, batched runs in the run timeline view will now proportionally reflect the status of the runs in the batch instead of reducing all run statuses to a single color.
- [dagster-dbt] [dagster-snowflake] You can now use the Snowflake IO manager with dbt assets, which allows them to be loaded from Snowflake into Pandas DataFrames in downstream steps.
- The dagster package’s pin of the alembic package is now much less restrictive.

### Bugfixes

- The sensor daemon when using threads will no longer evaluate the next tick for a sensor if the previous one is still in flight. This resolves a memory leak in the daemon process.
- The scheduler will no longer remove tracked state for automatically running schedules when they are absent due to a workspace load error.
- The way user code severs manage repository definitions has been changed to more efficiently serve requests.
- The `@multi_asset` decorator now respects its `config_schema` parameter.
- [dagit] Config supplied to `define_asset_job` is now prefilled in the modal that pops up when you click the Materialize button on an asset job page, so you can quickly adjust the defaults.
- [dagster-dbt] Previously, `DagsterDbtCliError`s produced from the dagster-dbt library would contain large serialized objects representing the raw unparsed logs from the relevant cli command. Now, these messages will contain only the parsed version of these messages.
- Fixed an issue where the `deploy_ecs` example didn’t work when built and deployed on an M1 Mac.

### Community Contributions

- [dagster-fivetran] The `resync_parameters` configuration on the `fivetran_resync_op` is now optional, enabling triggering historical re\*syncs for connectors. Thanks @dwallace0723!

### Documentation

- Improved API documentation for the Snowflake resource.

# 1.0.10 (core) / 0.16.10 (libraries)

### New

- Run status sensors can now monitor all runs in a Dagster Instance, rather than just runs from jobs within a single repository. You can enable this behavior by setting `monitor_all_repositories=True` in the run status sensor decorator.
- The `run_key` argument on `RunRequest` and `run_request_for_partition` is now optional.
- [dagster-databricks] A new “verbose_logs” config option on the databricks_pyspark_step_launcher makes it possible to silence non-critical logs from your external steps, which can be helpful for long-running, or highly parallel operations (thanks @zyd14!)
- [dagit] It is now possible to delete a run in Dagit directly from the run page. The option is available in the dropdown menu on the top right of the page.
- [dagit] The run timeline on the Workspace Overview page in Dagit now includes ad hoc asset materialization runs.

### Bugfixes

- Fixed a set of bugs in `multi_asset_sensor` where the cursor would fail to update, and materializations would be returned out of order for `latest_materialization_records_by_partition`.
- Fixed a bug that caused failures in runs with time-partitioned asset dependencies when the PartitionsDefinition had an offset that wasn’t included in the date format. E.g. a daily-partitioned asset with an hour offset, whose date format was `%Y-%m-%d`.
- An issue causing code loaded by file path to import repeatedly has been resolved.
- To align with best practices, singleton comparisons throughout the codebase have been converted from (e.g.) `foo == None` to `foo is None` (thanks @chrisRedwine!).
- [dagit] In backfill jobs, the “Partition Set” column would sometimes show an internal `__ASSET_JOB` name, rather than a comprehensible set of asset keys. This has been fixed.
- [dagit] It is now possible to collapse all Asset Observation rows on the AssetDetails page.
- [dagster-dbt] Fixed issue that would cause an error when loading assets from dbt projects in which a source had a “\*” character in its name (e.g. BigQuery sharded tables)
- [dagster-k8s] Fixed an issue where the `k8s_job_op` would sometimes fail if the Kubernetes job that it creates takes a long time to create a pod.
- Fixed an issue where links to the compute logs for a run would sometimes fail to load.
- [dagster-k8s] The `k8s_job_executor` now uses environment variables in place of CLI arguments to avoid limits on argument size with large dynamic jobs.

### Documentation

- Docs added to explain subsetting graph-backed assets. You can use this feature following the documentation [here](https://docs.dagster.io/concepts/assets/graph-backed-assets).
- UI updated to reflect separate version schemes for mature core Dagster packages and less mature integration libraries

# 1.0.9 (core) / 0.16.9 (libraries)

### New

- The `multi_asset_sensor` (experimental) now has improved capabilities to monitor asset partitions via a `latest_materialization_records_by_partition` method.
- Performance improvements for the Partitions page in Dagit.

### Bugfixes

- Fixed a bug that caused the op_config argument of `dagstermill.get_context` to be ignored
- Fixed a bug that caused errors when loading the asset details page for assets with time window partitions definitions
- Fixed a bug where assets sometimes didn’t appear in the Asset Catalog while in Folder view.
- [dagit] Opening the asset lineage tab no longer scrolls the page header off screen in some scenarios
- [dagit] The asset lineage tab no longer attempts to materialize source assets included in the upstream / downstream views.
- [dagit] The Instance page Run Timeline no longer commingles runs with the same job name in different repositories
- [dagit] Emitting materializations with JSON metadata that cannot be parsed as JSON no longer crashes the run details page
- [dagit] Viewing the assets related to a run no longer shows the same assets multiple times in some scenarios
- [dagster-k8s] Fixed a bug with timeouts causing errors in `k8s_job_op`
- [dagster-docker] Fixed a bug with Op retries causing errors with the `docker_executor`

### Community Contributions

- [dagster-aws] Thanks @Vivanov98 for adding the `list_objects` method to `S3FakeSession`!

### Experimental

- [dagster-airbyte] Added an experimental function to automatically generate Airbyte assets from project YAML files. For more information, see the [dagster-airbyte docs](https://docs.dagster.io/_apidocs/libraries/dagster-airbyte).
- [dagster-airbyte] Added the forward_logs option to `AirbyteResource`, allowing users to disble forwarding of Airbyte logs to the compute log, which can be expensive for long-running syncs.
- [dagster-airbyte] Added the ability to generate Airbyte assets for [basic normalization](https://docs.airbyte.com/understanding-airbyte/basic-normalization/#nesting) tables generated as part of a sync.

### Documentation

- [dagster-dbt] Added a new guide focused on the dbt Cloud integration.
- Fixed a bug that was hiding display of some public methods in the API docs.
- Added documentation for [managing full deployments in Dagster Cloud](https://docs.dagster.io/dagster-cloud/managing-deployments/managing-deployments), including a [reference for deployment configuration options](https://docs.dagster.io/dagster-cloud/developing-testing/deployment-settings-reference).

# 1.0.8 (core) / 0.16.8 (libraries)

### New

- With the new `cron_schedule` argument to `TimeWindowPartitionsDefinition`, you can now supply arbitrary cron expressions to define time window-based partition sets.
- Graph-backed assets can now be subsetted for execution via `AssetsDefinition.from_graph(my_graph, can_subset=True)`.
- `RunsFilter` is now exported in the public API.
- [dagster-k8s] The `dagster-user-deployments.deployments[].schedulerName` Helm value for specifying custom Kubernetes schedulers will now also apply to run and step workers launched for the given user deployment. Previously it would only apply to the grpc server.

### Bugfixes

- In some situations, default asset config was ignored when a subset of assets were selected for execution. This has been fixed.
- Added a pin to `grpcio` in dagster to address an issue with the recent 0.48.1 grpcio release that was sometimes causing Dagster code servers to hang.
- Fixed an issue where the “Latest run” column on the Instance Status page sometimes displayed an older run instead of the most recent run.

### Community Contributions

- In addition to a single cron string, `cron_schedule` now also accepts a sequence of cron strings. If a sequence is provided, the schedule will run for the union of all execution times for the provided cron strings, e.g., `['45 23 * * 6', '30 9 * * 0]` for a schedule that runs at 11:45 PM every Saturday and 9:30 AM every Sunday. Thanks @erinov1!
- Added an optional boolean config `install_default_libraries` to `databricks_pyspark_step_launcher` . It allows to run Databricks jobs without installing the default Dagster libraries .Thanks @nvinhphuc!

### Experimental

- [dagster-k8s] Added additional configuration fields (`container_config`, `pod_template_spec_metadata`, `pod_spec_config`, `job_metadata`, and `job_spec_config`) to the experimental `k8s_job_op` that can be used to add additional configuration to the Kubernetes pod that is launched within the op.

# 1.0.7 (core) / 0.16.7 (libraries)

### New

- Several updates to the Dagit run timeline view: your time window preference will now be preserved locally, there is a clearer “Now” label to delineate the current time, and upcoming scheduled ticks will no longer be batched with existing runs.
- [dagster-k8s] `ingress.labels` is now available in the Helm chart. Any provided labels are appended to the default labels on each object (`helm.sh/chart`, `app.kubernetes.io/version`, and `app.kubernetes.io/managed-by`).
- [dagster-dbt] Added support for two types of dbt nodes: metrics, and ephemeral models.
- When constructing a `GraphDefinition` manually, InputMapping and OutputMapping objects should be directly constructed.

### Bugfixes

- [dagster-snowflake] Pandas is no longer imported when `dagster_snowflake` is imported. Instead, it’s only imported when using functionality inside `dagster-snowflake` that depends on pandas.
- Recent changes to `run_status_sensors` caused sensors that only monitored jobs in external repositories to also monitor all jobs in the current repository. This has been fixed.
- Fixed an issue where "unhashable type" errors could be spawned from sensor executions.
- [dagit] Clicking between assets in different repositories from asset groups and asset jobs now works as expected.
- [dagit] The DAG rendering of composite ops with more than one input/output mapping has been fixed.
- [dagit] Selecting a source asset in Dagit no longer produces a GraphQL error
- [dagit] Viewing “Related Assets” for an asset run now shows the full set of assets included in the run, regardless of whether they were materialized successfully.
- [dagit] The Asset Lineage view has been simplified and lets you know if the view is being clipped and more distant upstream/downstream assets exist.
- Fixed erroneous experimental warnings being thrown when using `with_resources` alongside source assets.

### Breaking Changes

- [dagit] The launchpad tab is no longer shown for Asset jobs. Asset jobs can be launched via the “Materialize All” button shown on the Overview tab. To provide optional configuration, hold shift when clicking “Materialize”.
- The arguments to `InputMapping` and `OutputMapping` APIs have changed.

### Community Contributions

- The `ssh_resource` can now accept configuration from environment variables. Thanks @[cbini](https://github.com/cbini)!
- Spelling corrections in `migrations.md`. Thanks @[gogi2811](https://github.com/gogi2811)!

# 1.0.6 (core) / 0.16.6 (libraries)

### New

- [dagit] nbconvert is now installed as an extra in Dagit.
- Multiple assets can be monitored for materialization using the `multi_asset_sensor` (experimental).
- Run status sensors can now monitor jobs in external repositories.
- The `config` argument of `define_asset_job` now works if the job contains partitioned assets.
- When configuring sqlite-based storages in dagster.yaml, you can now point to environment variables.
- When emitting `RunRequests` from sensors, you can now optionally supply an `asset_selection` argument, which accepts a list of `AssetKey`s to materialize from the larger job.
- [dagster-dbt] `load_assets_from_dbt_project` and `load_assets_from_dbt_manifest` now support the `exclude` parameter, allowing you to more precisely which resources to load from your dbt project (thanks @flvndh!)
- [dagster-k8s] `schedulerName` is now available for all deployments in the Helm chart for users who use a custom Kubernetes scheduler

### Bugfixes

- Previously, types for multi-assets would display incorrectly in Dagit when specified. This has been fixed.
- In some circumstances, viewing nested asset paths in Dagit could lead to unexpected empty states. This was due to incorrect slicing of the asset list, and has been fixed.
- Fixed an issue in Dagit where the dialog used to wipe materializations displayed broken text for assets with long paths.
- [dagit] Fixed the Job page to change the latest run tag and the related assets to bucket repository-specific jobs. Previously, runs from jobs with the same name in different repositories would be intermingled.
- Previously, if you launched a backfill for a subset of a multi-asset (e.g. dbt assets), all assets would be executed on each run, instead of just the selected ones. This has been fixed.
- [dagster-dbt] Previously, if you configured a `select` parameter on your `dbt_cli_resource` , this would not get passed into the corresponding invocations of certain `context.resources.dbt.x()` commands. This has been fixed.

# 1.0.4 (core) / 0.16.4 (libraries)

### New

- Assets can now be materialized to storage conditionally by setting `output_required=False`. If this is set and no result is yielded from the asset, Dagster will not create an asset materialization event, the I/O manager will not be invoked, downstream assets will not be materialized, and asset sensors monitoring the asset will not trigger.
- `JobDefinition.run_request_for_partition` can now be used inside sensors that target multiple jobs (Thanks Metin Senturk!)
- The environment variable `DAGSTER_GRPC_TIMEOUT_SECONDS` now allows for overriding the default timeout for communications between host processes like dagit and the daemon and user code servers.
- Import time for the `dagster` module has been reduced, by approximately 50% in initial measurements.
- `AssetIn` now accepts a `dagster_type` argument, for specifying runtime checks on asset input values.
- [dagit] The column names on the Activity tab of the asset details page no longer reference the legacy term “Pipeline”.
- [dagster-snowflake] The `execute_query` method of the snowflake resource now accepts a `use_pandas_result` argument, which fetches the result of the query as a Pandas dataframe. (Thanks @swotai!)
- [dagster-shell] Made the execute and execute_script_file utilities in dagster_shell part of the public API (Thanks Fahad Khan!)
- [dagster-dbt] `load_assets_from_dbt_project` and `load_assets_from_dbt_manifest` now support the `exclude` parameter. (Thanks @flvndh!)

### Bugfixes

- [dagit] Removed the x-frame-options response header from Dagit, allowing the Dagit UI to be rendered in an iframe.
- [fully-featured project example] Fixed the duckdb IO manager so the comment_stories step can load data successfully.
- [dagster-dbt] Previously, if a `select` parameter was configured on the `dbt_cli_resource`, it would not be passed into invocations of `context.resources.dbt.run()` (and other similar commands). This has been fixed.
- [dagster-ge] An incompatibility between `dagster_ge_validation_factory` and dagster 1.0 has been fixed.
- [dagstermill] Previously, updated arguments and properties to `DagstermillExecutionContext` were not exposed. This has since been fixed.

### Documentation

- The integrations page on the docs site now has a section for links to community-hosted integrations. The first linked integration is @silentsokolov’s Vault integration.

# 1.0.3 (core) / 0.16.3 (libraries)

### New

- `Failure` now has an `allow_retries` argument, allowing a means to manually bypass retry policies.
- `dagstermill.get_context` and `dagstermill.DagstermillExecutionContext` have been updated to reflect stable dagster-1.0 APIs. `pipeline`/`solid` referencing arguments / properties will be removed in the next major version bump of `dagstermill`.
- `TimeWindowPartitionsDefinition` now exposes a `get_cron_schedule` method.

### Bugfixes

- In some situations where an asset was materialized and that asset that depended on a partitioned asset, and that upstream partitioned asset wasn’t part of the run, the partition-related methods of InputContext returned incorrect values or failed erroneously. This was fixed.
- Schedules and sensors with the same names but in different repositories no longer affect each others idempotence checks.
- In some circumstances, reloading a repository in Dagit could lead to an error that would crash the page. This has been fixed.

### Community Contributions

- @will-holley added an optional `key` argument to GCSFileManager methods to set the GCS blob key, thank you!
- Fix for sensors in [fully featured example](https://docs.dagster.io/guides/dagster/example_project#fully-featured-project), thanks @pwachira!

### Documentation

- New documentation for getting started with Dagster Cloud, including:
  - [Serverless deployment documentation](https://docs.dagster.io/dagster-cloud/getting-started/getting-started-with-serverless-deployment)
  - [Hybrid deployment documentation](https://docs.dagster.io/dagster-cloud/getting-started/getting-started-with-hybrid-deployment)

# 1.0.2 (core) / 0.16.2 (libraries)

### New

- When the workpace is updated, a notification will appear in Dagit, and the Workspace tab will automatically refresh.

### Bugfixes

- Restored the correct version mismatch warnings between dagster core and dagster integration libraries
- `Field.__init__` has been typed, which resolves an error that pylance would raise about `default_value`
- Previously, `dagster_type_materializer` and `dagster_type_loader` expected functions to take a context argument from an internal dagster import. We’ve added `DagsterTypeMaterializerContext` and `DagsterTypeLoaderContext` so that functions annotated with these decorators can annotate their arguments properly.
- Previously, a single-output op with a return description would not pick up the description of the return. This has been rectified.

### Community Contributions

- Fixed the `dagster_slack` documentation examples. Thanks @ssingh13-rms!

### Documentation

- New documentation for [Dagster Cloud environment variables](https://docs.dagster.io/dagster-cloud/developing-testing/environment-variables).
- The full list of APIs removed in 1.0 has been added to the [migration guide](https://github.com/dagster-io/dagster/blob/master/MIGRATION.md).

# 1.0.1 (core) / 0.16.1 (libraries)

### Bugfixes

- Fixed an issue where Dagster libraries would sometimes log warnings about mismatched versions despite having the correct version loaded.

### Documentation

- The [Dagster Cloud docs](https://docs.dagster.io/dagster-cloud) now live alongside all the other Dagster docs! Check them out by nagivating to Deployment > Cloud.

# 1.0.0 (core) / 0.16.0 (libraries)

## Major Changes

- A docs site overhaul! Along with tons of additional content, the existing pages have been significantly edited and reorganized to improve readability.
- All Dagster [examples](https://github.com/dagster-io/dagster/tree/master/examples)[](https://github.com/dagster-io/dagster/tree/master/examples) are revamped with a consistent project layout, descriptive names, and more helpful README files.
- A new `dagster project `CLI contains commands for bootstrapping new Dagster projects and repositories:
  - `dagster project scaffold` creates a folder structure with a single Dagster repository and other files such as workspace.yaml. This CLI enables you to quickly start building a new Dagster project with everything set up.
  - `dagster project from-example` downloads one of the Dagster examples. This CLI helps you to quickly bootstrap your project with an officially maintained example. You can find the available examples via `dagster project list-examples`.
  - Check out [Create a New Project](https://docs.dagster.io/getting-started/create-new-project) for more details.
- A `default_executor_def` argument has been added to the `@repository` decorator. If specified, this will be used for any jobs (asset or op) which do not explicitly set an `executor_def`.
- A `default_logger_defs` argument has been added to the `@repository` decorator, which works in the same way as `default_executor_def`.
- A new `execute_job` function presents a Python API for kicking off runs of your jobs.
- Run status sensors may now yield `RunRequests`, allowing you to kick off a job in response to the status of another job.
- When loading an upstream asset or op output as an input, you can now set custom loading behavior using the `input_manager_key` argument to AssetIn and In.
- In the UI, the global lineage graph has been brought back and reworked! The graph keeps assets in the same group visually clustered together, and the query bar allows you to visualize a custom slice of your asset graph.

## Breaking Changes and Deprecations

### Legacy API Removals

In 1.0.0, a large number of previously-deprecated APIs have been fully removed. A full list of breaking changes and deprecations, alongside instructions on how to migrate older code, can be found in [MIGRATION.md](https://github.com/dagster-io/dagster/blob/master/MIGRATION.md). At a high level:

- The `solid` and `pipeline` APIs have been removed, along with references to them in extension libraries, arguments, and the CLI _(deprecated in `0.13.0)`_.
- The `AssetGroup` and `build_asset_job` APIs, and a host of deprecated arguments to asset-related functions, have been removed _(deprecated in `0.15.0`)_.
- The `EventMetadata` and `EventMetadataEntryData` APIs have been removed _(deprecated in `0.15.0`)_.

### Deprecations

- `dagster_type_materializer` and `DagsterTypeMaterializer` have been marked experimental and will likely be removed within a 1.x release. Instead, use an `IOManager`.
- `FileManager` and `FileHandle` have been marked experimental and will likely be removed within a 1.x release.

### Other Changes

- As of 1.0.0, Dagster no longer guarantees support for python 3.6. This is in line with [PEP 494](https://peps.python.org/pep-0494/), which outlines that 3.6 has reached end of life.
- **[planned]** In an upcoming 1.x release, we plan to make a change that renders values supplied to `configured` in Dagit. Up through this point, values provided to `configured` have not been sent anywhere outside the process where they were used. This change will mean that, like other places you can supply configuration, `configured` is not a good place to put secrets: **You should not include any values in configuration that you don't want to be stored in the Dagster database and displayed inside Dagit.**
- `fs_io_manager`, `s3_pickle_io_manager`, and `gcs_pickle_io_manager`, and `adls_pickle_io_manager` no longer write out a file or object when handling an output with the `None` or `Nothing` type.
- The `custom_path_fs_io_manager` has been removed, as its functionality is entirely subsumed by the `fs_io_manager`, where a custom path can be specified via config.
- The default `typing_type` of a `DagsterType` is now `typing.Any` instead of `None`.
- Dagster’s integration libraries haven’t yet achieved the same API maturity as Dagster core. For this reason, all integration libraries will remain on a pre-1.0 (0.16.x) versioning track for the time being. However, 0.16.x library releases remain fully compatible with Dagster 1.x. In the coming months, we will graduate integration libraries one-by-one to the 1.x versioning track as they achieve API maturity. If you have installs of the form:

```
pip install dagster=={DAGSTER_VERSION} dagster-somelibrary=={DAGSTER_VERSION}
```

this should be converted to:

```
pip install dagster=={DAGSTER_VERSION} dagster-somelibrary
```

to make sure the correct library version is installed.

## New since 0.15.8

- [dagster-databricks] When using the `databricks_pyspark_step_launcher` the events sent back to the host process are now compressed before sending, resulting in significantly better performance for steps which produce a large number of events.
- [dagster-dbt] If an error occurs in `load_assets_from_dbt_project` while loading your repository, the error message in Dagit will now display additional context from the dbt logs, instead of just `DagsterDbtCliFatalRuntimeError`.

### Bugfixes

- Fixed a bug that causes Dagster to ignore the `group_name` argument to `AssetsDefinition.from_graph` when a `key_prefix` argument is also present.
- Fixed a bug which could cause GraphQL errors in Dagit when loading repositories that contained multiple assets created from the same graph.
- Ops and software-defined assets with the `None` return type annotation are now given the `Nothing` type instead of the `Any` type.
- Fixed a bug that caused `AssetsDefinition.from_graph` and `from_op` to fail when invoked on a `configured` op.
- The `materialize` function, which is not experimental, no longer emits an experimental warning.
- Fixed a bug where runs from different repositories would be intermingled when viewing the runs for a specific repository-scoped job/schedule/sensor.
- [dagster-dbt] A regression was introduced in 0.15.8 that would cause dbt logs to show up in json format in the UI. This has been fixed.
- [dagster-databricks] Previously, if you were using the `databricks_pyspark_step_launcher`, and the external step failed to start, a `RESOURCE_DOES_NOT_EXIST` error would be surfaced, without helpful context. Now, in most cases, the root error causing the step to fail will be surfaced instead.

### Documentation

- New [guide](https://docs.dagster.io/guides/dagster/transitioning-data-pipelines-from-development-to-production) that walks through seamlessly transitioning code from development to production environments.
- New [guide](https://docs.dagster.io/guides/dagster/branch_deployments) that demonstrates using Branch Deployments to test Dagster code in your cloud environment without impacting your production data.

# 0.15.8

### New

- Software-defined asset config schemas are no longer restricted to `dict`s.
- The `OpDefinition` constructor now accept `ins` and `outs` arguments, to make direct construction easier.
- `define_dagstermill_op` accepts `ins` and `outs` in order to make direct construction easier.

### Bugfixes

- Fixed a bug where default configuration was not applied when assets were selected for materialization in Dagit.
- Fixed a bug where `RunRequests` returned from `run_status_sensors` caused the sensor to error.
- When supplying config to `define_asset_job`, an error would occur when selecting most asset subsets. This has been fixed.
- Fixed an error introduced in 0.15.7 that would prevent viewing the execution plan for a job re-execution from 0.15.0 → 0.15.6
- [dagit] The Dagit server now returns `500` http status codes for GraphQL requests that encountered an unexpected server error.
- [dagit] Fixed a bug that made it impossible to kick off materializations of partitioned asset if the `day_offset`, `hour_offset`, or `minute_offset` parameters were set on the asset’s partitions definition.
- [dagster-k8s] Fixed a bug where overriding the Kubernetes command to use to run a Dagster job by setting the `dagster-k8s/config` didn’t actually override the command.
- [dagster-datahub] Pinned version of `acryl-datahub` to avoid build error.

### Breaking Changes

- The constructor of `JobDefinition` objects now accept a config argument, and the `preset_defs` argument has been removed.

### Deprecations

- `DagsterPipelineRunMetadataValue` has been renamed to `DagsterRunMetadataValue`. `DagsterPipelineRunMetadataValue` will be removed in 1.0.

### Community Contributions

- Thanks to @hassen-io for fixing a broken link in the docs!

### Documentation

- `MetadataEntry` static methods are now marked as deprecated in the docs.
- `PartitionMapping`s are now included in the API reference.
- A dbt example and memoization example using legacy APIs have been removed from the docs site.

# 0.15.7

### New

- `DagsterRun` now has a `job_name` property, which should be used instead of `pipeline_name`.
- `TimeWindowPartitionsDefinition` now has a `get_partition_keys_in_range` method which returns a sequence of all the partition keys between two partition keys.
- `OpExecutionContext` now has `asset_partitions_def_for_output` and `asset_partitions_def_for_input` methods.
- Dagster now errors immediately with an informative message when two `AssetsDefinition` objects with the same key are provided to the same repository.
- `build_output_context` now accepts a `partition_key` argument that can be used when testing the `handle_output` method of an IO manager.

### Bugfixes

- Fixed a bug that made it impossible to load inputs using a DagsterTypeLoader if the InputDefinition had an `asset_key` set.
- Ops created with the `@asset` and `@multi_asset` decorators no longer have a top-level “assets” entry in their config schema. This entry was unused.
- In 0.15.6, a bug was introduced that made it impossible to load repositories if assets that had non-standard metadata attached to them were present. This has been fixed.
- [dagster-dbt] In some cases, using `load_assets_from_dbt_manifest` with a `select` parameter that included sources would result in an error. This has been fixed.
- [dagit] Fixed an error where a race condition of a sensor/schedule page load and the sensor/schedule removal caused a GraphQL exception to be raised.
- [dagit] The “Materialize” button no longer changes to “Rematerialize” in some scenarios
- [dagit] The live overlays on asset views, showing latest materialization and run info, now load faster
- [dagit] Typing whitespace into the launchpad Yaml editor no longer causes execution to fail to start
- [dagit] The explorer sidebar no longer displays “mode” label and description for jobs, since modes are deprecated.

### Community Contributions

- An error will now be raised if a `@repository` decorated function expects parameters. Thanks @roeij!

### Documentation

- The non-asset version of the Hacker News example, which lived inside `examples/hacker_news/`, has been removed, because it hadn’t received updates in a long time and had drifted from best practices. The asset version is still there and has an updated README. Check it out [here](https://github.com/dagster-io/dagster/tree/master/examples/hacker_news_assets)

# 0.15.6

### New

- When an exception is wrapped by another exception and raised within an op, Dagit will now display the full chain of exceptions, instead of stopping after a single exception level.
- A `default_logger_defs` argument has been added to the `@repository` decorator. Check out [the docs](https://docs.dagster.io/concepts/logging/loggers#specifying-default-repository-loggers) on specifying default loggers to learn more.
- `AssetsDefinition.from_graph` and `AssetsDefinition.from_op` now both accept a `partition_mappings` argument.
- `AssetsDefinition.from_graph` and `AssetsDefinition.from_op` now both accept a `metadata_by_output_name` argument.
- `define_asset_job` now accepts an `executor_def` argument.
- Removed package pin for `gql` in `dagster-graphql`.
- You can now apply a group name to assets produced with the `@multi_asset` decorator, either by supplying a `group_name` argument (which will apply to all of the output assets), or by setting the `group_name` argument on individual `AssetOut`s.
- `InputContext` and `OutputContext` now each have an `asset_partitions_def` property, which returns the `PartitionsDefinition` of the asset that’s being loaded or stored.
- `build_schedule_from_partitioned_job` now raises a more informative error when provided a non-partitioned asset job
- `PartitionMapping`, `IdentityPartitionMapping`, `AllPartitionMapping`, and `LastPartitionMapping` are exposed at the top-level `dagster` package. They're currently marked experimental.
- When a non-partitioned asset depends on a partitioned asset, you can now control which partitions of the upstream asset are used by the downstream asset, by supplying a `PartitionMapping`.
- You can now set `PartitionMappings` on `AssetIn`.
- [dagit] Made performance improvements to the loading of the partitions and backfill pages.
- [dagit] The Global Asset Graph is back by popular demand, and can be reached via a new “View global asset lineage ”link on asset group and asset catalog pages! The global graph keeps asset in the same group visually clustered together and the query bar allows you to visualize a custom slice of your asset graph.
- [dagit] Simplified the Content Security Policy and removed `frame-ancestors` restriction.
- [dagster-dbt] `load_assets_from_dbt_project` and `load_assets_from_dbt_manifest` now support a `node_info_to_group_name_fn` parameter, allowing you to customize which group Dagster will assign each dbt asset to.
- [dagster-dbt] When you supply a `runtime_metadata_fn` when loading dbt assets, this metadata is added to the default metadata that dagster-dbt generates, rather than replacing it entirely.
- [dagster-dbt] When you load dbt assets with `use_build_command=True`, seeds and snapshots will now be represented as Dagster assets. Previously, only models would be loaded as assets.

### Bugfixes

- Fixed an issue where runs that were launched using the `DockerRunLauncher` would sometimes use Dagit’s Python environment as the entrypoint to launch the run, even if that environment did not exist in the container.
- Dagster no longer raises a “Duplicate definition found” error when a schedule definition targets a partitioned asset job.
- Silenced some erroneous warnings that arose when using software-defined assets.
- When returning multiple outputs as a tuple, empty list values no longer cause unexpected exceptions.
- [dagit] Fixed an issue with graph-backed assets causing a GraphQL error when graph inputs were type-annotated.
- [dagit] Fixed an issue where attempting to materialize graph-backed assets caused a graphql error.
- [dagit] Fixed an issue where partitions could not be selected when materializing partitioned assets with associated resources.
- [dagit] Attempting to materialize assets with required resources now only presents the launchpad modal if at least one resource defines a config schema.

### Breaking Changes

- An op with a non-optional DynamicOutput will now error if no outputs are returned or yielded for that dynamic output.
- If an `Output` object is used to type annotate the return of an op, an Output object must be returned or an error will result.

### Community Contributions

- Dagit now displays the path of the output handled by `PickledObjectS3IOManager` in run logs and Asset view. Thanks @danielgafni

### Documentation

- The Hacker News example now uses stable 0.15+ asset APIs, instead of the deprecated 0.14.x asset APIs.
- Fixed the build command in the instructions for contributing docs changes.
- [dagster-dbt] The dagster-dbt integration guide now contains information on using dbt with Software-Defined Assets.

# 0.15.5

### New

- Added documentation and helm chart configuration for threaded sensor evaluations.
- Added documentation and helm chart configuration for tick retention policies.
- Added descriptions for default config schema. Fields like execution, loggers, ops, and resources are now documented.
- UnresolvedAssetJob objects can now be passed to run status sensors.
- [dagit] A new global asset lineage view, linked from the Asset Catalog and Asset Group pages, allows you to view a graph of assets in all loaded asset groups and filter by query selector and repo.
- [dagit] A new option on Asset Lineage pages allows you to choose how many layers of the upstream / downstream graph to display.
- [dagit] Dagit's DAG view now collapses large sets of edges between the same ops for improved readability and rendering performance.

### Bugfixes

- Fixed a bug with `materialize` that would cause required resources to not be applied correctly.
- Fixed issue that caused repositories to fail to load when `build_schedule_from_partitioned_job` and `define_asset_job` were used together.
- Fixed a bug that caused auto run retries to always use the `FROM_FAILURE` strategy
- Previously, it was possible to construct Software-Defined Assets from graphs whose leaf ops were not mapped to assets. This is invalid, as these ops are not required for the production of any assets, and would cause confusing behavior or errors on execution. This will now result in an error at definition time, as intended.
- Fixed issue where the run monitoring daemon could mark completed runs as failed if they transitioned quickly between STARTING and SUCCESS status.
- Fixed stability issues with the sensor daemon introduced in 0.15.3 that caused the daemon to fail heartbeat checks if the sensor evaluation took too long.
- Fixed issues with the thread pool implementation of the sensor daemon where race conditions caused the sensor to fire more frequently than the minimum interval.
- Fixed an issue with storage implementations using MySQL server version 5.6 which caused SQL syntax exceptions to surface when rendering the Instance overview pages in Dagit.
- Fixed a bug with the `default_executor_def` argument on repository where asset jobs that defined executor config would result in errors.
- Fixed a bug where an erroneous exception would be raised if an empty list was returned for a list output of an op.
- [dagit] Clicking the "Materialize" button for assets with configurable resources will now present the asset launchpad.
- [dagit] If you have an asset group and no jobs, Dagit will display it by default rather than directing you to the asset catalog.
- [dagit] DAG renderings of software-defined assets now display only the last component of the asset's key for improved readability.
- [dagit] Fixes a regression where clicking on a source asset would trigger a GraphQL error.
- [dagit] Fixed issue where the “Unloadable” section on the sensors / schedules pages in Dagit were populated erroneously with loadable sensors and schedules
- [dagster-dbt] Fixed an issue where an exception would be raised when using the dbt build command with Software-Defined Assets if a test was defined on a source.

### Deprecations

- Removed the deprecated dagster-daemon health-check CLI command

### Community Contributions

- TimeWindow is now exported from the dagster package (Thanks [@nvinhphuc](https://github.com/nvinhphuc)!)
- Added a fix to allow customization of slack messages (Thanks [@solarisa21](https://github.com/solarisa21)!)
- [dagster-databricks] The `databricks_pyspark_step_launcher` now allows you to configure the following (Thanks [@Phazure](https://github.com/Phazure)!):
  - the `aws_attributes` of the cluster that will be spun up for the step.
  - arbitrary environment variables to be copied over to databricks from the host machine, rather than requiring these variables to be stored as secrets.
  - job and cluster permissions, allowing users to view the completed runs through the databricks console, even if they’re kicked off by a service account.

### Experimental

- [dagster-k8s] Added `k8s_job_op` to launch a Kubernetes Job with an arbitrary image and CLI command. This is in contrast with the `k8s_job_executor`, which runs each Dagster op in a Dagster job in its own k8s job. This op may be useful when you need to orchestrate a command that isn't a Dagster op (or isn't written in Python). Usage:

  ```python
  from dagster_k8s import k8s_job_op

  my_k8s_op = k8s_job_op.configured({
   "image": "busybox",
   "command": ["/bin/sh", "-c"],
   "args": ["echo HELLO"],
   },
   name="my_k8s_op",
  )
  ```

- [dagster-dbt] The dbt asset-loading functions now support `partitions_def` and `partition_key_to_vars_fn` parameters, adding preliminary support for partitioned dbt assets. To learn more, check out the [Github issue](https://github.com/dagster-io/dagster/issues/7683#issuecomment-1175593637)!

# 0.15.4

- Reverted sensor threadpool changes from 0.15.3 to address daemon stability issues.

# 0.15.3

### New

- When loading an upstream asset or op output as an input, you can now set custom loading behavior using the input_manager_key argument to AssetIn and In
- The list of objects returned by a repository can now contain nested lists.
- Added a data retention instance setting in dagster.yaml that enables the automatic removal of sensor/schedule ticks after a certain number of days.
- Added a sensor daemon setting in dagster.yaml that enables sensor evaluations to happen in a thread pool to increase throughput.
- `materialize_to_memory` and materialize now both have the partition_key argument.
- `Output` and `DynamicOutput` objects now work with deep equality checks:

```python
Output(value=5, name="foo") == Output(value=5, name="foo") # evaluates to True
```

- RunRequests can now be returned from run status sensors
- Added `resource_defs` argument to `AssetsDefinition.from_graph`. Allows for specifying resources required by constituent ops directly on the asset.
- When adding a tag to the Run search filter in Dagit by clicking the hover menu on the tag, the tag will now be appended to the filter instead of replacing the entire filter state.

### Bugfixes

- [dagster-dbt] An exception is now emitted if you attempt to invoke the library without having dbt-core installed. dbt-core is now also added as a dependency to the library.
- Asset group names can now contain reserved python keywords
- Fixed a run config parsing bug that was introduced in `0.15.1` that caused Dagit to interpret datetime strings as datetime objects and octal strings as integers.
- Runs that have failed to start are now represented in the Instance Timeline view on Dagit.
- Fixed an issue where the partition status was missing for partitioned jobs that had no runs.
- Fixed a bug where op/resource invocation would error when resources were required, no context was used in the body of the function, and no context was provided when invoking.
- [dagster-databricks] Fixed an issue where an exception related to the deprecated prior_attempts_count field when using the databricks_pyspark_step_launcher.
- [dagster-databricks] Polling information logged from the databricks_pyspark_step_launcher is now emitted at the DEBUG level instead of INFO.
- In the yaml editor in Dagit, the typeahead feature now correctly shows suggestions for nullable schema types.
- When editing asset configuration in Dagit, the “Scaffold config” button in the Dagit launchpad sometimes showed the scaffold dialog beneath the launchpad. This has been fixed.
- A recent change added execution timezones to some human-readable cron strings on schedules in Dagit. This was added incorrectly in some cases, and has now been fixed.
- In the Dagit launchpad, a config state containing only empty newlines could lead to an error that could break the editor. This has been fixed.
- Fixed issue that could cause partitioned graph-backed assets to attempt to load upstream inputs from the incorrect path when using the fs_io_manager (or other similar io managers).
- [dagster-dbt] Fixed issue where errors generated from issuing dbt cli commands would only show json-formatted output, rather than a parsed, human-readable output.
- [dagster-dbt] By default, dagster will invoke the dbt cli with a --log-format json flag. In some cases, this may cause dbt to report incorrect or misleading error messages. As a workaround, it is now possible to disable this behavior by setting the json_log_format configuration option on the dbt_cli_resource to False.
- materialize_to_memory erroneously allowed non-in-memory io managers to be used. Now, providing io managers to materialize_to_memory will result in an error, and mem_io_manager will be provided to all io manager keys.

# 0.15.2

### Bugfixes

- Fixed an issue where asset dependency resolution would break when two assets in the same group had the same name

# 0.15.1

### New

- When Dagster loads an event from the event log of a type that it doesn’t recognize (for example, because it was created by a newer version of Dagster) it will now return a placeholder event rather than raising an exception.
- AssetsDefinition.from_graph() now accepts a group_name parameter. All assets created by from_graph are assigned to this group.
- You can define an asset from an op via a new utility method `AssetsDefinition.from_op`. Dagster will infer asset inputs and outputs from the ins/outs defined on the `@op` in the same way as `@graphs`.
- A default executor definition can be defined on a repository using the `default_executor_def` argument. The default executor definition will be used for all op/asset jobs that don’t explicitly define their own executor.
- `JobDefinition.run_request_for_partition` now accepts a `tags` argument (Thanks @jburnich!)
- In Dagit, the graph canvas now has a dotted background to help it stand out from the reset of the UI.
- `@multi_asset` now accepts a resource_defs argument. The provided resources can be either used on the context, or satisfy the io manager requirements of the outs on the asset.
- In Dagit, show execution timezone on cron strings, and use 12-hour or 24-hour time format depending on the user’s locale.
- In Dagit, when viewing a run and selecting a specific step in the Gantt chart, the compute log selection state will now update to that step as well.
- `define_asset_job` and `to_job` now can now accept a `partitions_def` argument and a `config` argument at the same time, as long as the value for the `config` argument is a hardcoded config dictionary (not a `PartitionedConfig` or `ConfigMapping`)

### Bugfixes

- Fixed an issue where entering a string in the launchpad that is valid YAML but invalid JSON would render incorrectly in Dagit.
- Fixed an issue where steps using the `k8s_job_executor` and `docker_executor` would sometimes return the same event lines twice in the command-line output for the step.
- Fixed type annotations on the `@op` decorator (Thanks Milos Tomic!)
- Fixed an issue where job backfills were not displayed correctly on the Partition view in Dagit.
- `UnresolvedAssetJobDefinition` now supports the `run_request_for_partition` method.
- Fixed an issue in Dagit where the Instance Overview page would briefly flash a loading state while loading fresh data.

### Breaking Changes

- Runs that were executed in newer versions of Dagster may produce errors when their event logs are loaded in older versions of Dagit, due to new event types that were recently added. Going forward, Dagit has been made more resilient to handling new events.

### Deprecations

- Updated deprecation warnings to clarify that the deprecated metadata APIs will be removed in 0.16.0, not 0.15.0.

### Experimental

- If two assets are in the same group and the upstream asset has a multi-segment asset key, the downstream asset doesn’t need to specify the full asset key when declaring its dependency on the upstream asset - just the last segment.

### Documentation

- Added dedicated sections for op, graph, and job Concept docs in the sidenav
- Moved graph documentation from the jobs docs into its [own page](https://docs.dagster.io/concepts/ops-jobs-graphs/graphs)
- Added documentation for assigning [asset groups](https://docs.dagster.io/concepts/assets/software-defined-assets#grouping-assets) and viewing them in Dagit
- Added apidoc for `AssetOut` and `AssetIn`
- Fixed a typo on the Run Configuration concept page (Thanks Wenshuai Hou!)
- Updated screenshots in the software-defined assets tutorial to match the new Dagit UI
- Fixed a typo in the **Defining an asset** section of the software-defined assets tutorial (Thanks Daniel Kim!)

# 0.15.0 "Cool for the Summer"

## Major Changes

- Software-defined assets are now marked fully stable and are ready for prime time - we recommend using them whenever your goal using Dagster is to build and maintain data assets.
- You can now organize software defined assets into groups by providing a group_name on your asset definition. These assets will be grouped together in Dagit.
- Software-defined assets now accept configuration, similar to ops. E.g.

  ```
  from dagster import asset

  @asset(config_schema={"iterations": int})
  def my_asset(context):
      for i in range(context.op_config["iterations"]):
          ...
  ```

- Asset definitions can now be created from graphs via `AssetsDefinition.from_graph`:

  ```
  @graph(out={"asset_one": GraphOut(), "asset_two": GraphOut()})
  def my_graph(input_asset):
      ...

  graph_asset = AssetsDefinition.from_graph(my_graph)
  ```

- `execute_in_process` and `GraphDefinition.to_job` now both accept an `input_values` argument, so you can pass arbitrary Python objects to the root inputs of your graphs and jobs.
- Ops that return Outputs and DynamicOutputs now work well with Python type annotations. You no longer need to sacrifice static type checking just because you want to include metadata on an output. E.g.

  ```
  from dagster import Output, op

  @op
  def my_op() -> Output[int]:
      return Output(5, metadata={"a": "b"})
  ```

- You can now automatically re-execute runs from failure. This is analogous to op-level retries, except at the job level.
- You can now supply arbitrary structured metadata on jobs, which will be displayed in Dagit.
- The partitions and backfills pages in Dagit have been redesigned to be faster and show the status of all partitions, instead of just the last 30 or so.
- The left navigation pane in Dagit is now grouped by repository, which makes it easier to work with when you have large numbers of jobs, especially when jobs in different repositories have the same name.
- The Asset Details page for a software-defined asset now includes a Lineage tab, which makes it easy to see all the assets that are upstream or downstream of an asset.

## Breaking Changes and Deprecations

### Software-defined assets

This release marks the official transition of software-defined assets from experimental to stable. We made some final changes to incorporate feedback and make the APIs as consistent as possible:

- Support for adding tags to asset materializations, which was previously marked as experimental, has been removed.
- Some of the properties of the previously-experimental AssetsDefinition class have been renamed. group_names is now group_names_by_key, asset_keys_by_input_name is now keys_by_input_name, and asset_keys_by_output_name is now keys_by_output_name, asset_key is now key, and asset_keys is now keys.
- Removes previously experimental IO manager `fs_asset_io_manager` in favor of merging its functionality with `fs_io_manager`. `fs_io_manager` is now the default IO manager for asset jobs, and will store asset outputs in a directory named with the asset key. Similarly, removed `adls2_pickle_asset_io_manager`, `gcs_pickle_asset_io_manager` , and `s3_pickle_asset_io_manager`. Instead, `adls2_pickle_io_manager`, `gcs_pickle_io_manager`, and `s3_pickle_io_manager` now support software-defined assets.
- _(deprecation)_ The namespace argument on the `@asset` decorator and AssetIn has been deprecated. Users should use key_prefix instead.
- _(deprecation)_ AssetGroup has been deprecated. Users should instead place assets directly on repositories, optionally attaching resources using with_resources. Asset jobs should be defined using `define_asset_job` (replacing `AssetGroup.build_job`), and arbitrary sets of assets can be materialized using the standalone function materialize (replacing `AssetGroup.materialize`).
- _(deprecation)_ The `outs` property of the previously-experimental `@multi_asset` decorator now prefers a dictionary whose values are `AssetOut` objects instead of a dictionary whose values are `Out` objects. The latter still works, but is deprecated.
- The previously-experimental property on `OpExecutionContext` called `output_asset_partition_key` is now deprecated in favor of `asset_partition_key_for_output`

### Event records

- The `get_event_records` method on DagsterInstance now requires a non-None argument `event_records_filter`. Passing a `None` value for the `event_records_filter` argument will now raise an exception where previously it generated a deprecation warning.
- Removed methods `events_for_asset_key` and `get_asset_events`, which have been deprecated since 0.12.0.

### Extension libraries

- [dagster-dbt] (breaks previously-experimental API) When using the load_assets_from_dbt_project or load_assets_from_dbt_manifest , the AssetKeys generated for dbt sources are now the union of the source name and the table name, and the AssetKeys generated for models are now the union of the configured schema name for a given model (if any), and the model name. To revert to the old behavior: `dbt_assets = load_assets_from_dbt_project(..., node_info_to_asset_key=lambda node_info: AssetKey(node_info["name"])`.
- [dagster-k8s] In the Dagster Helm chart, user code deployment configuration (like secrets, configmaps, or volumes) is now automatically included in any runs launched from that code. Previously, this behavior was opt-in. In most cases, this will not be a breaking change, but in less common cases where a user code deployment was running in a different kubernetes namespace or using a different service account, this could result in missing secrets or configmaps in a launched run that previously worked. You can return to the previous behavior where config on the user code deployment was not applied to any runs by setting the includeConfigInLaunchedRuns.enabled field to false for the user code deployment. See the [Kubernetes Deployment docs](https://docs.dagster.io/deployment/guides/kubernetes/deploying-with-helm#configure-your-user-deployment) for more details.
- [dagster-snowflake] dagster-snowflake has dropped support for python 3.6. The library it is currently built on, snowflake-connector-python, dropped 3.6 support in their recent 2.7.5 release.

### Other

- The `prior_attempts_count` parameter is now removed from step-launching APIs. This parameter was not being used, as the information it held was stored elsewhere in all cases. It can safely be removed from invocations without changing behavior.
- The `FileCache` class has been removed.
- Previously, when schedules/sensors targeted jobs with the same name as other jobs in the repo, the jobs on the sensor/schedule would silently overwrite the other jobs. Now, this will cause an error.

## New since 0.14.20

- A new `define_asset_job` function allows you to define a selection of assets that should be executed together. The selection can be a simple string, or an AssetSelection object. This selection will be resolved into a set of assets once placed on the repository.

  ```
  from dagster import repository, define_asset_job, AssetSelection

  string_selection_job = define_asset_job(
      name="foo_job", selection="*foo"
  )
  object_selection_job = define_asset_job(
      name="bar_job", selection=AssetSelection.groups("some_group")
  )

  @repository
  def my_repo():
      return [
          *my_list_of_assets,
          string_selection_job,
          object_selection_job,
      ]
  ```

- [dagster-dbt] Assets loaded with `load_assets_from_dbt_project` and `load_assets_from_dbt_manifest` will now be sorted into groups based on the subdirectory of the project that each model resides in.
- `@asset` and `@multi_asset` are no longer considered experimental.
- Adds new utility methods `load_assets_from_modules`, `assets_from_current_module`, `assets_from_package_module`, and `assets_from_package_name` to fetch and return a list of assets from within the specified python modules.
- Resources and io managers can now be provided directly on assets and source assets.

  ```
  from dagster import asset, SourceAsset, resource, io_manager

  @resource
  def foo_resource():
      pass

  @asset(resource_defs={"foo": foo_resource})
  def the_resource(context):
      foo = context.resources.foo

  @io_manager
  def the_manager():
      ...

  @asset(io_manager_def=the_manager)
  def the_asset():
      ...
  ```

  Note that assets provided to a job must not have conflicting resource for the same key. For a given job, all resource definitions must match by reference equality for a given key.

- A `materialize_to_memory` method which will load the materializations of a provided list of assets into memory:

  ```
  from dagster import asset, materialize_to_memory

  @asset
  def the_asset():
      return 5

  result = materialize_to_memory([the_asset])
  output = result.output_for_node("the_asset")
  ```

- A `with_resources` method, which allows resources to be added to multiple assets / source assets at once:

  ```
  from dagster import asset, with_resources, resource

  @asset(required_resource_keys={"foo"})
  def requires_foo(context):
      ...

  @asset(required_resource_keys={"foo"})
  def also_requires_foo(context):
      ...

  @resource
  def foo_resource():
      ...

  requires_foo, also_requires_foo = with_resources(
      [requires_foo, also_requires_foo],
      {"foo": foo_resource},
  )
  ```

- You can now include asset definitions directly on repositories. A `default_executor_def` property has been added to the repository, which will be used on any materializations of assets provided directly to the repository.

  ```
  from dagster import asset, repository, multiprocess_executor

  @asset
  def my_asset():
    ...

  @repository(default_executor_def=multiprocess_executor)
  def repo():
      return [my_asset]
  ```

- The `run_storage`, `event_log_storage`, and `schedule_storage` configuration sections of the `dagster.yaml` can now be replaced by a unified `storage` configuration section. This should avoid duplicate configuration blocks with your `dagster.yaml`. For example, instead of:

  ```
  # dagster.yaml
  run_storage:
  module: dagster_postgres.run_storage
  class: PostgresRunStorage
  config:
      postgres_url: { PG_DB_CONN_STRING }
  event_log_storage:
  module: dagster_postgres.event_log
  class: PostgresEventLogStorage
  config:
      postgres_url: { PG_DB_CONN_STRING }
  schedule_storage:
  module: dagster_postgres.schedule_storage
  class: PostgresScheduleStorage
  config:
      postgres_url: { PG_DB_CONN_STRING }
  ```

  You can now write:

  ```
  storage:
    postgres:
      postgres_url: { PG_DB_CONN_STRING }
  ```

- All assets where a `group_name` is not provided are now part of a group called `default`.
- The group_name parameter value for `@asset` is now restricted to only allow letters, numbers and underscore.
- You can now [set policies to automatically retry Job runs](https://docs.dagster.io/master/deployment/run-retries). This is analogous to op-level retries, except at the job level. By default the retries pick up from failure, meaning only failed ops and their dependents are executed.
- [dagit] The new repository-grouped left navigation is fully launched, and is no longer behind a feature flag.
- [dagit] The left navigation can now be collapsed even when the viewport window is wide. Previously, the navigation was collapsible only for small viewports, but kept in a fixed, visible state for wide viewports. This visible/collapsed state for wide viewports is now tracked in localStorage, so your preference will persist across sessions.
- [dagit] Queued runs can now be terminated from the Run page.
- [dagit] The log filter on a Run page now shows counts for each filter type, and the filters have higher contrast and a switch to indicate when they are on or off.
- [dagit] The partitions and backfill pages have been redesigned to focus on easily viewing the last run state by partition. These redesigned pages were previously gated behind a feature flag — they are now loaded by default.
- [dagster-k8s] Overriding labels in the K8sRunLauncher will now apply to both the Kubernetes job and the Kubernetes pod created for each run, instead of just the Kubernetes pod.

### Bugfixes

- [dagster-dbt] In some cases, if Dagster attempted to rematerialize a dbt asset, but dbt failed to start execution, asset materialization events would still be emitted. This has been fixed.
- [dagit] On the Instance Overview page, the popover showing details of overlapping batches of runs is now scrollable.
- [dagit] When viewing Instance Overview, reloading a repository via controls in the left navigation could lead to an error that would crash the page due to a bug in client-side cache state. This has been fixed.
- [dagit] When scrolling through a list of runs, scrolling would sometimes get stuck on certain tags, specifically those with content overflowing the width of the tag. This has been fixed.
- [dagit] While viewing a job page, the left navigation item corresponding to that job will be highlighted, and the navigation pane will scroll to bring it into view.
- [dagit] Fixed a bug where the “Scaffold config” button was always enabled.

### Community Contributions

- You can now provide dagster-mlflow configuration parameters as environment variables, thanks @chasleslr!

### Documentation

- Added a guide that helps users who are familiar with ops and graphs understand how and when to use software-defined assets.
- Updated and reorganized docs to document software-defined assets changes since 0.14.0.
- The Deploying in Docker example now includes an example of using the `docker_executor` to run each step of a job in a different Docker container.
- Descriptions for the top-level fields of Dagit GraphQL queries, mutations, and subscriptions have been added.

# 0.14.20

### New

- [dagster-aws] Added an `env_vars` field to the EcsRunLauncher that allows you to configure environment variables in the ECS task for launched runs.
- [dagster-k8s] The `env_vars` field on `K8sRunLauncher` and `k8s_job_executor` can now except input of the form ENV_VAR_NAME=ENV_VAR_VALUE, and will set the value of ENV_VAR_NAME to ENV_VAR_VALUE. Previously, it only accepted input of the form ENV_VAR_NAME, and the environment variable had to be available in the pod launching the job.
- [dagster-k8s] setting ‘includeConfigInLaunchedRuns’ on a user code deployment will now also include any image pull secrets from the user code deployment in the pod for the launched runs.

### Bugfixes

- A recent change had made it so that, when `IOManager.load_input` was called to load an asset that was not being materialized as part of the run, the provided context would not include the metadata for that asset. `context.upstream_output.metadata` now correctly returns the metadata on the upstream asset.
- Fixed an issue where using generic type aliases introduced in Python 3.9 (like `list[str]`) as the type of an input would raise an exception.
- [dagster-k8s] Fixed an issue where upgrading the Helm chart version without upgrading your user code deployment version would result in an “Received unexpected config entry "scheme" at path root:postgres_db" error.

# 0.14.19

### New

- Metadata can now be added to jobs (via the `metadata` parameter) and viewed in dagit. You can use it to track code owners, link to docs, or add other useful information.
- In the Dagit launchpad, the panel below the config editor now shows more detailed information about the state of the config, including error state and whether the config requires further scaffolding or the removal of extra config.
- FileCache is now marked for deprecation in 0.15.0.
- In Dagit, the asset catalog now shows the last materialization for each asset and links to the latest run.
- Assets can now have a `config_schema`. If you attempt to materialize an asset with a config schema in Dagit, you'll be able to enter the required config via a modal.

### Bugfixes

- [helm] Fixed an issue where string floats and integers were not properly templated as image tags.
- [dagster-k8s] Fixed an issue when using the `k8s_job_executor` where ops with long names sometimes failed to create a pod due to a validation error with the label names automatically generated by Dagster.
- [dagster-aws] Fixed an issue where ECS tasks with large container contexts would sometimes fail to launch because their request to the ECS RunTask API was too large.

### Breaking Changes

- `fs_asset_io_manager` has been removed in favor of merging its functionality with `fs_io_manager`. `fs_io_manager` is now the default IO manager for asset jobs, and will store asset outputs in a directory named with the asset key.

### Community Contributions

- Fixed a bug that broke the `k8s_job_executor`’s `max_conccurent` configuration. Thanks @fahadkh!
- Fixed a bug that caused the `fs_io_manager` to incorrectly handle assets associated with upstream assets. Thanks @aroig!

### Documentation

- [helm] Add documentation for code server image pull secrets in the main chart.
- The Dagster README has been revamped with documentation and community links.

# 0.14.17

### New

- Added a pin to `protobuf` version 3 due to a backwards incompatible change in the `probobuf` version 4 release.
- [helm] The name of the Dagit deployment can now be overridden in the Dagster Helm chart.
- [dagit] The left navigation now shows jobs as expandable lists grouped by repository. You can opt out of this change using the feature flag in User Settings.
- [dagit] In the left navigation, when a job has more than one schedule or sensor, clicking the schedule/sensor icon will now display a dialog containing the full list of schedules and sensors for that job.
- [dagit] Assets on the runs page are now shown in more scenarios.
- [dagster-dbt] dbt assets now support subsetting! In dagit, you can launch off a dbt command which will only refresh the selected models, and when you’re building jobs using `AssetGroup.build_job()`, you can define selections which select subsets of the loaded dbt project.
- [dagster-dbt] [experimental] The `load_assets_from_dbt_manifest` function now supports an experimental `select` parameter. This allows you to use dbt selection syntax to select from an existing manifest.json file, rather than having Dagster re-compile the project on demand.
- For software-defined assets, `OpExecutionContext` now exposes an `asset_key_for_output` method, which returns the asset key that one of the op’s outputs corresponds too.
- The Backfills tab in Dagit loads much faster when there have been backfills that produced large numbers of runs.
- Added the ability to run the Dagster Daemon as a Python module, by running `python -m dagster.daemon`.
- The `non_argument_deps` parameter for the `asset` and `multi_asset` decorators can now be a set of strings in addition to a set of `AssetKey`.

### Bugfixes

- [dagit] In cases where Dagit is unable to make successful WebSocket connections, run logs could become stuck in a loading state. Dagit will now time out on the WebSocket connection attempt after a brief period of time. This allows run logs to fall back to http requests and move past the loading state.
- In version 0.14.16, launching an asset materialization run with source assets would error with an `InvalidSubsetError`. This is now fixed.
- Empty strings are no longer allowed as `AssetKey`s.
- Fixed an issue where schedules built from partitioned job config always ran at midnight, ignoring any hour or minute offset that was specified on the config.
- Fixed an issue where if the scheduler was interrupted and resumed in the middle of running a schedule tick that produced multiple RunRequests, it would show the same run ID multiple times on the list of runs for the schedule tick.
- Fixed an issue where Dagit would raise a GraphQL error when a non-dictionary YAML string was entered into the Launchpad.
- Fixed an issue where Dagster gRPC servers would sometimes raise an exception when loading repositories with many partition sets.
- Fixed an issue where the `snowflake_io_manager` would sometimes raise an error with `pandas` 1.4 or later installed.
- Fixed an issue where re-executing an entire set of dynamic steps together with their upstream step resulted in `DagsterExecutionStepNotFoundError`. This is now fixed.
- [dagit] Added loading indicator for job-scoped partition backfills.
- Fixed an issue that made it impossible to have graph-backed assets with upstream SourceAssets.

### Community Contributions

- `AssetIn` can now accept a string that will be coerced to an `AssetKey`. Thanks [@aroig](https://github.com/aroig)!
- Runtime type checks improved for some asset-related functions. Thanks [@aroig](https://github.com/aroig)!
- Docs grammar fixes. Thanks [@dwinston](https://github.com/dwinston)!
- Dataproc ops for `dagster-gcp` now have user-configurable timeout length. Thanks [@3cham](https://github.com/3cham)!

# 0.14.16

### New

- `AssetsDefinition.from_graph` now accepts a `partitions_def` argument.
- `@asset`-decorated functions can now accept variable keyword arguments.
- Jobs executed in ECS tasks now report the health status of the ECS task
- The CLI command `dagster instance info` now prints the current schema migration state for the configured instance storage.
- [dagster-dbt] You can now configure a `docs_url` on the `dbt_cli_resource`. If this value is set, AssetMaterializations associated with each dbt model will contain a link to the dbt docs for that model.
- [dagster-dbt] You can now configure a `dbt_cloud_host` on the `dbt_cloud_resource`, in the case that your dbt cloud instance is under a custom domain.

### Bugfixes

- Fixed a bug where `InputContext.upstream_output` was missing the `asset_key` when it referred to an asset outside the run.
- When specifying a `selection` parameter in `AssetGroup.build_job()`, the generated job would include an incorrect set of assets in certain situations. This has been fixed.
- Previously, a set of database operational exceptions were masked with a `DagsterInstanceSchemaOutdated` exception if the instance storage was not up to date with the latest schema. We no longer wrap these exceptions, allowing the underlying exceptions to bubble up.
- [dagster-airbyte] Fixed issue where successfully completed Airbyte syncs would send a cancellation request on completion. While this did not impact the sync itself, if alerts were set up on that connection, they would get triggered regardless of if the sync was successful or not.
- [dagster-azure] Fixed an issue where the Azure Data Lake Storage `adls2_pickle_io_manager` would sometimes fail to recursively delete a folder when cleaning up an output.
- Previously, if two different jobs with the same name were provided to the same repo, and one was targeted by a sensor/schedule, the job provided by the sensor/schedule would silently overwrite the other job instead of failing. In this release, a warning is fired when this case is hit, which will turn into an error in 0.15.0.
- Dagit will now display workspace errors after reloading all repositories.

### Breaking Changes

- Calls to `instance.get_event_records` without an event type filter is now deprecated and will generate a warning. These calls will raise an exception starting in `0.15.0`.

### Community Contributions

- `@multi_asset` now supports partitioning. Thanks @aroig!
- Orphaned process detection now works correctly across a broader set of platforms. Thanks @aroig!
- [K8s] Added a new `max_concurrent` field to the `k8s_job_executor` that limits the number of concurrent Ops that will execute per run. Since this executor launches a Kubernetes Job per Op, this also limits the number of concurrent Kuberenetes Jobs. Note that this limit is per run, not global. Thanks @kervel!
- [Helm] Added a new `externalConfigmap` field as an alternative to `dagit.workspace.servers` when running the user deployments chart in a separate release. This allows the workspace to be managed outside of the main Helm chart. Thanks @peay!
- Removed the pin on `markupsafe<=2.0.1`. Thanks @[bollwyvl](https://github.com/dagster-io/dagster/commits?author=bollwyvl)!

# 0.14.15

### New

- Sensors / schedules can now return a list of `RunRequest` objects instead of yielding them.
- Repositories can now contain asset definitions and source assets for the same asset key.
- `OpExecutionContext` (provided as the `context` argument to Ops) now has fields for, `run`, `job_def`, `job_name`, `op_def`, and `op_config`. These replace `pipeline_run`, `pipeline_def`, etc. (though they are still available).
- When a job is partitioned using an hourly, daily, weekly, or monthly partitions definition, `OpExecutionContext` now offers a `partition_time_window` attribute, which returns a tuple of datetime objects that mark the bounds of the partition’s time window.
- `AssetsDefinition.from_graph` now accepts a `partitions_def` argument.
- [dagster-k8s] Removed an unnecessary `dagster-test-connection` pod from the Dagster Helm chart.
- [dagster-k8s] The `k8s_job_executor` now polls the event log on a ~1 second interval (previously 0.1). Performance testing showed that this reduced DB load while not significantly impacting run time.
- [dagit] Removed package pins for `Jinja2` and `nbconvert`.
- [dagit] When viewing a list of Runs, tags with information about schedules, sensors, and backfills are now more visually prominent and are sorted to the front of the list.
- [dagit] The log view on Run pages now includes a button to clear the filter input.
- [dagit] When viewing a list of Runs, you can now hover over a tag to see a menu with an option to copy the tag, and in filtered Run views, an option to add the tag to the filter.
- [dagit] Configuration editors throughout Dagit now display clear indentation guides, and our previous whitespace indicators have been removed.
- [dagit] The Dagit Content-Security-Policy has been moved from a `<meta>` tag to a response header, and several more security and privacy related headers have been added as well.
- [dagit] Assets with multi-component key paths are always shown as `foo/bar` in dagit, rather than appearing as `foo > bar` in some contexts.
- [dagit] The Asset graph now includes a “Reload definitions” button which reloads your repositories.
- [dagit] On all DAGs, you can hold shift on the keyboard to switch from mouse wheel / touch pad zooming to panning. This makes it much easier to scroll horizontally at high speed without click-drag-click-drag-click-drag.
- [dagit] a `--log-level` flag is now available in the dagit cli for controlling the uvicorn log level.
- [dagster-dbt] The `load_assets_from_dbt_project()` and `load_assets_from_dbt_manifest()` utilities now have a `use_build_command` parameter. If this flag is set, when materializing your dbt assets, Dagster will use the `dbt build` command instead of `dbt run`. Any tests run during this process will be represented with AssetObservation events attached to the relevant assets. For more information on `dbt build`, see the [dbt docs](https://docs.getdbt.com/reference/commands/build).
- [dagster-dbt] If a dbt project successfully runs some models and then fails, AssetMaterializations will now be generated for the successful models.
- [dagster-snowflake] The new Snowflake IO manager, which you can create using `build_snowflake_io_manager` offers a way to store assets and op outputs in Snowflake. The `PandasSnowflakeTypeHandler` stores Pandas `DataFrame`s in Snowflake.
- [helm] `dagit.logLevel` has been added to values.yaml to access the newly added dagit --log-level cli option.

### Bugfixes

- Fixed incorrect text in the error message that’s triggered when building a job and an asset can’t be found that corresponds to one of the asset dependencies.
- An error is no longer raised when an op/job/graph/other definition has an empty docstring.
- Fixed a bug where pipelines could not be executed if `toposort<=1.6` was installed.
- [dagit] Fixed an issue in global search where rendering and navigation broke when results included objects of different types but with identical names.
- [dagit] server errors regarding websocket send after close no longer occur.
- [dagit] Fixed an issue where software-defined assets could be rendered improperly when the dagster and dagit versions were out of sync.

### Community Contributions

- [dagster-aws] `PickledObjectS3IOManager` now uses `list_objects` to check the access permission. Thanks @trevenrawr!

### Breaking Changes

- [dagster-dbt] The asset definitions produced by the experimental `load_assets_from_dbt_project` and `load_assets_from_dbt_manifest` functions now include the schemas of the dbt models in their asset keys. To revert to the old behavior: `dbt_assets = load_assets_from_dbt_project(..., node_info_to_asset_key=lambda node_info: AssetKey(node_info["name"])`.

### Experimental

- The `TableSchema` API is no longer experimental.

### Documentation

- Docs site now has a new design!
- Concepts pages now have links to code snippets in our examples that use those concepts.

# 0.14.14

### New

- When viewing a config schema in the Dagit launchpad, default values are now shown. Hover over an underlined key in the schema view to see the default value for that key.
- dagster, dagit, and all extension libraries (dagster-\*) now contain py.typed files. This exposes them as typed libraries to static type checking tools like mypy. If your project is using mypy or another type checker, this may surface new type errors. For mypy, to restore the previous state and treat dagster or an extension library as untyped (i.e. ignore Dagster’s type annotations), add the following to your configuration file:

```
[mypy-dagster]  (or e.g. mypy-dagster-dbt)
follow_imports = "skip"
```

- Op retries now surface the underlying exception in Dagit.
- Made some internal changes to how we store schema migrations across our different storage implementations.
- `build_output_context` now accepts an `asset_key` argument.
- They key argument to the SourceAsset constructor now accepts values that are strings or sequences of strings and coerces them to AssetKeys.
- You can now use the + operator to add two AssetGroups together, which forms an AssetGroup that contains a union of the assets in the operands.
- `AssetGroup.from_package_module`, `from_modules`, `from_package_name`, and `from_current_module` now accept an `extra_source_assets` argument that includes a set of source assets into the group in addition to the source assets scraped from modules.
- AssetsDefinition and AssetGroup now both expose a `to_source_assets` method that return SourceAsset versions of their assets, which can be used as source assets for downstream AssetGroups.
- Repositories can now include multiple AssetGroups.
- The new prefixed method on AssetGroup returns a new AssetGroup where a given prefix is prepended to the asset key of every asset in the group.
- Dagster now has a BoolMetadataValue representing boolean-type metadata. Specifying True or False values in metadata will automatically be casted to the boolean type.
- Tags on schedules can now be expressed as nested JSON dictionaries, instead of requiring that all tag values are strings.
- If an exception is raised during an op, Dagster will now always run the failure hooks for that op. Before, certain system exceptions would prevent failure hooks from being run.
- `mapping_key` can now be provided as an argument to `build_op_context`/`build_solid_context`. Doing so will allow the use of `OpExecutionContext.get_mapping_key()`.

### Bugfixes

- [dagit] Previously, when viewing a list of an asset’s materializations from a specified date/time, a banner would always indicate that it was a historical view. This banner is no longer shown when viewing the most recent materialization.
- [dagit] Special cron strings like @daily were treated as invalid when converting to human-readable strings. These are now handled correctly.
- The selection argument to `AssetGroup.build_job` now uses `>` instead of `.` for delimiting the components within asset keys, which is consistent with how selection works in Dagit.
- [postgres] passwords and usernames are now correctly url quoted when forming a connection string. Previously spaces were replaced with `+`.
- Fixed an issue where the `celery_docker_executor` would sometimes fail to execute with a JSON deserialization error when using Dagster resources that write to stdout.
- [dagster-k8s] Fixed an issue where the Helm chart failed to work when the user code deployment subchart was used in a different namespace than the main dagster Helm chart, due to missing configmaps.
- [dagster-airbyte] When a Dagster run is terminated while executing an Airbyte sync operation, the corresponding Airbyte sync will also be terminated.
- [dagster-dbt] Log output from dbt cli commands will no longer have distracting color-formatting characters.
- [dagit] Fixed issue where multi_assets would not show correct asset dependency information.
- Fixed an issue with the sensor daemon, where the sensor would sometimes enter a race condition and overwrite the sensor status.

### Community Contributions

- [dagster-graphql] The Python DagsterGraphQLClient now supports terminating in-progress runs using `client.terminate_run(run_id)`. Thanks [@Javier162380](https://github.com/Javier162380)!

### Experimental

- Added an experimental view of the Partitions page / Backfill page, gated behind a feature flag in Dagit.

# 0.14.13

### New

- [dagster-k8s] You can now specify resource requests and limits to the K8sRunLauncher when using the Dagster helm chart, that will apply to all runs. Before, you could only set resource configuration by tagging individual jobs. For example, you can set this config in your `values.yaml` file:

```
runLauncher:
  type: K8sRunLauncher
  config:
    k8sRunLauncher:
      resources:
        limits:
          cpu: 100m
          memory: 128Mi
        requests:
          cpu: 100m
          memory: 128Mi
```

- [dagster-k8s] Specifying `includeConfigInLaunchedRuns: true` in a user code deployment will now launch runs using the same namespace and service account as the user code deployment.
- The `@asset` decorator now accepts an `op_tags` argument, which allows e.g. providing k8s resource requirements on the op that computes the asset.
- Added CLI output to `dagster api grpc-health-check` (previously it just returned via exit codes)
- [dagster-aws] The `emr_pyspark_step_launcher` now supports dynamic orchestration, `RetryPolicy`s defined on ops, and re-execution from failure. For failed steps, the stack trace of the root error will now be available in the event logs, as will logs generated with `context.log.info`.
- Partition sets and can now return a nested dictionary in the `tags_fn_for_partition` function, instead of requiring that the dictionary have string keys and values.
- [dagit] It is now possible to perform bulk re-execution of runs from the Runs page. Failed runs can be re-executed from failure.
- [dagit] Table headers are now sticky on Runs and Assets lists.
- [dagit] Keyboard shortcuts may now be disabled from User Settings. This allows users with certain keyboard layouts (e.g. QWERTZ) to inadvertently avoid triggering unwanted shortcuts.
- [dagit] Dagit no longer continues making some queries in the background, improving performance when many browser tabs are open.
- [dagit] On the asset graph, you can now filter for multi-component asset keys in the search bar and see the “kind” tags displayed on assets with a specified compute_kind.
- [dagit] Repositories are now displayed in a stable order each time you launch Dagster.

### Bugfixes

- [dagster-k8s] Fixed an issue where the Dagster helm chart sometimes failed to parse container images with numeric tags. Thanks [@jrouly](https://github.com/jrouly)!
- [dagster-aws] The `EcsRunLauncher` now registers new task definitions if the task’s execution role or task role changes.
- Dagster now correctly includes `setuptools` as a runtime dependency.
- `In` can now accept `asset_partitions` without crashing.
- [dagit] Fixed a bug in the Launchpad, where default configuration failed to load.
- [dagit] Global search now truncates the displayed list of results, which should improve rendering performance.
- [dagit] When entering an invalid search filter on Runs, the user will now see an appropriate error message instead of a spinner and an alert about a GraphQL error.

### Documentation

- Added documentation for partitioned assets
- [dagster-aws] Fixed example code of a job using `secretsmanager_resource`.

# 0.14.12

### Bugfixes

- Fixed an issue where the Launchpad in Dagit sometimes incorrectly launched in an empty state.

# 0.14.11

### Bugfixes

- Fixed an issue where schedules created from partition sets that launched runs for multiple partitions in a single schedule tick would sometimes time out while generating runs in the scheduler.
- Fixed an issue where nested graphs would sometimes incorrectly determine the set of required resources for a hook.

# 0.14.10

### New

- [dagster-k8s] Added an `includeConfigInLaunchedRuns` flag to the Helm chart that can be used to automatically include configmaps, secrets, and volumes in any runs launched from code in a user code deployment. See https://docs.dagster.io/deployment/guides/kubernetes/deploying-with-helm#configure-your-user-deployment for more information.
- [dagit] Improved display of configuration yaml throughout Dagit, including better syntax highlighting and the addition of line numbers.
- The GraphQL input argument type `BackfillParams` (used for launching backfills), now has an `allPartitions` boolean flag, which can be used instead of specifying all the individual partition names.
- Removed `gevent` and `gevent-websocket` dependencies from `dagster-graphql`
- Memoization is now supported while using step selection
- Cleaned up various warnings across the project
- The default IO Managers now support asset partitions

### Bugfixes

- Fixed `sqlite3.OperationalError` error when viewing schedules/sensors pages in Dagit. This was affecting dagit instances using the default SQLite schedule storage with a SQLite version `< 3.25.0`.

- Fixed an issues where schedules and sensors would sometimes fail to run when the daemon and dagit were running in different Python environments.
- Fixed an exception when the telemetry file is empty
- fixed a bug with `@graph` composition which would cause the wrong input definition to be used for type checks
- [dagit] For users running Dagit with `--path-prefix`, large DAGs failed to render due to a WebWorker error, and the user would see an endless spinner instead. This has been fixed.
- [dagit] Fixed a rendering bug in partition set selector dropdown on Launchpad.
- [dagit] Fixed the ‘View Assets’ link in Job headers
- Fixed an issue where root input managers with resource dependencies would not work with software defined assets

### Community Contributions

- `dagster-census` is a new library that includes a `census_resource` for interacting the Census REST API, `census_trigger_sync_op` for triggering a sync and registering an asset once it has finished, and a `CensusOutput` type. Thanks @dehume!
- Docs fix. Thanks @ascrookes!

# 0.14.9

### New

- Added a parameter in `dagster.yaml` that can be used to increase the time that Dagster waits when spinning up a gRPC server before timing out. For more information, see https://docs.dagster.io/deployment/dagster-instance#code-servers.
- Added a new graphQL field `assetMaterializations` that can be queried off of a `DagsterRun` field. You can use this field to fetch the set of asset materialization events generated in a given run within a GraphQL query.
- Docstrings on functions decorated with the `@resource` decorator will now be used as resource descriptions, if no description is explicitly provided.
- You can now point `dagit -m` or `dagit -f` at a module or file that has asset definitions but no jobs or asset groups, and all the asset definitions will be loaded into Dagit.
- `AssetGroup` now has a `materialize` method which executes an in-process run to materialize all the assets in the group.
- `AssetGroup`s can now contain assets with different `partition_defs`.
- Asset materializations produced by the default asset IO manager, `fs_asset_io_manager`, now include the path of the file where the values were saved.
- You can now disable the `max_concurrent_runs` limit on the `QueuedRunCoordinator` by setting it to `-1`. Use this if you only want to limit runs using `tag_concurrency_limits`.
- [dagit] Asset graphs are now rendered asynchronously, which means that Dagit will no longer freeze when rendering a large asset graph.
- [dagit] When viewing an asset graph, you can now double-click on an asset to zoom in, and you can use arrow keys to navigate between selected assets.
- [dagit] The “show whitespace” setting in the Launchpad is now persistent.
- [dagit] A bulk selection checkbox has been added to the repository filter in navigation or Instance Overview.
- [dagit] A “Copy config” button has been added to the run configuration dialog on Run pages.
- [dagit] An “Open in Launchpad” button has been added to the run details page.
- [dagit] The Run page now surfaces more information about start time and elapsed time in the header.
- [dagster-dbt] The dbt_cloud_resource has a new `get_runs()` function to get a list of runs matching certain paramters from the dbt Cloud API (thanks @[kstennettlull](https://github.com/kstennettlull)!)
- [dagster-snowflake] Added an `authenticator` field to the connection arguments for the `snowflake_resource` (thanks @swotai!).
- [celery-docker] The celery docker executor has a new configuration entry `container_kwargs` that allows you to specify additional arguments to pass to your docker containers when they are run.

### Bugfixes

- Fixed an issue where loading a Dagster repository would fail if it included a function to lazily load a job, instead of a JobDefinition.
- Fixed an issue where trying to stop an unloadable schedule or sensor within Dagit would fail with an error.
- Fixed telemetry contention bug on windows when running the daemon.
- [dagit] Fixed a bug where the Dagit homepage would claim that no jobs or pipelines had been loaded, even though jobs appeared in the sidebar.
- [dagit] When filtering runs by tag, tag values that contained the `:` character would fail to parse correctly, and filtering would therefore fail. This has been fixed.
- [dagster-dbt] When running the “build” command using the dbt_cli_resource, the run_results.json file will no longer be ignored, allowing asset materializations to be produced from the resulting output.
- [dagster-airbyte] Responses from the Airbyte API with a 204 status code (like you would get from /connections/delete) will no longer produce raise an error (thanks @HAMZA310!)
- [dagster-shell] Fixed a bug where shell ops would not inherit environment variables if any environment variables were added for ops (thanks @kbd!)
- [dagster-postgres] usernames are now urlqouted in addition to passwords

### Documentation

- Instructions for Macs with M1 chips added to contributor setup guide.
- Added a short introductory tutorial for software-defined assets: https://docs.dagster.io/guides/dagster/asset-tutorial.
- Fixed a typo in docs for deploying with Helm (Thanks @LeoHuckvale!)

# 0.14.8

### New

- The MySQL storage implementations for Dagster storage is no longer marked as experimental.
- `run_id` can now be provided as an argument to `execute_in_process`.
- The text on `dagit`’s empty state no longer mentions the legacy concept “Pipelines”.
- Now, within the `IOManager.load_input` method, you can add input metadata via `InputContext.add_input_metadata`. These metadata entries will appear on the `LOADED_INPUT` event and if the input is an asset, be attached to an `AssetObservation`. This metadata is viewable in `dagit`.

### Bugfixes

- Fixed a set of bugs where schedules and sensors would get out of sync between `dagit` and `dagster-daemon` processes. This would manifest in schedules / sensors getting marked as “Unloadable” in `dagit`, and ticks not being registered correctly. The fix involves changing how Dagster stores schedule/sensor state and requires a schema change using the CLI command `dagster instance migrate`. Users who are not running into this class of bugs may consider the migration optional.
- `root_input_manager` can now be specified without a context argument.
- Fixed a bug that prevented `root_input_manager` from being used with `VersionStrategy`.
- Fixed a race condition between daemon and `dagit` writing to the same telemetry logs.
- [dagit] In `dagit`, using the “Open in Launchpad” feature for a run could cause server errors if the run configuration yaml was too long. Runs can now be opened from this feature regardless of config length.
- [dagit] On the Instance Overview page in `dagit`, runs in the timeline view sometimes showed incorrect end times, especially batches that included in-progress runs. This has been fixed.
- [dagit] In the `dagit` launchpad, reloading a repository should present the user with an option to refresh config that may have become stale. This feature was broken for jobs without partition sets, and has now been fixed.
- Fixed issue where passing a stdlib `typing` type as `dagster_type` to input and output definition was incorrectly being rejected.
- [dagster-airbyte] Fixed issue where AssetMaterialization events would not be generated for streams that had no updated records for a given sync.
- [dagster-dbt] Fixed issue where including multiple sets of dbt assets in a single repository could cause a conflict with the names of the underlying ops.

# 0.14.7

### New

- [helm] Added configuration to explicitly enable or disable telemetry.
- Added a new IO manager for materializing assets to Azure ADLS. You can specify this IO manager for your AssetGroups by using the following config:

```
`from dagster import AssetGroup
from dagster_azure import adls2_pickle_asset_io_manager, adls2_resource
asset_group = AssetGroup(
    [upstream_asset, downstream_asset],
    resource_defs={"io_manager": adls2_pickle_asset_io_manager, "adls2": adls2_resource}
)`
```

- Added ability to set a custom start time for partitions when using `@hourly_partitioned_config` , `@daily_partitioned_config`, `@weekly_partitioned_config`, and `@monthly_partitioned_config`
- Run configs generated from partitions can be retrieved using the `PartitionedConfig.get_run_config_for_partition_key` function. This will allow the use of the `validate_run_config` function in unit tests.
- [dagit] If a run is re-executed from failure, and the run fails again, the default action will be to re-execute from the point of failure, rather than to re-execute the entire job.
- `PartitionedConfig` now takes an argument `tags_for_partition_fn` which allows for custom run tags for a given partition.

### Bugfixes

- Fixed a bug in the message for reporting Kubernetes run worker failures
- [dagit] Fixed issue where re-executing a run that materialized a single asset could end up re-executing all steps in the job.
- [dagit] Fixed issue where the health of an asset’s partitions would not always be up to date in certain views.
- [dagit] Fixed issue where the “Materialize All” button would be greyed out if a job had SourceAssets defined.

### Documentation

- Updated resource docs to reference “ops” instead of “solids” (thanks @joe-hdai!)
- Fixed formatting issues in the ECS docs

# 0.14.6

### New

- Added IO manager for materializing assets to GCS. You can specify the GCS asset IO manager by using the following config for `resource_defs` in `AssetGroup`:

```
`from dagster import AssetGroup, gcs_pickle_asset_io_manager, gcs_resource
asset_group = AssetGroup(
    [upstream_asset, downstream_asset],
    resource_defs={"io_manager": gcs_pickle_asset_io_manager, "gcs": gcs_resource}
)`
```

- Improved the performance of storage queries run by the sensor daemon to enforce the idempotency of run keys. This should reduce the database CPU when evaluating sensors with a large volume of run requests with run keys that repeat across evaluations.
- [dagit] Added information on sensor ticks to show when a sensor has requested runs that did not result in the creation of a new run due to the enforcement of idempotency using run keys.
- [k8s] Run and step workers are now labeled with the Dagster run id that they are currently handling.
- If a step launched with a StepLauncher encounters an exception, that exception / stack trace will now appear in the event log.

### Bugfixes

- Fixed a race condition where canceled backfills would resume under certain conditions.
- Fixed an issue where exceptions that were raised during sensor and schedule execution didn’t always show a stack trace in Dagit.
- During execution, dependencies will now resolve correctly for certain dynamic graph structures that were previously resolving incorrectly.
- When using the forkserver start_method on the multiprocess executor, preload_modules have been adjusted to prevent libraries that change namedtuple serialization from causing unexpected exceptions.
- Fixed a naming collision between dagster decorators and submodules that sometimes interfered with static type checkers (e.g. pyright).
- [dagit] postgres database connection management has improved when watching actively executing runs
- [dagster-databricks] The databricks_pyspark_step_launcher now supports steps with RetryPolicies defined, as well as `RetryRequested` exceptions.

### Community Contributions

- Docs spelling fixes - thanks @antquinonez!

# 0.14.5

### Bugfixes

- [dagit] Fixed issue where sensors could not be turned on/off in dagit.
- Fixed a bug with direct op invocation when used with `funcsigs.partial` that would cause incorrect `InvalidInvocationErrors` to be thrown.
- Internal code no longer triggers deprecation warnings for all runs.

# 0.14.4

### New

- Dagster now supports non-standard vixie-style cron strings, like `@hourly`, `@daily`, `@weekly`, and `@monthly` in addition to the standard 5-field cron strings (e.g. `* * * * *`).
- `value` is now an alias argument of `entry_data` (deprecated) for the `MetadataEntry` constructor.
- Typed metadata can now be attached to `SourceAssets` and is rendered in `dagit`.
- When a step fails to upload its compute log to Dagster, it will now add an event to the event log with the stack trace of the error instead of only logging the error to the process output.
- [dagit] Made a number of improvements to the Schedule/Sensor pages in Dagit, including showing a paginated table of tick information, showing historical cursor state, and adding the ability to set a cursor from Dagit. Previously, we only showed tick information on the timeline view and cursors could only be set using the `dagster` CLI.
- [dagit] When materializing assets, Dagit presents a link to the run rather than jumping to it, and the status of the materialization (pending, running, failed) is shown on nodes in the asset graph.
- [dagit] Dagit now shows sensor and schedule information at the top of asset pages based on the jobs in which the asset appears.
- [dagit] Dagit now performs "middle truncation" on gantt chart steps and graph nodes, making it much easier to differentiate long assets and ops.
- [dagit] Dagit no longer refreshes data when tabs are in the background, lowering browser CPU usage.
- `dagster-k8s`, `dagster-celery-k8s`, and `dagster-docker` now name step workers `dagster-step-...` rather than `dagster-job-...`.
- [dagit] The launchpad is significantly more responsive when you're working with very large partition sets.
- [dagit] We now show an informative message on the Asset catalog table when there are no matching assets to display. Previously, we would show a blank white space.
- [dagit] Running Dagit without a backfill daemon no longer generates a warning unless queued backfills are present. Similarly, a missing sensor or schedule daemon only yields a warning if sensors or schedules are turned on.
- [dagit] On the instance summary page, hovering over a recent run’s status dot shows a more helpful tooltip.
- [dagster-k8s] Improved performance of the `k8s_job_executor` for runs with many user logs
- [dagster-k8s] When using the `dagster-k8s/config` tag to configure Dagster Kubernetes pods, the tags can now accept any valid Kubernetes config, and can be written in either snake case (`node_selector_terms`) or camel case (`nodeSelectorTerms`). See [the docs](https://docs.dagster.io/deployment/guides/kubernetes/customizing-your-deployment) for more information.
- [dagster-aws] You can now [set secrets on the `EcsRunLauncher` using the same syntax](https://legacy-versioned-docs.dagster.dagster-docs.io/0.14.4/deployment/guides/aws#secrets-management-in-ecs) that you use to set secrets in the ECS API.
- [dagster-aws] The `EcsRunLauncher` now attempts to reuse task definitions instead of registering a new task definition for every run.
- [dagster-aws] The `EcsRunLauncher` now raises the underlying ECS API failure if it cannot successfully start a task.

### Software-Defined Assets

- When loading assets from modules using `AssetGroup.from_package_name` and similar methods, lists of assets at module scope are now loaded.
- Added the static methods `AssetGroup.from_modules` and `AssetGroup.from_current_module`, which automatically load assets at module scope from particular modules.
- Software-defined assets jobs can now load partitioned assets that are defined outside the job.
- `AssetGraph.from_modules` now correctly raises an error if multiple assets with the same key are detected.
- The `InputContext` object provided to `IOManager.load_input` previously did not include resource config. Now it does.
- Previously, if an assets job had a partitioned asset as well as a non-partitioned asset that depended on another non-partitioned asset, it would fail to run. Now it runs without issue.
- [dagit] The asset "View Upstream Graph" links no longer select the current asset, making it easier to click "Materialize All".
- [dagit] The asset page's "partition health bar" highlights missing partitions better in large partition sets.
- [dagit] The asset "Materialize Partitions" modal now presents an error when partition config or tags cannot be generated.
- [dagit] The right sidebar of the global asset graph no longer defaults to 0% wide in fresh / incognito browser windows, which made it difficult to click nodes in the global graph.
- [dagit] In the asset catalog, the search bar now matches substrings so it's easier to find assets with long path prefixes.
- [dagit] Dagit no longer displays duplicate downstream dependencies on the Asset Details page in some scenarios.
- [dagster-fivetran] Assets created using `build_fivetran_assets` will now be properly tagged with a `fivetran` pill in Dagit.

### Bugfixes

- Fixed issue causing step launchers to fail in many scenarios involving re-execution or dynamic execution.
- Previously, incorrect selections (generally, step selections) could be generated for strings of the form `++item`. This has been fixed.
- Fixed an issue where run status sensors sometimes logged the wrong status to the event log if the run moved into a different status while the sensor was running.
- Fixed an issue where daily schedules sometimes produced an incorrect partition name on spring Daylight Savings time boundaries.
- [dagit] Certain workspace or repo-scoped pages relied on versions of the `SQLAlchemy` package to be `1.4` or greater to be installed. We are now using queries supported by `SQLAlchemy>=1.3`. Previously we would raise an error including the message: `'Select' object has no attribute 'filter'`.
- [dagit] Certain workspace or repo-scoped pages relied on versions of `sqlite` to be `3.25.0` or greater to be installed. This has been relaxed to support older versions of sqlite. This was previously marked as fixed in our `0.14.0` notes, but a handful of cases that were still broken have now been fixed. Previously we would raise an error (`sqlite3.OperationalError`).
- [dagit] When changing presets / partitions in the launchpad, Dagit preserves user-entered tags and replaces only the tags inherited from the previous base.
- [dagit] Dagit no longer hangs when rendering the run gantt chart for certain graph structures.
- [dagster-airbyte] Fixed issues that could cause failures when generating asset materializations from an Airbyte API response.
- [dagster-aws] 0.14.3 removed the ability for the `EcsRunLauncher` to use sidecars without you providing your own custom task definition. Now, you can continue to inherit sidecars from the launching task’s task definition by setting `include_sidecars: True` in your run launcher config.

### Breaking Changes

- `dagster-snowflake` has dropped support for python 3.6. The library it is currently built on, `snowflake-connector-python,` dropped 3.6 support in their recent `2.7.5` release.

### Community Contributions

- `MetadataValue.path()` and `PathMetadataValue` now accept [`os.PathLike`](https://docs.python.org/3/library/os.html#os.PathLike) objects in addition to strings. Thanks[@abkfenris](https://github.com/abkfenris)!
- [dagster-k8s] Fixed configuration of `env_vars` on the `k8s_job_executor`. Thanks [@kervel](https://github.com/kervel)!
- Typo fix on the Create a New Project page. Thanks [@frcode](https://github.com/frcode)!

### Documentation

- Concepts sections added for Op Retries and Dynamic Graphs
- The Hacker News Assets demo now uses `AssetGroup` instead of `build_assets_job`, and it can now be run entirely from a local machine with no additional infrastructure (storing data inside DuckDB).
- The Software-Defined Assets guide in the docs now uses `AssetGroup` instead of `build_assets_job`.

# 0.14.3

### New

- When using an executor that runs each op in its own process, exceptions in the Dagster system code that result in the op process failing will now be surfaced in the event log.
- Introduced new SecretsManager resources to the dagster-aws package to enable loading secrets into Jobs more easily. For more information, see[the documentation](https://docs.dagster.io/_apidocs/libraries/dagster-aws#secretsmanager).
- Daemon heartbeats are now processed in a batch request to the database.
- Job definitions now contain a method called `run_request_for_partition`, which returns a `RunRequest` that can be returned in a sensor or schedule evaluation function to launch a run for a particular partition for that job. See [our documentation](https://docs.dagster.io/concepts/partitions-schedules-sensors/partitions#creating-schedules-from-partitioned-jobs) for more information.
- Renamed the filter class from `PipelineRunsFilter` => `RunsFilter`.
- Assets can now be directly invoked for unit testing.
- [dagster-dbt] `load_assets_from_dbt_project` will now attach schema information to the generated assets if it is available in the dbt project (`schema.yml`).
- [examples] Added an [example](https://github.com/dagster-io/dagster/tree/master/examples/modern_data_stack_assets) that demonstrates using Software Defined Assets with Airbyte, dbt, and custom Python.
- The default io manager used in the `AssetGroup` api is now the `fs_asset_io_manager`.
- It's now possible to build a job where partitioned assets depend on partitioned assets that are maintained outside the job, and for those upstream partitions to show up on the context in the op and IOManager load_input function.
- `SourceAsset`s can now be partitioned, by setting the `partitions_def` argument.

### Bugfixes

- Fixed an issue where run status sensors would sometimes fire multiple times for the same run if the sensor function raised an error.
- [ECS] Previously, setting cpu/memory tags on a job would override the ECS task’s cpu/memory, but not individual containers. If you were using a custom task definition that explicitly sets a container’s cpu/memory, the container would not resize even if you resized the task. Now, setting cpu/memory tags on a job overrides both the ECS task’s cpu/memory and the container's cpu/memory.
- [ECS] Previously, if the EcsRunLauncher launched a run from a task with multiple containers - for example if both dagit and daemon were running in the same task - then the run would be launched with too many containers. Now, the EcsRunLauncher only launches tasks with a single container.
- Fixed an issue where the run status of job invoked through `execute_in_process` was not updated properly.
- Fixed some storage queries that were incompatible with versions of `SQLAlchemy<1.4.0`.
- [dagster-dbt] Fixed issue where `load_assets_from_dbt_project` would fail if models were organized into subdirectories.
- [dagster-dbt] Fixed issue where `load_assets_from_dbt_project` would fail if seeds or snapshots were present in the project.

### Community Contributions

- [dagster-fivetran] A new fivetran_resync_op (along with a corresponding resync_and_poll method on the fivetran_resource) allows you to kick off Fivetran resyncs using Dagster (thanks [@dwallace0723](https://github.com/dwallace0723)!)
- [dagster-shell] Fixed an issue where large log output could cause operations to hang (thanks [@kbd](https://github.com/kbd)!)

- [documentation] Fixed export message with dagster home path (thanks [@proteusiq](https://github.com/Proteusiq))!
- [documentation] Remove duplicate entries under integrations (thanks [@kahnwong](https://github.com/kahnwong))!

### UI

- Added a small toggle to the right of each graph on the asset details page, allowing them to be toggled on and off.
- Full asset paths are now displayed on the asset details page.

### Documentation

- Added API doc entries for `validate_run_config`.
- Fixed the example code for the `reexecute_pipeline` API.
- `TableRecord`, `TableSchema` and its constituents are now documented in the API docs.
- Docs now correctly use new metadata names `MetadataEntry` and `MetadataValue` instead of old ones.

# 0.14.2

### New

- Run status sensors can now be invoked in unit tests. Added `build_run_status_sensor_context` to help build context objects for run status sensors

### Bugfixes

- An issue preventing the use of `default_value` on inputs has been resolved. Previously, a defensive error that did not take `default_value` in to account was thrown.
- [dagster-aws] Fixed issue where re-emitting log records from the pyspark_step_launcher would occasionally cause a failure.
- [dagit] The asset catalog now displays entries for materialized assets when only a subset of repositories were selected. Previously, it only showed the software-defined assets unless all repositories were selected in Dagit.

### Community Contributions

- Fixed an invariant check in the databricks step launcher that was causing failures when setting the `local_dagster_job_package_path` config option (Thanks Iswariya Manivannan!)

### Documentation

- Fixed the example code in the `reconstructable` API docs.

# 0.14.1

### New

- [dagit] The sensor tick timeline now shows cursor values in the tick tooltip if they exist.

### Bugfixes

- Pinned dependency on `markupsafe` to function with existing `Jinja2` pin.
- Sensors that have a default status can now be manually started. Previously, this would fail with an invariant exception.

# 0.14.0 “Never Felt Like This Before”

### Major Changes

- Software-defined assets, which offer a declarative approach to data orchestration on top of Dagster’s core job/op/graph APIs, have matured significantly. Improvements include partitioned assets, a revamped asset details page in Dagit, a cross-repository asset graph view in Dagit, Dagster types on assets, structured metadata on assets, and the ability to materialize ad-hoc selections of assets without defining jobs. Users can expect the APIs to only undergo minor changes before being declared fully stable in Dagster’s next major release. For more information, view the software-defined assets concepts page [here](https://docs.dagster.io/concepts/assets/software-defined-assets).
- We’ve made it easier to define a set of [software-defined assets](https://docs.dagster.io/_apidocs/libraries/dagster-dbt#assets) where each Dagster asset maps to a dbt model. All of the dependency information between the dbt models will be reflected in the Dagster asset graph, while still running your dbt project in a single step.
- Dagit has a new homepage, dubbed the “factory floor” view, that provides an overview of recent runs of all the jobs. From it, you can monitor the status of each job’s latest run or quickly re-execute a job. The new timeline view reports the status of all recent runs in a convenient gantt chart.
- You can now write schedules and sensors that default to running as soon as they are loaded in your workspace, without needing to be started manually in Dagit. For example, you can create a sensor like this:

  ```python
  from dagster import sensor, DefaultSensorStatus

  @sensor(job=my_job, default_status=DefaultSensorStatus.RUNNING)
  def my_running_sensor():
      ...
  ```

  or a schedule like this:

  ```python
  from dagster import schedule, DefaultScheduleStatus, ScheduleEvaluationContext

  @schedule(job=my_job, cron_schedule="0 0 * * *", default_status=DefaultScheduleStatus.RUNNING)
  def my_running_schedule(context: ScheduleEvaluationContext):
      ...
  ```

  As soon as schedules or sensors with the default_status field set to `RUNNING` are included in the workspace loaded by your Dagster Daemon, they will begin creating ticks and submitting runs.

- Op selection now supports selecting ops inside subgraphs. For example, to select an op my_op inside a subgraph my_graph, you can now specify the query as `my_graph.my_op`. This is supported in both Dagit and Python APIs.
- Dagster Types can now have attached metadata. This allows TableSchema objects to be attached to Dagster Types via TableSchemaMetadata. A Dagster Type with a TableSchema will have the schema rendered in Dagit.
- A new [Pandera](https://pandera.readthedocs.io/) integration (dagster-pandera) allows you to use Pandera’s dataframe validation library to wrap dataframe schemas in Dagster types. This provides two main benefits: (1) Pandera’s rich schema validation can be used for runtime data validation of Pandas dataframes in Dagster ops/assets; (2) Pandera schema information is displayed in Dagit using a new TableSchema API for representing arbitrary table schemas.
- The new [AssetObservation event](https://docs.dagster.io/_apidocs/solids#event-types) enables recording metadata about an asset without indicating that the asset has been updated.
- `AssetMaterializations`, `ExpectationResults`, and `AssetObservations` can be logged via the context of an op using the [OpExecutionContext.log_event](https://docs.dagster.io/_apidocs/execution#dagster.OpExecutionContext.log_event) method. Output metadata can also be logged using the [OpExecutionContext.add_output_metadata](https://docs.dagster.io/_apidocs/execution#dagster.OpExecutionContext.add_output_metadata) method. Previously, Dagster expected these events to be yielded within the body of an op, which caused lint errors for many users, made it difficult to add mypy types to ops, and also forced usage of the verbose Output API. Here’s an example of the new invocations:

  ```python
  from dagster import op, AssetMaterialization

  @op
  def the_op(context):
      context.log_event(AssetMaterialization(...))
      context.add_output_metadata({"foo": "bar"})
      ...
  ```

- A new Airbyte integration [(dagster-airbyte)](https://docs.dagster.io/_apidocs/libraries/dagster-airbyte#airbyte-dagster-airbyte) allows you to kick off and monitor [Airbyte](https://airbyte.com/) syncs from within Dagster. The original contribution from @airbytehq’s own @marcosmarxm includes a [resource implementation](https://docs.dagster.io/_apidocs/libraries/dagster-airbyte#resources) as well as a [pre-built op](https://docs.dagster.io/_apidocs/libraries/dagster-airbyte#ops) for this purpose, and we’ve extended this library to support [software-defined asset](https://docs.dagster.io/_apidocs/libraries/dagster-airbyte#assets) use cases as well. Regardless of which interface you use, Dagster will automatically capture the Airbyte log output (in the compute logs for the relevant steps) and track the created tables over time (via AssetMaterializations).
- The [ECSRunLauncher](https://docs.dagster.io/deployment/guides/ecs) (introduced in Dagster 0.11.15) is no longer considered experimental. You can bootstrap your own Dagster deployment on ECS using our [docker compose example](https://github.com/dagster-io/dagster/tree/master/examples/deploy_ecs) or you can use it in conjunction with a [managed Dagster Cloud deployment](https://docs.dagster.cloud/agents/ecs/setup). Since its introduction, we’ve added the ability to customize Fargate container memory and CPU, mount secrets from AWS SecretsManager, and run with a variety of AWS networking configurations. Join us in [#dagster-ecs](https://dagster.slack.com/archives/C014UDS8LAV) in Slack!
- [Helm] The default liveness and startup probes for Dagit and user deployments have been replaced with readiness probes. The liveness and startup probe for the Daemon has been removed. We observed and heard from users that under load, Dagit could fail the liveness probe which would result in the pod restarting. With the new readiness probe, the pod will not restart but will stop serving new traffic until it recovers. If you experience issues with any of the probe changes, you can revert to the old behavior by specifying liveness and startup probes in your Helm values (and reach out via an issue or Slack).

### Breaking Changes and Deprecations

- The Dagster Daemon now uses the same workspace.yaml file as Dagit to locate your Dagster code. You should ensure that if you make any changes to your workspace.yaml file, they are included in both Dagit’s copy and the Dagster Daemon’s copy. When you make changes to the workspace.yaml file, you don’t need to restart either Dagit or the Dagster Daemon - in Dagit, you can reload the workspace from the Workspace tab, and the Dagster Daemon will periodically check the workspace.yaml file for changes every 60 seconds. If you are using the Dagster Helm chart, no changes are required to include the workspace in the Dagster Daemon.
- Dagster’s metadata API has undergone a signficant overhaul. Changes include:
  - To reflect the fact that metadata can be specified on definitions in addition to events, the following names are changing. The old names are deprecated, and will function as aliases for the new names until 0.15.0:
    - `EventMetadata` > `MetadataValue`
    - `EventMetadataEntry` > `MetadataEntry`
    - `XMetadataEntryData` > `XMetadataValue` (e.g. `TextMetadataEntryData` > `TextMetadataValue`)
  - The `metadata_entries` keyword argument to events and Dagster types is deprecated. Instead, users should use the metadata keyword argument, which takes a dictionary mapping string labels to `MetadataValue`s.
  - Arbitrary metadata on In/InputDefinition and Out/OutputDefinition is deprecated. In 0.15.0, metadata passed for these classes will need to be resolvable to MetadataValue (i.e. function like metadata everywhere else in Dagster).
  - The description attribute of `EventMetadataEntry` is deprecated.
  - The static API of `EventMetadataEntry` (e.g. `EventMetadataEntry.text`) is deprecated. In 0.15.0, users should avoid constructing `EventMetadataEntry` objects directly, instead utilizing the metadata dictionary keyword argument, which maps string labels to `MetadataValues`.
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

- Dagit
  - Dagit no longer allows non-software-defined asset materializations to be be graphed or grouped by partition. This feature could render in incorrect / incomplete ways because no partition space was defined for the asset.
  - Dagit’s “Jobs” sidebar now collapses by default on Instance, Job, and Asset pages. To show the left sidebar, click the “hamburger” icon in the upper left.
  - “Step Execution Time” is no longer graphed on the asset details page in Dagit, which significantly improves page load time. To view this graph, go to the asset graph for the job, uncheck “View as Asset Graph” and click the step to view its details.
  - The “experimental asset UI” feature flag has been removed from Dagit, this feature is shipped in 0.14.0!
- The Dagster Daemon now requires a workspace.yaml file, much like Dagit.
- Ellipsis (“...”) is now an invalid substring of a partition key. This is because Dagit accepts an ellipsis to specify partition ranges.
- [Helm] The Dagster Helm chart now only supported Kubernetes clusters above version 1.18.

### New since 0.13.19

- Software Defined Assets:

  - In Dagit, the Asset Catalog now offers a third display mode - a global graph of your software-defined assets.
  - The Asset Catalog now allows you to filter by repository to see a subset of your assets, and offers a “View in Asset Graph” button for quickly seeing software-defined assets in context.
  - The Asset page in Dagit has been split into two tabs, “Activity” and “Definition”.
  - Dagit now displays a warning on the Asset page if the most recent run including the asset’s step key failed without yielding a materialization, making it easier to jump to error logs.
  - Dagit now gives you the option to view jobs with software-defined assets as an Asset Graph (default) or as an Op Graph, and displays asset <-> op relationships more prominently when a single op yields multiple assets.
  - You can now include your assets in a repository with the use of an AssetGroup. Each repository can only have one AssetGroup, and it can provide a jumping off point for creating the jobs you plan on using from your assets.

    ```python
    from dagster import AssetGroup, repository, asset

    @asset(required_resource_keys={"foo"})
    def asset1():
        ...

    @asset
    def asset2():
        ...

    @repository
    def the_repo():
        asset_group = AssetGroup(assets=[asset1, asset2], resource_defs={"foo": ...})
        return [asset_group, asset_group.build_job(selection="asset1-")]
    ```

  - `AssetGroup.build_job` supports a [selection syntax](https://docs.dagster.io/concepts/ops-jobs-graphs/job-execution#op-selection-syntax) similar to that found in op selection.

- Asset Observations:
  - You can now yield AssetObservations to log metadata about a particular asset from beyond its materialization site. AssetObservations appear on the asset details page alongside materializations and numerical metadata is graphed. For assets with software-defined partitions, materialized and observed metadata about each partition is rolled up and presented together. For more information, view the [docs page here](https://docs.dagster.io/concepts/assets/asset-observations).
  - Added an `asset_observations_for_node` method to `ExecuteInProcessResult` for fetching the AssetObservations from an in-process execution.
- Dagster Types with an attached TableSchemaMetadataValue now render the schema in Dagit UI.
- [dagster-pandera] New integration library dagster-pandera provides runtime validation from the [Pandera](https://pandera.readthedocs.io/en/latest/dataframe_schemas.html) dataframe validation library and renders table schema information in Dagit.
- `OpExecutionContext.log_event` provides a way to log AssetMaterializations, ExpectationResults, and AssetObservations from the body of an op without having to yield anything. Likewise, you can use `OpExecutionContext.add_output_metadata` to attach metadata to an output without having to explicitly use the Output object.
- `OutputContext.log_event` provides a way to log AssetMaterializations from within the handle_output method of an IO manager without yielding. Likewise, output metadata can be added using `OutputContext.add_output_metadata`.
- [dagster-dbt] The load_assets_from_dbt_project function now returns a set of assets that map to a single dbt run command (rather than compiling each dbt model into a separate step). It also supports a new node_info_to_asset_key argument which allows you to customize the asset key that will be used for each dbt node.
- [dagster-airbyte] The dagster-airbyte integration now collects the Airbyte log output for each run as compute logs, and generates AssetMaterializations for each table that Airbyte updates or creates.
- [dagster-airbyte] The dagster-airbyte integration now supports the creation of software-defined assets, with the build_airbyte_assets function.
- [dagster-fivetran] The dagster-fivetran integration now supports the creation of software-defined assets with the build_fivetran_assets function.
- The multiprocess executor now supports choosing between spawn or forkserver for how its subprocesses are created. When using forkserver we attempt to intelligently preload modules to reduce the per-op overhead.
- [Helm] Labels can now be set on the Dagit and daemon deployments.
- [Helm] The default liveness and startup probes for Dagit and user deployments have been replaced with readiness probes. The liveness and startup probe for the Daemon has been removed. We observed and heard from users that under load, Dagit could fail the liveness probe which would result in the pod restarting. With the new readiness probe, the pod will not restart but will stop serving new traffic until it recovers. If you experience issues with any of the probe changes, you can revert to the old behavior by specifying liveness and startup probes in your Helm values (and reach out via an issue or Slack).
- [Helm] The Ingress v1 is now supported.

### Community Contributions

- Typo fix from @jiafi, thank you!

### Bugfixes

- Fixed an issue where long job names were truncated prematurely in the Jobs page in Dagit.
- Fixed an issue where loading the sensor timeline would sometimes load slowly or fail with a timeout error.
- Fixed an issue where the first time a run_status_sensor executed, it would sometimes run very slowly or time out.
- Fixed an issue where Launchpad mistakenly defaulted with invalid subset error in Dagit.
- Multi-component asset keys can now be used in the asset graph filter bar.
- Increased the storage query statement timeout to better handle more complex batch queries.
- Added fallback support for older versions of sqlite to service top-level repository views in Dagit (e.g. the top-level jobs, schedule, and sensor pages).

### Documentation

- Images in the documentation now enlarge when clicked.
- New example in examples/bollinger demonstrates dagster-pandera and TableSchema , and software-defined assets in the context of analyzing stock price data.

# 0.13.19

### New

- [dagit] Various performance improvements for asset graph views.
- [dagster-aws] The `EcsRunLauncher` can now override the `secrets_tag` parameter to None, which will cause it to not look for any secrets to be included in the tasks for the run. This can be useful in situations where the run launcher does not have permissions to query AWS Secretsmanager.

### Bugfixes

- [dagster-mysql] For instances using MySQL for their run storage, runs created using dagster versions `0.13.17` / `0.13.18` might display an incorrect timestamp for its start time on the Runs page. Running the `dagster instance migrate` CLI command should resolve the issue.

# 0.13.18

### New

- Op selection now supports selecting ops inside subgraphs. For example, to select an op `my_op` inside a subgraph `my_graph`, you can now specify the query as `"my_graph.my_op"`.
- The error message raised on failed Dagster type check on an output now includes the description provided on the TypeCheck object.
- The `dagster asset wipe` CLI command now takes a `--noprompt` option.
- Added the new `Map` config type, used to represent mappings between arbitrary scalar keys and typed values. For more information, see the [Map ConfigType docs](https://docs.dagster.io/_apidocs/types#dagster.Map).
- [`build_resources`](https://docs.dagster.io/master/concepts/resources#initializing-resources-outside-of-execution) has been added to the top level API. It provides a way to initialize resources outside of execution. This provides a way to use resources within the body of a sensor or schedule: https://github.com/dagster-io/dagster/issues/3794
- The `dagster-daemon` process now creates fewer log entries when no actions are taken (for example, if the run queue is empty)
- [dagster-k8s] When upgrading the Dagster helm chart, the old `dagster-daemon` pod will now spin down completely before the new `dagster-daemon` pod is started.
- [dagster-k8s] A flag can now be set in the Dagster helm chart to control whether the Kubernetes Jobs and Pods created by the `K8sRunLauncher` should fail if the Dagster run fails. To enable this flag, set the ``failPodOnRunFailure` key to true in the run launcher portion of the Helm chart.
- [dagster-dbt] Fixed compatibility issues with dbt 1.0. The `schema` and `data` arguments on the `DbtCliResource.test` function no longer need to be set to False to avoid errors, and the dbt output will be no longer be displayed in json format in the event logs.
- Dagster Types can now have metadata entries attached to them.
- `DagsterGraphQLClient` now supports submitting runs with op/solid sub-selections.
- [dagit] The Asset Catalog view will now include information from both AssetMaterializations and AssetObservation events for each asset.
- [dagit] [software-defined-assets] A warning will now be displayed if you attempt to backfill partitions of an asset whose upstream dependencies are missing.

### Bugfixes

- When Dagit fails to load a list of ops, the error message used the legacy term “solids”. Now it uses “ops”.
- Runs created using dagster versions `0.13.15` / `0.13.16` / `0.13.17` might display an incorrect timestamp for its start time on the Runs page. This would only happen if you had run a schema migration (using one of those versions) with the `dagster instance migrate` CLI command. Running the `dagster instance reindex` command should run a data migration that resolves this issue.
- When attempting to invoke run status sensors or run failure sensors, it will now incur an error. Run status/failure sensor invocation is not yet supported.
- [dagster-k8s] Fixed a bug in the sanitization of K8s label values with uppercase characters and underscores

### Community Contributions

- [software-defined-assets] Language in dagit has been updated from “refreshing” to “rematerializing” assets (thanks @Sync271!)
- [docs] The changelog page is now mobile friendly (thanks @keyz!)
- [docs] The loading shimmer for text on docs pages now has correct padding (also @keyz!)

### Experimental

- [software-defined-assets] The `namespace` argument of the `@asset` decorator now accepts a list of strings in addition to a single string.
- [memoization] Added a missing space to the error thrown when trying to use memoization without a persistent Dagster instance.
- [metadata] Two new metadata types, `TableSchemaMetadataEntryData` and `TableMetadataEntryData` allow you to emit metadata representing the schema / contents of a table, to be displayed in Dagit.

# 0.13.17

### New

- When a user-generated context.log call fails while writing to the event log, it will now log a system error in the event log instead of failing the run.
- [dagit] Made performance improvements to the Runs page, which can be realized after running an optional storage schema migration using dagster instance migrate.
- When a job is created from a graph, it will now use the graph’s description if a description is not explicitly provided to override it. (Thanks [@AndreaGiardini](https://github.com/AndreaGiardini)!)
- [dagit] Log job names are now truncated in Dagit.
- [dagit] The execution timezone is shown beside schedule cron strings, since their timezone may be UTC or a custom value.
- [dagit] Graph filter inputs now default to using quoted strings, and this syntax matches ops, steps, or assets via an exact string match. "build_table"+ will select that asset and it's downstream children without selecting another containing that string, such as build_table_result. Removing the quotes provides the old string matching behavior
- [dagster-aws] When using the emr_pyspark_step_launcher to run Dagster ops in an Amazon EMR cluster, the raw stdout output of the Spark driver is now written to stdout and will appear in the compute logs for the op in dagit, rather than being written to the Dagster event log.
- [dagit] Improved performance loading the Asset entry page in Dagit.

### Bugfixes

- [dagster-mysql] Added a schema migration script that was mistakenly omitted from 0.13.16. Migrating instance storage using dagster instance migrate should now complete without error.
- [dagster-airbyte] Fixed a packaging dependency issue with dagster-airbyte. (Thanks [bollwyvl](https://github.com/bollwyvl)!)
- Fixed a bug where config provided to the config arg on to_job required environment variables to exist at definition time.
- [dagit] The asset graph view now supports ops that yield multiple assets and renders long asset key paths correctly.
- [dagit] The asset graph’s filter input now allows you to filter on assets with multi-component key paths.
- [dagit] The asset graph properly displays downstream asset links to other asset jobs in your workspace.

### Experimental

- [dagster-celery-k8s] Experimental run monitoring is now supported with the CeleryK8sRunLauncher. This will detect when a run worker K8s Job has failed (due to an OOM, a Node shutting down, etc.) and mark the run as failed so that it doesn’t hang in STARTED. To enable this feature, set dagsterDaemon.runMonitoring.enabled to true in your Helm values.

### Documentation

- [dagster-snowflake] Fixed some example code in the API doc for snowflake_resource, which incorrectly constructed a Dagster job using the snowflake resource.

# 0.13.16

### New

- Added an integration with Airbyte, under the dagster-airbyte package (thanks Marcos Marx).
- An op that has a config schema is no longer required to have a context argument.

### Bugfixes

- Fixed an issue introduced in 0.13.13 where jobs with DynamicOutputs would fail when using the `k8s_job_executor` due to a label validation error when creating the step pod.
- In Dagit, when searching for asset keys on the Assets page, string matches beyond a certain character threshold on deeply nested key paths were ignored. This has been fixed, and all keys in the asset path are now searchable.
- In Dagit, links to Partitions views were broken in several places due to recent URL querystring changes, resulting in page crashes due to JS errors. These links have been fixed.
- The “Download Debug File” menu link is fixed on the Runs page in Dagit.
- In the “Launch Backfill” dialog on the Partitions page in Dagit, the range input sometimes discarded user input due to page updates. This has been fixed. Additionally, pressing the return key now commits changes to the input.
- When using a mouse wheel or touchpad gestures to zoom on a DAG view for a job or graph in Dagit, the zoom behavior sometimes was applied to the entire browser instead of just the DAG. This has been fixed.
- Dagit fonts now load correctly when using the `--path-prefix` option.
- Date strings in tool tips on time-based charts no longer duplicate the meridiem indicator.

### Experimental

- Software-defined assets can now be partitioned. The `@asset` decorator has a `partitions_def` argument, which accepts a `PartitionsDefinition` value. The asset details page in Dagit now represents which partitions are filled in.

### Documentation

- Fixed the documented return type for the `sync_and_poll` method of the dagster-fivetran resource (thanks Marcos Marx).
- Fixed a typo in the Ops concepts page (thanks Oluwashina Aladejubelo).

# 0.13.14

### New

- When you produce a PartitionedConfig object using a decorator like daily_partitioned_config or static_partitioned_config, you can now directly invoke that object to invoke the decorated function.
- The end_offset argument to PartitionedConfig can now be negative. This allows you to define a schedule that fills in partitions further in the past than the current partition (for example, you could define a daily schedule that fills in the partition from two days ago by setting end_offset to -1.
- The runConfigData argument to the launchRun GraphQL mutation can now be either a JSON-serialized string or a JSON object , instead of being required to be passed in as a JSON object. This makes it easier to use the mutation in typed languages where passing in unserialized JSON objects as arguments can be cumbersome.
- Dagster now always uses the local working directory when resolving local imports in job code, in all workspaces. In the case where you want to use a different base folder to resolve local imports in your code, the working_directory argument can now always be specified (before, it was only available when using the python_file key in your workspace). See the Workspace docs (https://docs.dagster.io/concepts/code-locations/workspace-files#loading-relative-imports) for more information.

### Bugfixes

- In Dagit, when viewing an in-progress run, the logic used to render the “Terminate” button was backward: it would appear for a completed run, but not for an in-progress run. This bug was introduced in 0.13.13, and is now fixed.
- Previously, errors in the instance’s configured compute log manager would cause runs to fail. Now, these errors are logged but do not affect job execution.
- The full set of DynamicOutputs returned by a op are no longer retained in memory if there is no hook to receive the values. This allows for DynamicOutput to be used for breaking up a large data set that can not fit in memory.

### Breaking Changes

- When running your own gRPC server to serve Dagster code, jobs that launch in a container using code from that server will now default to using dagster as the entry point. Previously, the jobs would run using PYTHON_EXECUTABLE -m dagster, where PYTHON_EXECUTABLE was the value of sys.executable on the gRPC server. For the vast majority of Dagster jobs, these entry points will be equivalent. To keep the old behavior (for example, if you have multiple Python virtualenvs in your image and want to ensure that runs also launch in a certain virtualenv), you can launch the gRPC server using the new ----use-python-environment-entry-point command-line arg.

### Community Contributions

- [bugfix] Fixed an issue where log levels on handlers defined in dagster.yaml would be ignored (thanks @lambdaTW!)

### Documentation

- Typo fix in the jobs page (thanks kmiku7 (https://github.com/kmiku7))!
- Added docs on how to modify k8s job TTL

### UI

- When re-launching a run, the log/step filters are now preserved in the new run’s page.
- Step execution times/recent runs now appear in the job/graph sidebar.

# 0.13.13

### New

- [dagster-dbt] dbt rpc resources now surface dbt log messages in the Dagster event log.
- [dagster-databricks] The `databricks_pyspark_step_launcher` now streams Dagster logs back from Databricks rather than waiting for the step to completely finish before exporting all events. Fixed an issue where all events from the external step would share the same timestamp. Immediately after execution, stdout and stderr logs captured from the Databricks worker will be automatically surfaced to the event log, removing the need to set the `wait_for_logs` option in most scenarios.
- [dagster-databricks] The `databricks_pyspark_step_launcher` now supports dynamically mapped steps.
- If the scheduler is unable to reach a code server when executing a schedule tick, it will now wait until the code server is reachable again before continuing, instead of marking the schedule tick as failed.
- The scheduler will now check every 5 seconds for new schedules to run, instead of every 30 seconds.
- The run viewer and workspace pages of Dagit are significantly more performant.
- Dagit loads large (100+ node) asset graphs faster and retrieves information about the assets being rendered only.
- When viewing an asset graph in Dagit, you can now rematerialize the entire graph by clicking a single “Refresh” button, or select assets to rematerialize them individually. You can also launch a job to rebuild an asset directly from the asset details page.
- When viewing a software-defined asset, Dagit displays its upstream and downstream assets in two lists instead of a mini-graph for easier scrolling and navigation. The statuses of these assets are updated in real-time. This new UI also resolves a bug where only one downstream asset would appear.

### Bugfixes

- Fixed bug where `execute_in_process` would not work for graphs with nothing inputs.
- In the Launchpad in Dagit, the `Ctrl+A` command did not correctly allow select-all behavior in the editor for non-Mac users, this has now been fixed.
- When viewing a DAG in Dagit and hovering on a specific input or output for an op, the connections between the highlighted inputs and outputs were too subtle to see. These are now a bright blue color.
- In Dagit, when viewing an in-progress run, a caching bug prevented the page from updating in real time in some cases. For instance, runs might appear to be stuck in a queued state long after being dequeued. This has been fixed.
- Fixed a bug in the `k8s_job_executor` where the same step could start twice in rare cases.
- Enabled faster queries for the asset catalog by migrating asset database entries to store extra materialization data.
- [dagster-aws] Viewing the compute logs for in-progress ops for instances configured with the `S3ComputeLogManager` would cause errors in Dagit. This is now fixed.
- [dagster-pandas] Fixed bug where Pandas categorical dtype did not work by default with dagster-pandas `categorical_column` constraint.
- Fixed an issue where schedules that yielded a `SkipReason` from the schedule function did not display the skip reason in the tick timeline in Dagit, or output the skip message in the dagster-daemon log output.
- Fixed an issue where the snapshot link of a finished run in Dagit would sometimes fail to load with a GraphQL error.
- Dagit now supports software-defined assets that are defined in multiple jobs within a repo, and displays a warning when assets in two repos share the same name.

### Breaking Changes

- We previously allowed schedules to be defined with cron strings like `@daily` rather than `0 0 * * *`. However, these schedules would fail to actually run successfully in the daemon and would also cause errors when viewing certain pages in Dagit. We now raise an `DagsterInvalidDefinitionError` for schedules that do not have a cron expression consisting of a 5 space-separated fields.

### Community Contributions

- In dagster-dask, a schema can now be conditionally specified for ops materializing outputs to parquet files, thank you [@kudryk](https://github.com/kudryk)!
- Dagster-gcp change from [@AndreaGiardini](https://github.com/AndreaGiardini) that replaces `get_bucket()` calls with `bucket()`, to avoid unnecessary bucket metadata fetches, thanks!
- Typo fix from [@sebastianbertoli](https://github.com/sebastianbertoli), thank you!
- [dagster-k8s] Kubernetes jobs and pods created by Dagster now have labels identifying the name of the Dagster job or op they are running. Thanks [@skirino](https://github.com/skirino)!

### Experimental

- [dagit] Made performance improvements for loading the asset graph.
- [dagit] The debug console logging output now tracks calls to fetch data from the database, to help track inefficient queries.

# 0.13.12

### New

- The dagit and dagster-daemon processes now use a structured Python logger for command-line output.
- Dagster command-line logs now include the system timezone in the logging timestamp.
- When running your own Dagster gRPC code server, the server process will now log a message to stdout when it starts up and when it shuts down.
- [dagit] The sensor details page and sensor list page now display links to the assets tracked by `@asset_sensor`s.
- [dagit] Improved instance warning in Dagit. Previously, Dagit showed an instance warning for daemon not running when no repos have schedulers or sensors.
- [dagster-celery-k8s] You can now specify volumes and volume mounts to runs using the `CeleryK8sRunLauncher` that will be included in all launched jobs.
- [dagster-databricks] You are no longer required to specify storage configuration when using the databricks_pyspark_step_launcher.
- [dagster-databricks] The databricks_pyspark_step_launcher can now be used with dynamic mapping and collect steps.
- [dagster-mlflow] The `end_mlflow_on_run_finished` hook is now a top-level export of the dagster mlflow library. The API reference also now includes an entry for it.

### Bugfixes

- Better backwards-compatibility for fetching asset keys materialized from older versions of dagster.
- Fixed an issue where jobs running with op subsets required some resource configuration as part of the run config, even when they weren’t required by the selected ops.
- `RetryPolicy` is now respected when execution is interrupted.
- [dagit] Fixed "Open in Playground" link on the scheduled ticks.
- [dagit] Fixed the run ID links on the Asset list view.
- [dagit] When viewing an in-progress run, the run status sometimes failed to update as new logs arrived, resulting in a Gantt chart that either never updated from a “queued” state or did so only after a long delay. The run status and Gantt chart now accurately match incoming logs.

### Community Contributions

- [dagster-k8s] Fixed an issue where specifying `job_metadata` in tags did not correctly propagate to Kubernetes jobs created by Dagster. Thanks [@ibelikov](https://github.com/ibelikov)!

### Experimental

- [dagit] Made performance improvements for loading the asset graph.

### Documentation

- The Versioning and Memoization guide has been updated to reflect a new set of core memoization APIs.
- [dagster-dbt] Updated the dagster-dbt integration guide to mention the new dbt Cloud integration.
- [dagster-dbt] Added documentation for the `default_flags` property of `DbtCliResource`.

# 0.13.11

### New

- [dagit] Made performance improvements to the Run page.
- [dagit] Highlighting a specific sensor / schedule ticks is now reflected in a shareable URL.

### Bugfixes

- [dagit] On the Runs page, when filtering runs with a tag containing a comma, the filter input would incorrectly break the tag apart. This has been fixed.
- [dagit] For sensors that do not target a specific job (e.g. un_status_sensor, we are now hiding potentially confusing Job details
- [dagit] Fixed an issue where some graph explorer views generated multiple scrollbars.
- [dagit] Fixed an issue with the Run view where the Gantt view incorrectly showed in-progress steps when the run had exited.
- [dagster-celery-k8s] Fixed an issue where setting a custom Celery broker URL but not a custom Celery backend URL in the helm chart would produce an incorrect Celery configuration.
- [dagster-k8s] Fixed an issue where Kubernetes volumes using list or dict types could not be set in the Helm chart.

### Community Contributions

- [dagster-k8s] Added the ability to set a custom location name when configuring a workspace in the Helm chart. Thanks [@pcherednichenko!](https://github.com/pcherednichenko)

### Experimental

- [dagit] Asset jobs now display with spinners on assets that are currently in progress.
- [dagit] Assets jobs that are in progress will now display a dot icon on all assets that are not yet running but will be re-materialized in the run.
- [dagit] Fixed broken links to the asset catalog entries from the explorer view of asset jobs.
- The `AssetIn` input object now accepts an asset key so upstream assets can be explicitly specified (e.g. `AssetIn(asset_key=AssetKey("asset1"))`)
- The `@asset` decorator now has an optional `non_argument_deps` parameter that accepts AssetKeys of assets that do not pass data but are upstream dependencies.
- `ForeignAsset` objects now have an optional `description` attribute.

### Documentation

- “Validating Data with Dagster Type Factories” guide added.

# 0.13.10

### New

- `run_id`, `job_name`, and `op_exception` have been added as parameters to `build_hook_context`.
- You can now define inputs on the top-level job / graph. Those inputs can be can configured as an inputs key on the top level of your run config. For example, consider the following job:

```python
from dagster import job, op

@op
def add_one(x):
    return x + 1

@job
def my_job(x):
    add_one(x)
```

You can now add config for x at the top level of my run_config like so:

```python
run_config = {
  "inputs": {
    "x": {
      "value": 2
    }
  }
}
```

- You can now create partitioned jobs and reference a run’s partition from inside an op body or IOManager load_input or handle_output method, without threading partition values through config. For example, where previously you might have written:

```python
@op(config_schema={"partition_key": str})
def my_op(context):
    print("partition_key: " + context.op_config["partition_key"])

@static_partitioned_config(partition_keys=["a", "b"])
def my_static_partitioned_config(partition_key: str):
    return {"ops": {"my_op": {"config": {"partition_key": partition_key}}}}

@job(config=my_static_partitioned_config)
def my_partitioned_job():
    my_op()
```

You can now write:

```python
@op
def my_op(context):
    print("partition_key: " + context.partition_key)

@job(partitions_def=StaticPartitionsDefinition(["a", "b"]))
def my_partitioned_job():
    my_op()
```

- Added `op_retry_policy` to `@job`. You can also specify `op_retry_policy` when invoking `to_job` on graphs.
- [dagster-fivetran] The `fivetran_sync_op` will now be rendered with a fivetran tag in Dagit.
- [dagster-fivetran] The `fivetran_sync_op` now supports producing `AssetMaterializations` for each table updated during the sync. To this end, it now outputs a structured `FivetranOutput` containing this schema information, instead of an unstructured dictionary.
- [dagster-dbt] `AssetMaterializations` produced from the dbt_cloud_run_op now include a link to the dbt Cloud docs for each asset (if docs were generated for that run).
- You can now use the `@schedule` decorator with `RunRequest` - based evaluation functions. For example, you can now write:

```python
@schedule(cron_schedule="* * * * *", job=my_job)
def my_schedule(context):
    yield RunRequest(run_key="a", ...)
    yield RunRequest(run_key="b", ...)
```

- [dagster-k8s] You may now configure instance-level `python_logs` settings using the [Dagster Helm chart](https://github.com/dagster-io/dagster/tree/master/helm/dagster).
- [dagster-k8s] You can now manage a secret that contains the Celery broker and backend URLs, rather than the Helm chart
- [Dagster-slack] Improved the default messages in `make_slack_on_run_failure_sensor` to use Slack layout blocks and include clickable link to Dagit. Previously, it sent a plain text message.

### Dagit

- Made performance improvements to the Run page.
- The Run page now has a pane control that splits the Gantt view and log table evenly on the screen.
- The Run page now includes a list of succeeded steps in the status panel next to the Gantt chart.
- In the Schedules list, execution timezone is now shown alongside tick timestamps.
- If no repositories are successfully loaded when viewing Dagit, we now redirect to /workspace to quickly surface errors to the user.
- Increased the size of the reload repository button
- Repositories that had been hidden from the left nav became inaccessible when loaded in a workspace containing only that repository. Now, when loading a workspace containing a single repository, jobs for that repository will always appear in the left nav.
- In the Launchpad, selected ops were incorrectly hidden in the lower right panel.
- Repaired asset search input keyboard interaction.
- In the Run page, the list of previous runs was incorrectly ordered based on run ID, and is now ordered by start time.
- Using keyboard commands with the / key (e.g. toggling commented code) in the config editor

### Bugfixes

- Previously, if an asset in software-defined assets job depended on a `ForeignAsset`, the repository containing that job would fail to load.
- Incorrectly triggered global search. This has been fixed.
- Fix type on tags of EMR cluster config (thanks [Chris](https://github.com/cdchan))!
- Fixes to the tests in dagster new-project , which were previously using an outdated result API (thanks [Vašek](https://github.com/illagrenan))!

### Experimental

- You can now mount AWS Secrets Manager secrets as environment variables in runs launched by the `EcsRunLauncher`.
- You can now specify the CPU and Memory for runs launched by the `EcsRunLauncher`.
- The `EcsRunLauncher` now dynamically chooses between assigning a public IP address or not based on whether it’s running in a public or private subnet.
- The `@asset` and `@multi_asset` decorator now return `AssetsDefinition` objects instead of `OpDefinitions`

### Documentation

- The tutorial now uses `get_dagster_logger` instead of `context.log`.
- In the API docs, most configurable objects (such as ops and resources) now have their configuration schema documented in-line.
- Removed typo from CLI readme (thanks Kan (https://github.com/zkan))!

# 0.13.9

### New

- Memoization can now be used with the multiprocess, k8s, celery-k8s, and dask executors.

# 0.13.8

### New

- Improved the error message for situations where you try `a, b = my_op()`, inside `@graph` or `@job`, but `my`\_op only has a single `Out`.
- [dagster-dbt] A new integration with dbt Cloud allows you to launch dbt Cloud jobs as part of your Dagster jobs. This comes complete with rich error messages, links back to the dbt Cloud UI, and automatically generated [Asset Materializations](https://docs.dagster.io/concepts/assets/asset-materializations) to help keep track of your dbt models in Dagit. It provides a pre-built `dbt_cloud_run_op`, as well as a more flexible `dbt_cloud_resource` for more customized use cases. Check out the [api docs](https://docs.dagster.io/_apidocs/libraries/dagster-dbt#ops) to learn more!
- [dagster-gcp] Pinned the google-cloud-bigquery dependency to <3, because the new 3.0.0b1 version was causing some problems in tests.
- [dagit] Verbiage update to make it clear that wiping an asset means deleting the materialization events for that asset.

### Bugfixes

- Fixed a bug with the `pipeline launch` / `job launch` CLIs that would spin up an ephemeral dagster instance for the launch, then tear it down before the run actually executed. Now, the CLI will enforce that your instance is non-ephemeral.
- Fixed a bug with re-execution when upstream step skips some outputs. Previously, it mistakenly tried to load inputs from parent runs. Now, if an upstream step doesn’t yield outputs, the downstream step would skip.
- [dagit] Fixed a bug where configs for unsatisfied input wasn’t properly resolved when op selection is specified in Launchpad.
- [dagit] Restored local font files for Inter and Inconsolata instead of using the Google Fonts API. This allows correct font rendering for offline use.
- [dagit] Improved initial workspace loading screen to indicate loading state instead of showing an empty repository message.

### Breaking Changes

- The `pipeline` argument of the `InitExecutorContext` constructor has been changed to `job`.

### Experimental

- The `@asset` decorator now accepts a `dagster_type` argument, which determines the DagsterType for the output of the asset op.
- `build_assets_job` accepts an `executor_def` argument, which determines the executor for the job.

### Documentation

- A docs section on context manager resources has been added. Check it out [here](https://docs.dagster.io/concepts/resources#context-manager-resources).
- Removed the versions of the Hacker News example jobs that used the legacy solid & pipeline APIs.

# 0.13.7

### New

- The Runs page in Dagit now loads much more quickly.

### Bugfixes

- Fixed an issue where Dagit would sometimes display a red "Invalid JSON" error message.

### Dependencies

- `google-cloud-bigquery` is temporarily pinned to be prior to version 3 due to a breaking change in that version.

# 0.13.6

### Bugfixes

- Previously, the `EcsRunLauncher` tagged each ECS task with its corresponding Dagster Run ID. ECS tagging isn't supported for AWS accounts that have not yet [migrated to using the long ARN format](https://aws.amazon.com/blogs/compute/migrating-your-amazon-ecs-deployment-to-the-new-arn-and-resource-id-format-2/). Now, the `EcsRunLauncher` only adds this tag if your AWS account has the long ARN format enabled.
- Fixed a bug in the `k8s_job_executor` and `docker_executor` that could result in jobs exiting as `SUCCESS` before all ops have run.
- Fixed a bug in the `k8s_job_executor` and `docker_executor` that could result in jobs failing when an op is skipped.

### Dependencies

- `graphene` is temporarily pinned to be prior to version 3 to unbreak Dagit dependencies.

# 0.13.5

### New

- [dagster-fivetran] A new dagster-fivetran integration allows you to launch Fivetran syncs and monitor their progress from within Dagster. It provides a pre-built `fivetran_sync_op`, as well as a more flexible `fivetran_resource` for more customized use cases. Check out the [api docs](https://docs.dagster.io/_apidocs/libraries/dagster-fivetran) to learn more!
- When inferring a graph/job/op/solid/pipeline description from the docstring of the decorated function, we now dedent the docstring even if the first line isn’t indented. This allows descriptions to be formatted nicely even when the first line is on the same line as the triple-quotes.
- The `SourceHashVersionStrategy` class has been added, which versions `op` and `resource` code. It can be provided to a job like so:

```
from dagster import job, SourceHashVersionStrategy

@job(version_strategy=SourceHashVersionStrategy())
def my_job():
     ...
```

- [dagit] Improved performance on the initial page load of the Run page, as well as the partitions UI / launch backfill modal
- [dagit] Fixed a bug where top-level graphs in the repo could not be viewed in the `Workspace` > `Graph` view.

### Bugfixes

- Fixed an issue where turning a partitioned schedule off and on again would sometimes result in unexpected past runs being created. (#5604)
- Fixed an issue where partition sets that didn’t return a new copy of run configuration on each function call would sometimes apply the wrong config to partitions during backfills.
- Fixed rare issue where using dynamic outputs in combination with optional outputs would cause errors when using certain executors.
- [dagster-celery-k8s] Fixed bug where CeleryK8s executor would not respect job run config
- [dagit] Fixed bug where graphs would sometimes appear off-center.

### Breaking Changes

- In 0.13.0, job CLI commands executed via `dagster job` selected both pipelines and jobs. This release changes the `dagster job` command to select only jobs and not pipelines.

### Community Contributions

- [dagster-dask] Updated DaskClusterTypes to have the correct import paths for certain cluster managers (thanks @[kudryk](https://github.com/kudryk)!)
- [dagster-azure] Updated version requirements for Azure to be more recent and more permissive (thanks @[roeap](https://github.com/roeap) !)
- [dagster-shell] Ops will now copy the host environment variables at runtime, rather than copying them from the environment that their job is launched from (thanks @[alexismanuel](https://github.com/alexismanuel) !)

### Documentation

- The job, op, graph migration guide was erroneously marked experimental. This has been fixed.

# 0.13.4

### New

- [dagster-k8s] The [`k8s_job_executor`](https://docs.dagster.io/_apidocs/libraries/dagster-k8s#dagster_k8s.k8s_job_executor) is no longer experimental, and is recommended for production workloads. This executor runs each op in a separate Kubernetes job. We recommend this executor for Dagster jobs that require greater isolation than the `multiprocess` executor can provide within a single Kubernetes pod. The `celery_k8s_job_executor` will still be supported, but is recommended only for use cases where Celery is required (The most common example is to offer step concurrency limits using multiple Celery queues). Otherwise, the `k8s_job_executor` is the best way to get Kubernetes job isolation.
- [dagster-airflow] Updated dagster-airflow to better support job/op/graph changes by adding a `make_dagster_job_from_airflow_dag` factory function. Deprecated `pipeline_name` argument in favor of `job_name` in all the APIs.
- Removed a version pin of the `chardet` library that was required due to an incompatibility with an old version of the `aiohttp` library, which has since been fixed.
- We now raise a more informative error if the wrong type is passed to the `ins` argument of the `op` decorator.
- In the Dagit Launchpad, the button for launching a run now says “Launch Run” instead of “Launch Execution”

### Bugfixes

- Fixed an issue where job entries from Dagit search navigation were not linking to the correct job pages.
- Fixed an issue where jobs / pipelines were showing up instead of the underlying graph in the list of repository graph definitions.
- Fixed a bug with using custom loggers with default config on a job.
- [dagster-slack] The `slack_on_run_failure_sensor` now says “Job” instead of “Pipeline” in its default message.

### Community Contributions

- Fixed a bug that was incorrectly causing a `DagsterTypeCheckDidNotPass` error when a Dagster Type contained a List inside a Tuple (thanks [@jan-eat](https://github.com/jan-eat)!)
- Added information for setting DAGSTER_HOME in Powershell and batch for windows users. (thanks [@slamer59](https://github.com/slamer59)!)

### Experimental

- Changed the job explorer view in Dagit to show asset-based graphs when the experimental Asset API flag is turned on for any job that has at least one software-defined asset.

### Documentation

- Updated API docs and integration guides to reference job/op/graph for various libraries (`dagstermill`, `dagster-pandas`, `dagster-airflow`, etc)
- Improved documentation when attempting to retrieve output value from `execute_in_process`, when job does not have a top-level output.

# 0.13.3

### Bugfixes

- [dagster-k8s] Fixed a bug that caused retries to occur twice with the `k8s_job_executor`

# 0.13.2

### New

- Updated dagstermill to better support job/op/graph changes by adding a `define_dagstermill_op` factory function. Also updated documentation and examples to reflect these changes.
- Changed run history for jobs in Dagit to include legacy mode tags for runs that were created from pipelines that have since been converted to use jobs.
- The new [get_dagster_logger()](https://docs.dagster.io/_apidocs/utilities#dagster.utils.log.get_dagster_logger) method is now importable from the top level dagster module (`from dagster import get_dagster_logger`)
- [dagster-dbt] All dagster-dbt resources (`dbt_cli_resource`, `dbt_rpc_resource`, and `dbt_rpc_sync_resource`) now support the `dbt ls` command: `context.resources.dbt.ls()`.
- Added `ins` and `outs` properties to `OpDefinition`.
- Updated the run status favicon of the Run page in Dagit.
- There is now a `resources_config` argument on `build_solid_context`. The config argument has been renamed to `solid_config`.
- [helm] When deploying Redis using the Dagster helm chart, by default the new cluster will not require authentication to start a connection to it.
- [dagster-k8s] The component name on Kubernetes jobs for run and step workers is now `run_worker` and `step_worker`, respectively.
- Improved performance for rendering the Gantt chart on the Run page for runs with very long event logs.

### Bugfixes

- Fixed a bug where decorating a job with a hook would create a pipeline.
- Fixed a bug where providing default logger config to a job would break with a confusing error.
- Fixed a bug with retrieving output results from a mapped input on `execute_in_process`
- Fixed a bug where schedules referencing a job were not creating runs using that job’s default run config.
- [dagster-k8s] Fixed a bug where the retry mode was not being passed along through the k8s executor.

### Breaking Changes

- The first argument on `Executor.execute(...)` has changed from `pipeline_context` to `plan_context`

### Community Contributions

- When using multiple Celery workers in the Dagster helm chart, each worker can now be individually configured. See the [helm chart](https://github.com/dagster-io/dagster/blob/master/helm/dagster/values.yaml#L436-L448) for more information. Thanks [@acrulopez](https://github.com/acrulopez)!
- [dagster-k8s] Changed Kubernetes job containers to use the fixed name `dagster`, rather than repeating the job name. Thanks [@skirino](https://github.com/dagster-io/dagster/commits?author=skirino)!

### Experimental

- [dagster-docker] Added a new `docker_executor` which executes steps in separate Docker containers.
- The dagster-daemon process can now detect hanging runs and restart crashed run workers. Currently
  only supported for jobs using the `docker_executor` and `k8s_job_executor`. Enable this feature in your dagster.yaml with:

  ```
  run_monitoring:
    enabled: true
  ```

  Documentation coming soon. Reach out in the #dagster-support Slack channel if you are interested in using this feature.

### Documentation

- Adding “Python Logging” back to the navigation pane.
- Updated documentation for `dagster-aws`, `dagster-github`, and `dagster-slack` to reference job/op/graph APIs.

# 0.13.1

### New

- All dbt resources ([dbt_cli_resource](https://docs.dagster.io/_apidocs/libraries/dagster-dbt#dagster_dbt.dbt_cli_resource), [dbt_rpc_resource](https://docs.dagster.io/_apidocs/libraries/dagster-dbt#dagster_dbt.dbt_rpc_resource), and [dbt_rpc_sync_resource](https://docs.dagster.io/_apidocs/libraries/dagster-dbt#dagster_dbt.dbt_rpc_sync_resource)) now support the `ls` command.

### Docs

- Various fixes to broken links on pages in 0.13.0 docs release

### Bug fixes

- Previously, the Dagster CLI would use a completely ephemeral dagster instance if $DAGSTER_HOME was not set. Since the new job abstraction by default requires a non-ephemeral dagster instance, this has been changed to instead create a persistent instance that is cleaned up at the end of an execution.

### Dagit

- Run-status-colorized dagster logo is back on job execution page
- Improvements to Gantt chart color scheme

# 0.13.0 "Get the Party Started"

### Major Changes

- The job, op, and graph APIs now represent the stable core of the system, and replace pipelines, solids, composite solids, modes, and presets as Dagster’s core abstractions. All of Dagster’s documentation - tutorials, examples, table of contents - is in terms of these new core APIs. Pipelines, modes, presets, solids, and composite solids are still supported, but are now considered “Legacy APIs”. We will maintain backcompatibility with the legacy APIs for some time, however, we believe the new APIs represent an elegant foundation for Dagster going forward. As time goes on, we will be adding new features that only apply to the new core. All in all, the new APIs provide increased clarity - they unify related concepts, make testing more lightweight, and simplify operational workflows in Dagit. For comprehensive instructions on how to transition to the new APIs, refer to the [migration guide](https://legacy-versioned-docs.dagster.dagster-docs.io/0.15.7/guides/dagster/graph_job_op).
- Dagit has received a complete makeover. This includes a refresh to the color palette and general design patterns, as well as functional changes that make common Dagit workflows more elegant. These changes are designed to go hand in hand with the new set of core APIs to represent a stable core for the system going forward.
- You no longer have to pass a context object around to do basic logging. Many updates have been made to our logging system to make it more compatible with the python logging module. You can now capture logs produced by standard python loggers, set a global python log level, and set python log handlers that will be applied to every log message emitted from the Dagster framework. Check out the docs [here](https://docs.dagster.io/concepts/logging/python-logging)!
- The Dagit “playground” has been re-named into the Dagit “launchpad”. This reflects a vision of the tool closer to how our users actually interact with it - not just a testing/development tool, but also as a first-class starting point for many one-off workflows.
- Introduced a new integration with Microsoft Teams, which includes a connection resource and support for sending messages to Microsoft Teams. See details in the [API Docs](https://docs.dagster.io/_apidocs/libraries/dagster-msteams) (thanks [@iswariyam](https://github.com/iswariyam)!).
- Intermediate storages, which were deprecated in 0.10.0, have now been removed. Refer to the “Deprecation: Intermediate Storage” section of the [0.10.0 release notes](https://github.com/dagster-io/dagster/releases/tag/0.10.0) for how to use IOManagers instead.
- The pipeline-level event types in the run log have been renamed so that the PIPELINE prefix has been replaced with RUN. For example, the PIPELINE_START event is now the RUN_START event.

### New since 0.12.15

- Addition of get_dagster_logger function, which creates a python loggers whose output messages will be captured and converted into Dagster log messages.

### Community Contributions

- The run_config attribute is now available on ops/solids built using the build_op_context or build_solid_context functions. Thanks [@jiafi](https://github.com/jiafi)!
- Limit configuration of applyLimitPerUniqueValue in k8s environments. Thanks [@cvb](https://github.com/cvb)!
- Fix for a solid’s return statement in the intro tutorial. Thanks [@dbready](https://github.com/dbready)!
- Fix for a bug with output keys in the s3_pickle_io_manager. Thanks [@jiafi](https://github.com/jiafi)!

### Breaking Changes

- We have renamed a lot of our GraphQL Types to reflect our emphasis on the new job/op/graph APIs. We have made the existing types backwards compatible so that GraphQL fragments should still work. However, if you are making custom GraphQL requests to your Dagit webserver, you may need to change your code to handle the new types.
- We have paired our GraphQL changes with changes to our Python GraphQL client. If you have upgraded the version of your Dagit instance, you will most likely also want to upgrade the version of your Python GraphQL client.

### Improvements

- Solid, op, pipeline, job, and graph descriptions that are inferred from docstrings now have leading whitespaces stripped out.
- Improvements to how we cache and store step keys should speed up dynamic workflows with many dynamic outputs significantly.

### Bugfixes

- Fixed a bug where kwargs could not be used to set the context when directly invoking a solid. IE my_solid(context=context_obj).
- Fixed a bug where celery-k8s config did not work in the None case:

```yaml
execution:
  celery-k8s:
```

### Experimental

- Removed the lakehouse library, whose functionality is subsumed by @asset and build_assets_job in Dagster core.

### Documentation

- Removed the trigger_pipeline example, which was not referenced in docs.
- dagster-mlflow APIs have been added to API docs.

# 0.12.15

### Community Contributions

- You can now configure credentials for the `GCSComputeLogManager` using a string or environment variable instead of passing a path to a credentials file. Thanks @silentsokolov!
- Fixed a bug in the dagster-dbt integration that caused the DBT RPC solids not to retry when they received errors from the server. Thanks @cdchan!
- Improved helm schema for the QueuedRunCoordinator config. Thanks @cvb!

### Bugfixes

- Fixed a bug where `dagster instance migrate` would run out of memory when migrating over long run histories.

### Experimental

- Fixed broken links in the Dagit workspace table view for the experimental software-defined assets feature.

# 0.12.14

### Community Contributions

- Updated click version, thanks @ashwin153!
- Typo fix, thanks @geoHeil!

### Bugfixes

- Fixed a bug in `dagster_aws.s3.sensor.get_s3_keys` that would return no keys if an invalid s3 key was provided
- Fixed a bug with capturing python logs where statements of the form `my_log.info("foo %s", "bar")` would cause errors in some scenarios.
- Fixed a bug where the scheduler would sometimes hang during fall Daylight Savings Time transitions when Pendulum 2 was installed.

### Experimental

- Dagit now uses an asset graph to represent jobs built using `build_assets_job`. The asset graph shows each node in the job’s graph with metadata about the asset it corresponds to - including asset materializations. It also contains links to upstream jobs that produce assets consumed by the job, as well as downstream jobs that consume assets produced by the job.
- Fixed a bug in `load_assets_from_dbt_project` and `load_assets_from_dbt_project` that would cause runs to fail if no `runtime_metadata_fn` argument were supplied.
- Fixed a bug that caused `@asset` not to infer the type of inputs and outputs from type annotations of the decorated function.
- `@asset` now accepts a `compute_kind` argument. You can supply values like “spark”, “pandas”, or “dbt”, and see them represented as a badge on the asset in the Dagit asset graph.

# 0.12.13

### Community Contributions

- Changed `VersionStrategy.get_solid_version` and `VersionStrategy.get_resource_version` to take in a `SolidVersionContext` and `ResourceVersionContext`, respectively. This gives VersionStrategy access to the config (in addition to the definition object) when determining the code version for memoization. (Thanks [@RBrossard](https://github.com/RBrossard)!).

  **Note:** This is a breaking change for anyone using the experimental `VersionStrategy` API. Instead of directly being passed `solid_def` and `resource_def`, you should access them off of the context object using `context.solid_def` and `context.resource_def` respectively.

### New

- [dagster-k8s] When launching a pipeline using the K8sRunLauncher or k8s_job_executor, you can know specify a list of volumes to be mounted in the created pod. See the [API docs](https://docs.dagster.io/_apidocs/libraries/dagster-k8s#dagster_k8s.K8sRunLauncher) for for information.
- [dagster-k8s] When specifying a list of environment variables to be included in a pod using [custom configuration](https://docs.dagster.io/deployment/guides/kubernetes/customizing-your-deployment#solid-or-pipeline-kubernetes-configuration), you can now specify the full set of parameters allowed by a [V1EnvVar](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.19/#envvar-v1-core) in Kubernetes.

### Bugfixes

- Fixed a bug where mapping inputs through nested composite solids incorrectly caused validation errors.
- Fixed a bug in Dagit, where WebSocket reconnections sometimes led to logs being duplicated on the Run page.
- Fixed a bug In Dagit, where log views that were scrolled all the way down would not auto-scroll as new logs came in.

### Documentation

- Added documentation for new (experimental) python logging [configuration options](https://docs.dagster.io/concepts/logging/python-logging#python-logging)

# 0.12.12

### Community Contributions

- [dagster-msteams] Introduced a new integration with Microsoft Teams, which includes a connection resource and support for sending messages to Microsoft Teams. See details in the [API Docs](https://docs.dagster.io/_apidocs/libraries/dagster-msteams) (thanks [@iswariyam](https://github.com/iswariyam)!).
- Fixed a mistake in the sensors docs (thanks [@vitorbaptista](https://github.com/vitorbaptista))!

### Bugfixes

- Fixed a bug that caused run status sensors to sometimes repeatedly fire alerts.
- Fixed a bug that caused the `emr_pyspark_step_launcher` to fail when stderr included non-Log4J-formatted lines.
- Fixed a bug that caused `applyPerUniqueValue` config on the `QueuedRunCoordinator` to fail Helm schema validation.
- [dagster-shell] Fixed an issue where a failure while executing a shell command sometimes didn’t raise a clear explanation for the failure.

### Experimental

- Added experimental `@asset` decorator and `build_assets_job` APIs to construct asset-based jobs, along with Dagit support.
- Added `load_assets_from_dbt_project` and `load_assets_from_dbt_manifest`, which enable constructing asset-based jobs from DBT models.

# 0.12.11

### Community Contributions

- [helm] The ingress now supports TLS (thanks @cpmoser!)
- [helm] Fixed an issue where dagit could not be configured with an empty workspace (thanks @yamrzou!)

### New

- [dagstermill] You can now have more precise IO control over the output notebooks by specifying `output_notebook_name` in `define_dagstermill_solid` and providing your own IO manager via "output_notebook_io_manager" resource key.
- We've deprecated `output_notebook` argument in `define_dagstermill_solid` in favor of `output_notebook_name`.
- Previously, the output notebook functionality requires “file_manager“ resource and result in a FileHandle output. Now, when specifying output_notebook_name, it requires "output_notebook_io_manager" resource and results in a bytes output.
- You can now customize your own "output_notebook_io_manager" by extending OutputNotebookIOManager. A built-in `local_output_notebook_io_manager` is provided for handling local output notebook materialization.
- See detailed migration guide in https://github.com/dagster-io/dagster/pull/4490.

- Dagit fonts have been updated.

### Bugfixes

- Fixed a bug where log messages of the form `context.log.info("foo %s", "bar")` would not get formatted as expected.
- Fixed a bug that caused the `QueuedRunCoordinator`’s `tag_concurrency_limits` to not be respected in some cases
- When loading a Run with a large volume of logs in Dagit, a loading state is shown while logs are retrieved, clarifying the loading experience and improving render performance of the Gantt chart.
- Using solid selection with pipelines containing dynamic outputs no longer causes unexpected errors.

### Experimental

- You can now set tags on a graph by passing in a dictionary to the `tags` argument of the `@graph` decorator or `GraphDefinition` constructor. These tags will be set on any runs of jobs are built from invoking `to_job` on the graph.
- You can now set separate images per solid when using the `k8s_job_executor` or `celery_k8s_job_executor`. Use the key `image` inside the `container_config` block of the [k8s solid tag](https://docs.dagster.io/deployment/guides/kubernetes/customizing-your-deployment#solid-or-pipeline-kubernetes-configuration).
- You can now target multiple jobs with a single sensor, by using the `jobs` argument. Each `RunRequest` emitted from a multi-job sensor’s evaluation function must specify a `job_name`.

# 0.12.10

### Community Contributions

- [helm] The `KubernetesRunLauncher` image pull policy is now configurable in a separate field (thanks [@yamrzou](https://github.com/yamrzou)!).
- The `dagster-github` package is now usable for GitHub Enterprise users (thanks [@metinsenturk](https://github.com/metinsenturk)!) A hostname can now be provided via config to the dagster-github resource with the key `github_hostname`:

```
execute_pipeline(
      github_pipeline, {'resources': {'github': {'config': {
           "github_app_id": os.getenv('GITHUB_APP_ID'),
           "github_app_private_rsa_key": os.getenv('GITHUB_PRIVATE_KEY'),
           "github_installation_id": os.getenv('GITHUB_INSTALLATION_ID'),
           "github_hostname": os.getenv('GITHUB_HOSTNAME'),
      }}}}
)
```

### New

- Added a database index over the event log to improve the performance of `pipeline_failure_sensor` and `run_status_sensor` queries. To take advantage of these performance gains, run a schema migration with the CLI command: `dagster instance migrate`.

### Bugfixes

- Performance improvements have been made to allow dagit to more gracefully load a run that has a large number of events.
- Fixed an issue where `DockerRunLauncher` would raise an exception when no networks were specified in its configuration.

### Breaking Changes

- `dagster-slack` has migrated off of deprecated [`slackclient` (deprecated)](http://slackclient/) and now uses `[slack_sdk](https://slack.dev/python-slack-sdk/v3-migration/)`.

### Experimental

- `OpDefinition`, the replacement for `SolidDefinition` which is the type produced by the `@op` decorator, is now part of the public API.
- The `daily_partitioned_config`, `hourly_partitioned_config`, `weekly_partitioned_config`, and `monthly_partitioned_config` now accept an `end_offset` parameter, which allows extending the set of partitions so that the last partition ends after the current time.

# 0.12.9

### Community Contributions

- A service account can now be specified via Kubernetes tag configuration (thanks [@skirino](https://github.com/skirino)) !

### New

- Previously in Dagit, when a repository location had an error when reloaded, the user could end up on an empty page with no context about the error. Now, we immediately show a dialog with the error and stack trace, with a button to try reloading the location again when the error is fixed.
- Dagster is now compatible with Python’s logging module. In your config YAML file, you can configure log handlers and formatters that apply to the entire Dagster instance. Configuration instructions and examples detailed in the docs: https://docs.dagster.io/concepts/logging/python-logging
- [helm] The timeout of database statements sent to the Dagster instance can now be configured using `.dagit.dbStatementTimeout`.

- The `QueuedRunCoordinator` now supports setting separate limits for each unique value with a certain key. In the below example, 5 runs with the tag `(backfill: first)` could run concurrently with 5 other runs with the tag `(backfill: second)`.

```yaml
run_coordinator:
  module: dagster.core.run_coordinator
  class: QueuedRunCoordinator
  config:
    tag_concurrency_limits:
      - key: backfill
        value:
          applyLimitPerUniqueValue: True
        limit: 5
```

### Bugfixes

- Previously, when specifying hooks on a pipeline, resource-to-resource dependencies on those hooks would not be resolved. This is now fixed, so resources with dependencies on other resources can be used with hooks.
- When viewing a run in Dagit, the run status panel to the right of the Gantt chart did not always allow scrolling behavior. The entire panel is now scrollable, and sections of the panel are collapsible.
- Previously, attempting to directly invoke a solid with Nothing inputs would fail. Now, the defined behavior is that Nothing inputs should not be provided to an invocation, and the invocation will not error.
- Skip and fan-in behavior during execution now works correctly when solids with dynamic outputs are skipped. Previously solids downstream of a dynamic output would never execute.
- [helm] Fixed an issue where the image tag wasn’t set when running an instance migration job via `.migrate.enabled=True`.

# 0.12.8

### New

- Added `instance` on `RunStatusSensorContext` for accessing the Dagster Instance from within the
  run status sensors.
- The inputs of a Dagstermill solid now are loaded the same way all other inputs are loaded in the
  framework. This allows rerunning output notebooks with properly loaded inputs outside Dagster
  context. Previously, the IO handling depended on temporary marshal directory.
- Previously, the Dagit CLI could not target a bare graph in a file, like so:

  ```python
  from dagster import op, graph

  @op
  def my_op():
      pass

  @graph
  def my_graph():
      my_op()
  ```

  This has been remedied. Now, a file `foo.py` containing just a graph can be targeted by the dagit
  CLI: `dagit -f foo.py`.

- When a solid, pipeline, schedule, etc. description or event metadata entry contains a
  markdown-formatted table, that table is now rendered in Dagit with better spacing between elements.
- The hacker-news example now includes
  [instructions](https://github.com/dagster-io/dagster/tree/master/examples/hacker_news#deploying)
  on how to deploy the repository in a Kubernetes cluster using the Dagster Helm chart.
- [dagster-dbt] The `dbt_cli_resource` now supports the `dbt source snapshot-freshness` command
  (thanks @emilyhawkins-drizly!)
- [helm] Labels are now configurable on user code deployments.

Bugfixes

- Dagit’s dependency on [graphql-ws](https://github.com/graphql-python/graphql-ws) is now pinned
  to < 0.4.0 to avoid a breaking change in its latest release. We expect to remove this dependency
  entirely in a future Dagster release.
- Execution steps downstream of a solid that emits multiple dynamic outputs now correctly
  resolve without error.
- In Dagit, when repositories are loaded asynchronously, pipelines/jobs now appear immediately in
  the left navigation.
- Pipeline/job descriptions with markdown are now rendered correctly in Dagit, and styling is
  improved for markdown-based tables.
- The Dagit favicon now updates correctly during navigation to and from Run pages.
- In Dagit, navigating to assets with keys that contain slashes would sometimes fail due to a lack
  of URL encoding. This has been fixed.
- When viewing the Runs list on a smaller viewport, tooltips on run tags no longer flash.
- Dragging the split panel view in the Solid/Op explorer in Dagit would sometimes leave a broken
  rendered state. This has been fixed.
- Dagstermill notebook previews now works with remote user code deployment.
- [dagster-shell] When a pipeline run fails, subprocesses spawned from dagster-shell utilities
  will now be properly terminated.
- Fixed an issue associated with using `EventMetadata.asset` and `EventMetadata.pipeline_run` in
  `AssetMaterialization` metadata. (Thanks @ymrzkrrs and @drewsonne!)

Breaking Changes

- Dagstermill solids now require a shared-memory io manager, e.g. `fs_io_manager`, which allows
  data to be passed out of the Jupyter process boundary.

Community Contributions

- [helm] Added missing documentation to fields in the Dagster User Deployments subchart
  (thanks @jrouly!)

Documentation

- `objects.inv` is available at http://docs.dagster.io/objects.inv for other projects to link.
- `execute_solid` has been removed from the testing (https://docs.dagster.io/concepts/testing)
  section. Direct invocation is recommended for testing solids.
- The Hacker News demo pipelines no longer include `gcsfs` as a dependency.
- The documentation for `create_databricks_job_solid` now includes an example of how to use it.
- The Airflow integration documentation now all lives at
  https://docs.dagster.io/integrations/airflow, instead of being split across two pages

# 0.12.7

### New

- In Dagit, the repository locations list has been moved from the Instance Status page to the Workspace page. When repository location errors are present, a warning icon will appear next to “Workspace” in the left navigation.
- Calls to `context.log.info()` and other similar functions now fully respect the python logging API. Concretely, log statements of the form `context.log.error(“something %s happened!”, “bad”)` will now work as expected, and you are allowed to add things to the “extra” field to be consumed by downstream loggers: `context.log.info("foo", extra={"some":"metadata"})`.
- Utility functions [`config_from_files`](https://docs.dagster.io/_apidocs/utilities#dagster.config_from_files), [`config_from_pkg_resources`](https://docs.dagster.io/_apidocs/utilities#dagster.config_from_pkg_resources), and [`config_from_yaml_strings`](https://docs.dagster.io/_apidocs/utilities#dagster.config_from_yaml_strings) have been added for constructing run config from yaml files and strings.
- `DockerRunLauncher` can now be configured to launch runs that are connected to more than one network, by configuring the `networks` key.

### Bugfixes

- Fixed an issue with the pipeline and solid Kubernetes configuration tags. `env_from` and `volume_mounts` are now properly applied to the corresponding Kubernetes run worker and job pods.
- Fixed an issue where Dagit sometimes couldn’t start up when using MySQL storage.
- [dagster-mlflow] The `end_mlflow_run_on_pipeline_finished` hook now no longer errors whenever invoked.

### Breaking Changes

- Non-standard keyword arguments to `context.log` calls are now not allowed. `context.log.info("msg", foo="hi")` should be rewritten as `context.log.info("msg", extra={"foo":"hi"})`.
- [dagstermill] When writing output notebook fails, e.g. no file manager provided, it won't yield `AssetMaterialization`. Previously, it would still yield an `AssetMaterialization` where the path is a temp file path that won't exist after the notebook execution.

### Experimental

- Previously, in order to use memoization, it was necessary to provide a resource version for every resource used in a pipeline. Now, resource versions are optional, and memoization can be used without providing them.
- `InputContext` and `OutputContext` now each has an `asset_key` that returns the asset key that was provided to the corresponding `InputDefinition` or `OutputDefinition`.

### Documentation

- The Spark documentation now discusses all the ways of using Dagster with Spark, not just using PySpark

# 0.12.6

### New

- [dagster-dbt] Added a new synchronous RPC dbt resource (`dbt_rpc_sync_resource`), which allows you to programmatically send `dbt` commands to an RPC server, returning only when the command completes (as opposed to returning as soon as the command has been sent).
- Specifying secrets in the `k8s_job_executor` now adds to the secrets specified in `K8sRunLauncher` instead of overwriting them.
- The `local_file_manager` no longer uses the current directory as the default `base_dir` instead defaulting to `LOCAL_ARTIFACT_STORAGE/storage/file_manager`. If you wish, you can configure `LOCAL_ARTIFACT_STORAGE` in your dagster.yaml file.

### Bugfixes

- Following the recent change to add strict Content-Security-Policy directives to Dagit, the CSP began to block the iframe used to render ipynb notebook files. This has been fixed and these iframes should now render correctly.
- Fixed an error where large files would fail to upload when using the `s3_pickle_io_manager` for intermediate storage.
- Fixed an issue where Kubernetes environment variables defined in pipeline tags were not being applied properly to Kubernetes jobs.
- Fixed tick preview in the `Recent` live tick timeline view for Sensors.
- Added more descriptive error messages for invalid sensor evaluation functions.
- `dagit` will now write to a temp directory in the current working directory when launched with the env var `DAGSTER_HOME` not set. This should resolve issues where the event log was not keeping up to date when observing runs progress live in `dagit` with no `DAGSTER_HOME`
- Fixed an issue where retrying from a failed run sometimes failed if the pipeline was changed after the failure.
- Fixed an issue with default config on `to_job` that would result in an error when using an enum config schema within a job.

### Community Contributions

- Documentation typo fix for pipeline example, thanks @clippered!

### Experimental

- Solid and resource versions will now be validated for consistency. Valid characters are `A-Za-z0-9_`.

### Documentation

- The “Testing Solids and Pipelines” section of the tutorial now uses the new direct invocation functionality and tests a solid and pipeline from an earlier section of the tutorial.
- Fixed the example in the API docs for `EventMetadata.python_artifact`.

# 0.12.5

### Bugfixes

- Fixed tick display in the sensor/schedule timeline view in Dagit.
- Changed the `dagster sensor list` and `dagster schedule list` CLI commands to include schedules and sensors that have never been turned on.
- Fixed the backfill progress stats in Dagit which incorrectly capped the number of successful/failed runs.
- Improved query performance in Dagit on pipeline (or job) views, schedule views, and schedules list view by loading partition set data on demand instead of by default.
- Fixed an issue in Dagit where re-executing a pipeline that shares an identical name and graph to a pipeline in another repository could lead to the wrong pipeline being executed.
- Fixed an issue in Dagit where loading a very large DAG in the pipeline overview could sometimes lead to a render loop that repeated the same GraphQL query every few seconds, causing an endless loading state and never rendering the DAG.
- Fixed an issue with `execute_in_process` where providing default executor config to a job would cause config errors.
- Fixed an issue with default config for jobs where using an `ops` config entry in place of `solids` would cause a config error.
- Dynamic outputs are now properly supported while using `adls2_io_manager`
- `ModeDefinition` now validates the keys of `resource_defs` at definition time.
- `Failure` exceptions no longer bypass the `RetryPolicy` if one is set.

### Community Contributions

- Added `serviceAccount.name` to the user deployment Helm subchart and schema, thanks [@jrouly](https://github.com/jrouly)!

### Experimental

- To account for ECS’ eventual consistency model, the `EcsRunLauncher` will now exponentially backoff certain requests for up to a minute while waiting for ECS to reach a consistent state.
- Memoization is now available from all execution entrypoints. This means that a pipeline tagged for use with memoization can be launched from dagit, the `launch` CLI, and other modes of external execution, whereas before, memoization was only available via `execute_pipeline` and the `execute` CLI.
- Memoization now works with root input managers. In order to use a root input manager in a pipeline that utilizes memoization, provide a string value to the `version` argument on the decorator:

```python
from dagster import root_input_manager

@root_input_manager(version="foo")
def my_root_manager(_):
    pass
```

- The `versioned_fs_io_manager` now defaults to using the storage directory of the instance as a base directory.
- `GraphDefinition.to_job` now accepts a tags dictionary with non-string values - which will be serialized to JSON. This makes job tags work similarly to pipeline tags and solid tags.

### Documentation

- The guide for migrating to the experimental graph, job, and op APIs now includes an example of how to migrate a pipeline with a composite solid.

# 0.12.4

### New

- [helm] The compute log manager now defaults to a `NoOpComputeLogManager`. It did not make sense to default to the `LocalComputeLogManager` as pipeline runs are executed in ephemeral jobs, so logs could not be retrieved once these jobs were cleaned up. To have compute logs in a Kubernetes environment, users should configure a compute log manager that uses a cloud provider.
- [helm] The K8sRunLauncher now supports environment variables to be passed in from the current container to the launched Kubernetes job.
- [examples] Added a new `dbt_pipeline` to the [hacker news example repo](https://github.com/dagster-io/dagster/tree/master/examples/hacker_news), which demonstrates how to run a dbt project within a Dagster pipeline.
- Changed the default configuration of steps launched by the `k8s_job_executor` to match the configuration set in the `K8sRunLauncher`.

### Bugfixes

- Fixed an issue where dagster gRPC servers failed to load if they did not have permissions to write to a temporary directory.
- Enabled compression and raised the message receive limit for our gRPC communication. This prevents large pipelines from causing gRPC message limit errors. This limit can now be manually overridden with the `DAGSTER_GRPC_MAX_RX_BYTES` environment variable.
- Fixed errors with `dagster instance migrate` when the asset catalog contains wiped assets.
- Fixed an issue where backfill jobs with the “Re-execute from failures” option enabled were not picking up the solid selection from the originating failed run.
- Previously, when using memoization, if every step was memoized already, you would get an error. Now, the run succeeds and runs no steps.
- [dagster-dbt] If you specify `--models`, `--select`, or `--exclude` flags while configuring the `dbt_cli_resource`, it will no longer attempt to supply these flags to commands that don’t accept them.
- [dagstermill] Fixed an issue where `yield_result` wrote output value to the same file path if output names are the same for different solids.

### Community Contributions

- Added the ability to customize the TTL and backoff limit on Dagster Kubernetes jobs (thanks [@Oliver-Sellwood](https://github.com/Oliver-Sellwood)!)

### Experimental

- `ops` can now be used as a config entry in place of `solids`.
- Fixed a GraphQL bug in ECS deployments by making the `EcsRunLauncher` more resilient to ECS’ eventual consistency model.

### Documentation

- Fixed hyperlink display to be more visible within source code snippets.
- Added documentation for Run Status Sensor on the [Sensors](https://docs.dagster.io/concepts/partitions-schedules-sensors/sensors#run-status-sensors) concept page.

# 0.12.3

### New

- The Dagit web app now has a strict Content Security Policy.
- Introduced a new decorator `[@run_status_sensor](https://docs.dagster.io/_apidocs/schedules-sensors#dagster.run_status_sensor)` which defines sensors that react to given `PipelineRunStatus`.
- You can now specify a `solid` on `build_hook_context`. This allows you to access the `hook_context.solid` parameter.

### Bugfixes

- `dagster`’s dependency on `docstring-parser` has been loosened.
- `@pipeline` now pulls its `description` from the doc string on the decorated function if it is provided.
- The sensor example generated via `dagster new-project` now no longer targets a non-existent mode.

### Community Contributions

- Thanks for the docs typo fix @cvoegele!

### Experimental

- The “jobs” key is now supported when returning a dict from `@repository` functions.
- `GraphDefinition.to_job` now supports the `description` argument.
- Jobs with nested Graph structures no longer fail to load in dagit.
- Previously, the ECS reference deployment granted its tasks the `AmazonECS_FullAccess` policy. Now, the attached roles has been more narrowly scoped to only allow the daemon and dagit tasks to interact with the ECS actions required by the EcsRunLauncher.
- The EcsRunLauncher launches ECS tasks by setting a command override. Previously, if the Task Definition it was using also defined an entrypoint, it would concatenate the entrypoint and the overridden command which would cause launches to fail with `Error: Got unexpected extra arguments`. Now, it ignores the entrypoint and launches succeed.

### Documentation

- Fixed a broken link in the sensor testing overview.

# 0.12.2

### New

- Improved Asset catalog load times in Dagit, for Dagster instances that have fully migrated using `dagster instance migrate`.
- When using the `ScheduleDefinition` constructor to instantiate a schedule definition, if a schedule name is not provided, the name of the schedule will now default to the pipeline name, plus “\_schedule”, instead of raising an error.

### Bugfixes

- Fixed a bug where pipeline definition arguments `description` and `solid_retry_policy` were getting dropped when using a `solid_hook` decorator on a pipeline definition ([#4355](https://github.com/dagster-io/dagster/issues/4355)).
- Fixed an issue where the Dagit frontend wasn’t disabling certain UI elements when launched in read-only mode.
- Fixed a bug where directly invoking an async solid with type annotations would fail, if called from another async function.

### Documentation

- Added a guide to migrating from the existing Pipeline, Mode, Preset, and Solid APIs to the new experimental Graph, Job, and Op APIs. Check out the guide [here](https://legacy-versioned-docs.dagster.dagster-docs.io/0.15.7/guides/dagster/graph_job_op)!

# 0.12.1

### Bugfixes

- Fixes implementation issues in `@pipeline_failure_sensor` that prevented them from working.

# 0.12.0 “Into The Groove”

### Major Changes

- With the new **first-class Pipeline Failure sensors**, you can now write sensors to perform arbitrary actions when pipelines in your repo fail using [`@pipeline_failure_sensor`](https://docs.dagster.io/_apidocs/schedules-sensors#dagster.pipeline_failure_sensor). Out-of-the-box sensors are provided to send emails using [`make_email_on_pipeline_failure_sensor`](https://docs.dagster.io/_apidocs/utilities#dagster.utils.make_email_on_pipeline_failure_sensor) and slack messages using [`make_slack_on_pipeline_failure_sensor`](https://docs.dagster.io/_apidocs/libraries/dagster-slack#dagster_slack.make_slack_on_pipeline_failure_sensor).

  See the [Pipeline Failure Sensor](https://docs.dagster.io/concepts/partitions-schedules-sensors/sensors#pipeline-failure-sensor) docs to learn more.

- New **first-class Asset sensors** help you define sensors that launch pipeline runs or notify appropriate stakeholders when specific asset keys are materialized. This pattern also enables Dagster to infer _cross-pipeline dependency_ links. Check out the docs [here](https://docs.dagster.io/concepts/partitions-schedules-sensors/sensors#asset_sensors)!
- **Solid-level retries**: A new `retry_policy` argument to the `@solid` decorator allows you to easily and flexibly control how specific solids in your pipelines will be retried if they fail by setting a [RetryPolicy](https://docs.dagster.io/_apidocs/solids#dagster.RetryPolicy).
- Writing tests in Dagster is now even easier, using the new suite of **direct invocation apis**. [Solids](*https://docs.dagster.io/concepts/testing#experimental-testing-solids-with-invocation* "https://docs.dagster.io/concepts/testing#experimental-testing-solids-with-invocation"), [resources](*https://docs.dagster.io/concepts/modes-resources#experimental-testing-resource-initialization* "https://docs.dagster.io/concepts/modes-resources#experimental-testing-resource-initialization"), [hooks](https://docs.dagster.io/concepts/solids-pipelines/solid-hooks#experimental-testing-hooks), [loggers](https://docs.dagster.io/concepts/logging/loggers#testing-custom-loggers), [sensors](*https://docs.dagster.io/concepts/partitions-schedules-sensors/sensors#testing-sensors* "https://docs.dagster.io/concepts/partitions-schedules-sensors/sensors#testing-sensors"), and [schedules](https://docs.dagster.io/concepts/partitions-schedules-sensors/schedules#testing-partition-schedules) can all be invoked directly to test their behavior. For example, if you have some solid `my_solid` that you'd like to test on an input, you can now write `assert my_solid(1, "foo") == "bar"` (rather than explicitly calling `execute_solid()`).
- [Experimental] A new set of experimental core APIs. Among many benefits, these changes unify concepts such as Presets and Partition sets, make it easier to reuse common resources within an environment, make it possible to construct test-specific resources outside of your pipeline definition, and more. These changes are significant and impactful, so we encourage you to try them out and let us know how they feel! You can learn more about the specifics [here](https://docs.dagster.io/master/_apidocs/experimental)
- [Experimental] There’s a new [reference deployment for running Dagster on AWS ECS](https://docs.dagster.io/deployment/guides/aws#example "https://docs.dagster.io/deployment/guides/aws#example") and a new [EcsRunLauncher](https://github.com/dagster-io/dagster/blob/0.12.0/python_modules/libraries/dagster-aws/dagster_aws/ecs/launcher.py "https://github.com/dagster-io/dagster/blob/0.11.15/python_modules/libraries/dagster-aws/dagster_aws/ecs/launcher.py") that launches each pipeline run in its own ECS Task.
- [Experimental] There’s a new `k8s_job_executor` (https://docs.dagster.io/_apidocs/libraries/dagster-k8s#dagster_k8s.k8s_job_executor)which executes each solid of your pipeline in a separate Kubernetes job. This addition means that you can now choose at runtime (https://docs.dagster.io/deployment/guides/kubernetes/deploying-with-helm#executor) between single pod and multi-pod isolation for solids in your run. Previously this was only configurable for the entire deployment- you could either use the `K8sRunLauncher` with the default executors (in process and multiprocess) for low isolation, or you could use the `CeleryK8sRunLauncher` with the `celery_k8s_job_executor` for pod-level isolation. Now, your instance can be configured with the `K8sRunLauncher` and you can choose between the default executors or the k8s_job_executor.

### New since 0.11.16

- Using the `@schedule`, `@resource`, or `@sensor` decorator no longer requires a context parameter. If you are not using the context parameter in these, you can now do this:

  ```python
  @schedule(cron_schedule="\* \* \* \* \*", pipeline_name="my_pipeline")
  def my_schedule():
    return {}

  @resource
  def my_resource():
    return "foo"

  @sensor(pipeline_name="my_pipeline")
  def my_sensor():
    return RunRequest(run_config={})
  ```

- Dynamic mapping and collect features are no longer marked “experimental”. `DynamicOutputDefinition` and `DynamicOutput` can now be imported directly from `dagster`.
- Added repository_name property on `SensorEvaluationContext`, which is name of the repository that the sensor belongs to.
- `get_mapping_key` is now available on `SolidExecutionContext` , allowing for discerning which downstream branch of a `DynamicOutput` you are in.
- When viewing a run in Dagit, you can now download its debug file directly from the run view. This can be loaded into dagit-debug.
- [dagster-dbt] A new `dbt_cli_resource` simplifies the process of working with dbt projects in your pipelines, and allows for a wide range of potential uses. Check out the [integration guide](https://docs.dagster.io/integrations/dbt#using-dbt-with-dagster) for examples!

### Bugfixes

- Fixed a bug when retry from failure with fan-in solids didn’t load the right input source correctly. Now the fan-in solids can load the persistent source from corresponding previous runs if retry from failure.
- Fixed a bug in the `k8s_job_executor` that caused solid tag user defined Kubernetes config to not be applied to the Kubernetes jobs.
- Fixed an issue in dagstermill when concurrently running pipelines that contain multiple dagstermill solids with inputs of the same name.

### Breaking Changes

- The deprecated `SystemCronScheduler` and `K8sScheduler` schedulers have been removed. All schedules are now executed using the dagster-daemon proess. See the [deployment docs](https://docs.dagster.io/deployment#hands-on-guides-to-deploying-dagster) for more information about how to use the `dagster-daemon` process to run your schedules.
- If you have written a custom run launcher, the arguments to the `launch_run` function have changed in order to enable faster run launches. `launch_run` now takes in a `LaunchRunContext` object. Additionally, run launchers should now obtain the `PipelinePythonOrigin` to pass as an argument to dagster api `execute_run`. See the implementation of [DockerRunLauncher](https://github.com/dagster-io/dagster/blob/master/python_modules/libraries/dagster-docker/dagster_docker/docker_run_launcher.py) for an example of the new way to write run launchers.
- [helm] `.Values.dagsterDaemon.queuedRunCoordinator` has had its schema altered. It is now referenced at `.Values.dagsterDaemon.runCoordinator.`
  Previously, if you set up your run coordinator configuration in the following manner:

  ```
  dagsterDaemon:
    queuedRunCoordinator:
      enabled: true
      module: dagster.core.run_coordinator
      class: QueuedRunCoordinator
      config:
        max_concurrent_runs: 25
        tag_concurrency_limits: []
        dequeue_interval_seconds: 30
  ```

  It is now configured like:

  ```
  dagsterDaemon:
    runCoordinator:
      enabled: true
      type: QueuedRunCoordinator
      config:
        queuedRunCoordinator:
        maxConcurrentRuns: 25
        tagConcurrencyLimits: []
        dequeueIntervalSeconds: 30
  ```

- The method `events_for_asset_key` on `DagsterInstance` has been deprecated and will now issue a warning. This method was previously used in our asset sensor example code. This can be replaced by calls using the new `DagsterInstance` API `get_event_records`. The example code in our sensor documentation has been updated to use our new APIs as well.

### Community Contributions

- A dagster-mlflow library has been added, thanks @hug0l1ma!
- imagePullSecrets improvements in the user code deployment helm chart, thanks @jrouly (https://github.com/dagster-io/dagster/commits?author=jrouly)!

### Experimental

- You can now configure the EcsRunLauncher to use an existing Task Definition of your choosing. By default, it continues to register its own Task Definition for each run.

# 0.11.16

### New

- In Dagit, a new page has been added for user settings, including feature flags and timezone preferences. It can be accessed via the gear icon in the top right corner of the page.
- SensorExecutionContext and ScheduleExecutionContext have been renamed to SensorEvaluationContext and ScheduleEvaluationContext, respectively. The old names will be supported until 0.12.0.

### Bugfixes

- When turning on a schedule in Dagit, if the schedule had an identical name and identical pipeline name to a schedule in another repository in the workspace, both schedules would incorrectly appear to be turned on, due to a client-side rendering bug. The same bug occurred for sensors. This has now been fixed.
- The “Copy URL” button on a Run view in Dagit was inoperative for users not using Dagit in localhost or https. This has been fixed.
- Fixed a bug in Dagit where Dagit would leak memory for each websocket connection.
- When executing pipeline that contains composite solids, the composite solids mistakenly ignored the upstream outputs. This bug was introduced in 0.11.15, and is now fixed.

### Community Contributions

- Fixed a link to the Kubernetes deployment documentation. Thanks to @jrouly!

### Documentation

- Added documentation for pipeline execution. See [Pipeline Execution](https://docs.dagster.io/concepts/solids-pipelines/pipeline-execution).
- Added practical guide on various ways to to re-execute Dagster pipelines. See [Re-execution in Dagster](https://docs.dagster.io/guides/dagster/re-execution).

# 0.11.15

### New

- The Python GraphQL client now includes a shutdown_repository_location API call that shuts down a gRPC server. This is useful in situations where you want Kubernetes to restart your server and re-create your repository definitions, even though the underlying Python code hasn’t changed (for example, if your pipelines are loaded programatically from a database)
- io_manager_key and root_manager_key is disallowed on composite solids’ InputDefinitions and OutputDefinitions. Instead, custom IO managers on the solids inside composite solids will be respected:

  ```python
  @solid(input_defs=[InputDefinition("data", dagster_type=str, root_manager_key="my_root")])
  def inner_solid(_, data):
    return data

  @composite_solid
  def my_composite():
    return inner_solid()
  ```

- Schedules can now be directly invoked. This is intended to be used for testing. To learn more, see https://docs.dagster.io/master/concepts/partitions-schedules-sensors/schedules#testing-schedules

### Bugfixes

- Dagster libraries (for example, `dagster-postgres` or `dagster-graphql`) are now pinned to the same version as the core `dagster` package. This should reduce instances of issues due to backwards compatibility problems between Dagster packages.
- Due to a recent regression, when viewing a launched run in Dagit, the Gantt chart would inaccurately show the run as queued well after it had already started running. This has been fixed, and the Gantt chart will now accurately reflect incoming logs.
- In some cases, navigation in Dagit led to overfetching a workspace-level GraphQL query that would unexpectedly reload the entire app. The excess fetches are now limited more aggressively, and the loading state will no longer reload the app when workspace data is already available.
- Previously, execution would fail silently when trying to use memoization with a root input manager. The error message now more clearly states that this is not supported.

### Breaking Changes

- Invoking a generator solid now yields a generator, and output objects are not unpacked.

  ```python
  @solid
  def my_solid():
    yield Output("hello")

  assert isinstance(list(my_solid())[0], Output)
  ```

### Experimental

- Added an experimental [`EcsRunLauncher`](https://github.com/dagster-io/dagster/commit/cb07e82a7bf9a46880359fcffd63e17f6da9bae1#diff-9bf38a50da8f0c910296ba4257fb174d34297d6844031476e9c368c07eae6fba). This creates a new ECS Task Definition and launches a new ECS Task for each run. You can use the new [ECS Reference Deployment](https://github.com/dagster-io/dagster/tree/master/examples/deploy_ecs) to experiment with the `EcsRunLauncher`. We’d love your feedback in our [#dagster-ecs](https://dagster.slack.com/archives/C014UDS8LAV) Slack channel!

### Documentation

- Added docs section on testing hooks. https://docs.dagster.io/concepts/ops-jobs-graphs/op-hooks#experimental-testing-hooks

# 0.11.14

### New

- Supplying the "metadata" argument to InputDefinitions and OutputDefinitions is no longer considered experimental.
- The "context" argument can now be omitted for solids that have required resource keys.
- The S3ComputeLogManager now takes a boolean config argument skip_empty_files, which skips uploading empty log files to S3. This should enable a work around of timeout errors when using the S3ComputeLogManager to persist logs to MinIO object storage.
- The Helm subchart for user code deployments now allows for extra manifests.
- Running `dagit` with flag `--suppress-warnings` will now ignore all warnings, such as ExperimentalWarnings.
- PipelineRunStatus, which represents the run status, is now exported in the public API.

### Bugfixes

- The asset catalog now has better backwards compatibility for supporting deprecated Materialization events. Previously, these events were causing loading errors.

### Community Contributions

- Improved documentation of the `dagster-dbt` library with some helpful tips and example code (thanks @makotonium!).
- Fixed the example code in the `dagster-pyspark` documentation for providing and accessing the pyspark resource (thanks @Andrew-Crosby!).
- Helm chart serviceaccounts now allow annotations (thanks @jrouly!).

### Documentation

- Added section on testing resources ([link](https://docs.dagster.io/concepts/resources#experimental-testing-resource-initialization)).
- Revamped IO manager testing section to use `build_input_context` and `build_output_context` APIs ([link](https://docs.dagster.io/concepts/io-management/io-managers#testing-an-io-manager)).

# 0.11.13

### New

- Added an example that demonstrates what a complete repository that takes advantage of many Dagster features might look like. Includes usage of IO Managers, modes / resources, unit tests, several cloud service integrations, and more! Check it out at [`examples/hacker_news`](https://github.com/dagster-io/dagster/tree/master/examples/hacker_news)!
- `retry_number` is now available on `SolidExecutionContext`, allowing you to determine within a solid function how many times the solid has been previously retried.
- Errors that are surfaced during solid execution now have clearer stack traces.
- When using Postgres or MySQL storage, the database mutations that initialize Dagster tables on startup now happen in atomic transactions, rather than individual SQL queries.
- For versions >=0.11.13, when specifying the `--version` flag when installing the Helm chart, the tags for Dagster-provided images in the Helm chart will now default to the current Chart version. For `--version` <0.11.13, the image tags will still need to be updated properly to use old chart version.
- Removed the `PIPELINE_INIT_FAILURE` event type. A failure that occurs during pipeline initialization will now produce a `PIPELINE_FAILURE` as with all other pipeline failures.

### Bugfixes

- When viewing run logs in Dagit, in the stdout/stderr log view, switching the filtered step did not work. This has been fixed. Additionally, the filtered step is now present as a URL query parameter.
- The `get_run_status` method on the Python GraphQL client now returns a `PipelineRunStatus` enum instead of the raw string value in order to align with the mypy type annotation. Thanks to Dylan Bienstock for surfacing this bug!
- When a docstring on a solid doesn’t match the reST, Google, or Numpydoc formats, Dagster no longer raises an error.
- Fixed a bug where memoized runs would sometimes fail to execute when specifying a non-default IO manager key.

### Experimental

- Added the[`k8s_job_executor`](https://docs.dagster.io/master/_apidocs/libraries/dagster-k8s#dagster_k8s.k8s_job_executor), which executes solids in separate kubernetes jobs. With the addition of this executor, you can now choose at runtime between single pod and multi-pod isolation for solids in your run. Previously this was only configurable for the entire deployment - you could either use the K8sRunLauncher with the default executors (in_process and multiprocess) for low isolation, or you could use the CeleryK8sRunLauncher with the celery_k8s_job_executor for pod-level isolation. Now, your instance can be configured with the K8sRunLauncher and you can choose between the default executors or the k8s_job_executor.
- The `DagsterGraphQLClient` now allows you to specify whether to use HTTP or HTTPS when connecting to the GraphQL server. In addition, error messages during query execution or connecting to dagit are now clearer. Thanks to @emily-hawkins for raising this issue!
- Added experimental hook invocation functionality. Invoking a hook will call the underlying decorated function. For example:

```
  from dagster import build_hook_context

  my_hook(build_hook_context(resources={"foo_resource": "foo"}))
```

- Resources can now be directly invoked as functions. Invoking a resource will call the underlying decorated initialization function.

```
  from dagster import build_init_resource_context

  @resource(config_schema=str)
  def my_basic_resource(init_context):
      return init_context.resource_config

  context = build_init_resource_context(config="foo")
  assert my_basic_resource(context) == "foo"
```

- Improved the error message when a pipeline definition is incorrectly invoked as a function.

### Documentation

- Added a section on testing custom loggers: https://docs.dagster.io/master/concepts/logging/loggers#testing-custom-loggers

# 0.11.12

### Bugfixes

- `ScheduleDefinition` and `SensorDefinition` now carry over properties from functions decorated by `@sensor` and `@schedule`. Ie: docstrings.
- Fixed a bug with configured on resources where the version set on a `ResourceDefinition` was not being passed to the `ResourceDefinition` created by the call to `configured`.
- Previously, if an error was raised in an `IOManager` `handle_output` implementation that was a generator, it would not be wrapped `DagsterExecutionHandleOutputError`. Now, it is wrapped.
- Dagit will now gracefully degrade if websockets are not available. Previously launching runs and viewing the event logs would block on a websocket conection.

### Experimental

- Added an example of run attribution via a [custom run coordinator](https://github.com/dagster-io/dagster/tree/master/examples/run_attribution_example), which reads a user’s email from HTTP headers on the Dagster GraphQL server and attaches the email as a run tag. Custom run coordinator are also now specifiable in the Helm chart, under `queuedRunCoordinator`. See the [docs](https://docs.dagster.io/master/guides/dagster/run-attribution) for more information on setup.
- `RetryPolicy` now supports backoff and jitter settings, to allow for modulating the `delay` as a function of attempt number and randomness.

### Documentation

- Added an overview section on testing schedules. Note that the `build_schedule_context` and `validate_run_config` functions are still in an experimental state. https://docs.dagster.io/master/concepts/partitions-schedules-sensors/schedules#testing-schedules
- Added an overview section on testing partition sets. Note that the `validate_run_config` function is still in an experimental state. https://docs.dagster.io/master/concepts/partitions-schedules-sensors/partitions#experimental-testing-a-partition-set

# 0.11.11

### New

- [Helm] Added `dagit.enableReadOnly` . When enabled, a separate Dagit instance is deployed in `—read-only` mode. You can use this feature to serve Dagit to users who you do not want to able to kick off new runs or make other changes to application state.
- [dagstermill] Dagstermill is now compatible with current versions of papermill (2.x). Previously we required papermill to be pinned to 1.x.
- Added a new metadata type that links to the asset catalog, which can be invoked using `EventMetadata.asset`.
- Added a new log event type `LOGS_CAPTURED`, which explicitly links to the captured stdout/stderr logs for a given step, as determined by the configured `ComputeLogManager` on the Dagster instance. Previously, these links were available on the `STEP_START` event.
- The `network` key on `DockerRunLauncher` config can now be sourced from an environment variable.
- The Workspace section of the Status page in Dagit now shows more metadata about your workspace, including the python file, python package, and Docker image of each of your repository locations.
- In Dagit, settings for how executions are viewed now persist across sessions.

### Breaking Changes

- The `get_execution_data` method of `SensorDefinition` and `ScheduleDefinition` has been renamed to `evaluate_tick`. We expect few to no users of the previous name, and are renaming to prepare for improved testing support for schedules and sensors.

### Community Contributions

- README has been updated to remove typos (thanks @gogi2811).
- Configured API doc examples have been fixed (thanks @jrouly).

### Experimental

- Documentation on testing sensors using experimental `build_sensor_context` API. See [Testing sensors](https://docs.dagster.io/concepts/partitions-schedules-sensors/sensors#testing-sensors).

### Bugfixes

- Some mypy errors encountered when using the built-in Dagster types (e.g., `dagster.Int` ) as type annotations on functions decorated with `@solid` have been resolved.
- Fixed an issue where the `K8sRunLauncher` sometimes hanged while launching a run due to holding a stale Kubernetes client.
- Fixed an issue with direct solid invocation where default config values would not be applied.
- Fixed a bug where resource dependencies to io managers were not being initialized during memoization.
- Dagit can once again override pipeline tags that were set on the definition, and UI clarity around the override behavior has been improved.
- Markdown event metadata rendering in dagit has been repaired.

### Documentation

- Added documentation on how to deploy Dagster infrastructure separately from user code. See [Separately Deploying Dagster infrastructure and User Code](https://docs.dagster.io/deployment/guides/kubernetes/customizing-your-deployment#separately-deploying-dagster-infrastructure-and-user-code).

# 0.11.10

### New

- Sensors can now set a string cursor using `context.update_cursor(str_value)` that is persisted across evaluations to save unnecessary computation. This persisted string value is made available on the context as `context.cursor`. Previously, we encouraged cursor-like behavior by exposing `last_run_key` on the sensor context, to keep track of the last time the sensor successfully requested a run. This, however, was not useful for avoiding unnecessary computation when the sensor evaluation did not result in a run request.
- Dagit may now be run in `--read-only` mode, which will disable mutations in the user interface and on the server. You can use this feature to run instances of Dagit that are visible to users who you do not want to able to kick off new runs or make other changes to application state.
- In `dagster-pandas`, the `event_metadata_fn` parameter to the function `create_dagster_pandas_dataframe_type` may now return a dictionary of `EventMetadata` values, keyed by their string labels. This should now be consistent with the parameters accepted by Dagster events, including the `TypeCheck` event.

```py
# old
MyDataFrame = create_dagster_pandas_dataframe_type(
    "MyDataFrame",
    event_metadata_fn=lambda df: [
        EventMetadataEntry.int(len(df), "number of rows"),
        EventMetadataEntry.int(len(df.columns), "number of columns"),
    ]
)

# new
MyDataFrame = create_dagster_pandas_dataframe_type(
    "MyDataFrame",
    event_metadata_fn=lambda df: {
        "number of rows": len(df),
        "number of columns": len(dataframe.columns),
    },
)
```

- dagster-pandas’ `PandasColumn.datetime_column()` now has a new `tz` parameter, allowing you to constrain the column to a specific timezone (thanks `@mrdavidlaing`!)
- The `DagsterGraphQLClient` now takes in an optional `transport` argument, which may be useful in cases where you need to authenticate your GQL requests:

```py
authed_client = DagsterGraphQLClient(
    "my_dagit_url.com",
    transport=RequestsHTTPTransport(..., auth=<some auth>),
)
```

- Added an `ecr_public_resource` to get login credentials for the AWS ECR Public Gallery. This is useful if any of your pipelines need to push images.
- Failed backfills may now be resumed in Dagit, by putting them back into a “requested” state. These backfill jobs should then be picked up by the backfill daemon, which will then attempt to create and submit runs for any of the outstanding requested partitions . This should help backfill jobs recover from any deployment or framework issues that occurred during the backfill prior to all the runs being launched. This will not, however, attempt to re-execute any of the individual pipeline runs that were successfully launched but resulted in a pipeline failure.
- In the run log viewer in Dagit, links to asset materializations now include the timestamp for that materialization. This will bring you directly to the state of that asset at that specific time.
- The Databricks step launcher now includes a `max_completion_wait_time_seconds` configuration option, which controls how long it will wait for a Databricks job to complete before exiting.

### Experimental

- Solids can now be invoked outside of composition. If your solid has a context argument, the `build_solid_context` function can be used to provide a context to the invocation.

```py
from dagster import build_solid_context

@solid
def basic_solid():
    return "foo"

assert basic_solid() == 5

@solid
def add_one(x):
    return x + 1

assert add_one(5) == 6

@solid(required_resource_keys={"foo_resource"})
def solid_reqs_resources(context):
    return context.resources.foo_resource + "bar"

context = build_solid_context(resources={"foo_resource": "foo"})
assert solid_reqs_resources(context) == "foobar"
```

- `build_schedule_context` allows you to build a `ScheduleExecutionContext` using a `DagsterInstance`. This can be used to test schedules.

```py
from dagster import build_schedule_context

with DagsterInstance.get() as instance:
    context = build_schedule_context(instance)
    my_schedule.get_execution_data(context)
```

- `build_sensor_context` allows you to build a `SensorExecutionContext` using a `DagsterInstance`. This can be used to test sensors.

```py

from dagster import build_sensor_context

with DagsterInstance.get() as instance:
    context = build_sensor_context(instance)
    my_sensor.get_execution_data(context)
```

- `build_input_context` and `build_output_context` allow you to construct `InputContext` and `OutputContext` respectively. This can be used to test IO managers.

```py
from dagster import build_input_context, build_output_context

io_manager = MyIoManager()

io_manager.load_input(build_input_context())
io_manager.handle_output(build_output_context(), val)
```

- Resources can be provided to either of these functions. If you are using context manager resources, then `build_input_context`/`build_output_context` must be used as a context manager.

```py
with build_input_context(resources={"cm_resource": my_cm_resource}) as context:
    io_manager.load_input(context)
```

- `validate_run_config` can be used to validate a run config blob against a pipeline definition & mode. If the run config is invalid for the pipeline and mode, this function will throw an error, and if correct, this function will return a dictionary representing the validated run config that Dagster uses during execution.

```py
validate_run_config(
    {"solids": {"a": {"config": {"foo": "bar"}}}},
    pipeline_contains_a
) # usage for pipeline that requires config

validate_run_config(
    pipeline_no_required_config
) # usage for pipeline that has no required config
```

- The ability to set a `RetryPolicy` has been added. This allows you to declare automatic retry behavior when exceptions occur during solid execution. You can set `retry_policy` on a solid invocation, `@solid` definition, or `@pipeline` definition.

```py
@solid(retry_policy=RetryPolicy(max_retries=3, delay=5))
def fickle_solid(): # ...

@pipeline( # set a default policy for all solids
solid_retry_policy=RetryPolicy()
)
def my_pipeline(): # will use the pipelines policy by default
    some_solid()

    # solid definition takes precedence over pipeline default
    fickle_solid()

    # invocation setting takes precedence over definition
    fickle_solid.with_retry_policy(RetryPolicy(max_retries=2))
```

### Bugfixes

- Previously, asset materializations were not working in dagster-dbt for dbt >= 0.19.0. This has been fixed.
- Previously, using the `dagster/priority` tag directly on pipeline definitions would cause an error. This has been fixed.
- In dagster-pandas, the `create_dagster_pandas_dataframe_type()` function would, in some scenarios, not use the specified `materializer` argument when provided. This has been fixed (thanks `@drewsonne`!)
- `dagster-graphql --remote` now sends the query and variables as post body data, avoiding uri length limit issues.
- In the Dagit pipeline definition view, we no longer render config nubs for solids that do not need them.
- In the run log viewer in Dagit, truncated row contents (including errors with long stack traces) now have a larger and clearer button to expand the full content in a dialog.
- [dagster-mysql] Fixed a bug where database connections accumulated by `sqlalchemy.Engine` objects would be invalidated after 8 hours of idle time due to MySQL’s default configuration, resulting in an `sqlalchemy.exc.OperationalError` when attempting to view pages in Dagit in long-running deployments.

### Documentation

- In 0.11.9, context was made an optional argument on the function decorated by @solid. The solids throughout tutorials and snippets that do not need a context argument have been altered to omit that argument, and better reflect this change.
- In a previous docs revision, a tutorial section on accessing resources within solids was removed. This has been re-added to the site.

# 0.11.9

### New

- In Dagit, assets can now be viewed with an `asOf` URL parameter, which shows a snapshot of the asset at the provided timestamp, including parent materializations as of that time.
- [Dagit] Queries and Mutations now use HTTP instead of a websocket-based connection.

### Bugfixes

- A regression in 0.11.8 where composites would fail to render in the right side bar in Dagit has been fixed.
- A dependency conflict in `make dev_install` has been fixed.
- [dagster-python-client] `reload_repository_location` and `submit_pipeline_execution` have been fixed - the underlying GraphQL queries had a missing inline fragment case.

### Community Contributions

- AWS S3 resources now support named profiles (thanks @deveshi!)
- The Dagit ingress path is now configurable in our Helm charts (thanks @orf!)
- Dagstermill’s use of temporary files is now supported across operating systems (thanks @slamer59!)
- Deploying with Helm documentation has been updated to reflect the correct name for “dagster-user-deployments” (thanks @hebo-yang!)
- Deploying with Helm documentation has been updated to suggest naming your release “dagster” (thanks @orf!)
- Solids documentation has been updated to remove a typo (thanks @dwallace0723!)
- Schedules documentation has been updated to remove a typo (thanks @gdoron!)

# 0.11.8

### New

- The `@solid` decorator can now wrap a function without a `context` argument, if no context information is required. For example, you can now do:

```py
@solid
def basic_solid():
    return 5

@solid
def solid_with_inputs(x, y):
    return x + y

```

however, if your solid requires config or resources, then you will receive an error at definition time.

- It is now simpler to provide structured metadata on events. Events that take a `metadata_entries` argument may now instead accept a `metadata` argument, which should allow for a more convenient API. The `metadata` argument takes a dictionary with string labels as keys and `EventMetadata` values. Some base types (`str`, `int`, `float`, and JSON-serializable `list`/`dict`s) are also accepted as values and will be automatically coerced to the appropriate `EventMetadata` value. For example:

```py
@solid
def old_metadata_entries_solid(df):
   yield AssetMaterialization(
       "my_asset",
       metadata_entries=[
           EventMetadataEntry.text("users_table", "table name"),
           EventMetadataEntry.int(len(df), "row count"),
           EventMetadataEntry.url("http://mysite/users_table", "data url")
       ]
   )

@solid
def new_metadata_solid(df):
    yield AssetMaterialization(
       "my_asset",
       metadata={
           "table name": "users_table",
           "row count": len(df),
           "data url": EventMetadata.url("http://mysite/users_table")
       }
   )

```

- The dagster-daemon process now has a `--heartbeat-tolerance` argument that allows you to configure how long the process can run before shutting itself down due to a hanging thread. This parameter can be used to troubleshoot failures with the daemon process.
- When creating a schedule from a partition set using `PartitionSetDefinition.create_schedule_definition`, the `partition_selector` function that determines which partition to use for a given schedule tick can now return a list of partitions or a single partition, allowing you to create schedules that create multiple runs for each schedule tick.

### Bugfixes

- Runs submitted via backfills can now correctly resolve the source run id when loading inputs from previous runs instead of encountering an unexpected `KeyError`.
- Using nested `Dict` and `Set` types for solid inputs/outputs now works as expected. Previously a structure like `Dict[str, Dict[str, Dict[str, SomeClass]]]` could result in confusing errors.
- Dagstermill now correctly loads the config for aliased solids instead of loading from the incorrect place which would result in empty `solid_config`.
- Error messages when incomplete run config is supplied are now more accurate and precise.
- An issue that would cause `map` and `collect` steps downstream of other `map` and `collect` steps to mysteriously not execute when using multiprocess executors has been resolved.

### Documentation

- Typo fixes and improvements (thanks @elsenorbw (https://github.com/dagster-io/dagster/commits?author=elsenorbw) !)
- Improved documentation for scheduling partitions

# 0.11.7

### New

- For pipelines with tags defined in code, display these tags in the Dagit playground.
- On the Dagit asset list page, use a polling query to regularly refresh the asset list.
- When viewing the Dagit asset list, persist the user’s preference between the flattened list view and the directory structure view.
- Added `solid_exception` on `HookContext` which returns the actual exception object thrown in a failed solid. See the example “[Accessing failure information in a failure hook](https://docs.dagster.io/concepts/solids-pipelines/solid-hooks#accessing-failure-information-in-a-failure-hook)“ for more details.
- Added `solid_output_values` on `HookContext` which returns the computed output values.
- Added `make_values_resource` helper for defining a resource that passes in user-defined values. This is useful when you want multiple solids to share values. See the [example](https://docs.dagster.io/concepts/configuration/config-schema#passing-configuration-to-multiple-solids-in-a-pipeline) for more details.
- StartupProbes can now be set to disabled in Helm charts. This is useful if you’re running on a version earlier than Kubernetes 1.16.

### Bugfixes

- Fixed an issue where partial re-execution was not referencing the right source run and failed to load the correct persisted outputs.
- When running Dagit with `--path-prefix`, our color-coded favicons denoting the success or failure of a run were not loading properly. This has been fixed.
- Hooks and tags defined on solid invocations now work correctly when executing a pipeline with a solid subselection
- Fixed an issue where heartbeats from the dagster-daemon process would not appear on the Status page in dagit until the process had been running for 30 seconds
- When filtering runs, Dagit now suggests all “status:” values and other auto-completions in a scrolling list
- Fixed asset catalog where nested directory structure links flipped back to the flat view structure

### Community Contributions

- [Helm] The Dagit service port is now configurable (thanks @trevenrawr!)
- [Docs] Cleanup & updating visual aids (thanks @keypointt!)

### Experimental

- [Dagster-GraphQL] Added an official Python Client for Dagster’s GraphQL API ([GH issue #2674](https://github.com/dagster-io/dagster/issues/2674)). Docs can be found [here](https://docs.dagster.io/concepts/dagit/graphql-client)

### Documentation

- Fixed a confusingly-worded header on the Solids/Pipelines Testing page

# 0.11.6

### Breaking Changes

- `DagsterInstance.get()` no longer falls back to an ephemeral instance if `DAGSTER_HOME` is not set. We don’t expect this to break normal workflows. This change allows our tooling to be more consistent around it’s expectations. If you were relying on getting an ephemeral instance you can use `DagsterInstance.ephemeral()` directly.
- Undocumented attributes on `HookContext` have been removed. `step_key` and `mode_def` have been documented as attributes.

### New

- Added a permanent, linkable panel in the Run view in Dagit to display the raw compute logs.
- Added more descriptive / actionable error messages throughout the config system.
- When viewing a partitioned asset in Dagit, display only the most recent materialization for a partition, with a link to view previous materializations in a dialog.
- When viewing a run in Dagit, individual log line timestamps now have permalinks. When loading a timestamp permalink, the log table will highlight and scroll directly to that line.
- The default `config_schema` for all configurable objects - solids, resources, IO managers, composite solids, executors, loggers - is now `Any`. This means that you can now use configuration without explicitly providing a `config_schema`. Refer to the docs for more details: https://docs.dagster.io/concepts/configuration/config-schema.
- When launching an out of process run, resources are no longer initialized in the orchestrating process. This should give a performance boost for those using out of process execution with heavy resources (ie, spark context).
- `input_defs` and `output_defs` on `@solid` will now flexibly combine data that can be inferred from the function signature that is not declared explicitly via `InputDefinition` / `OutputDefinition`. This allows for more concise defining of solids with reduced repetition of information.
- [Helm] Postgres storage configuration now supports connection string parameter keywords.
- The Status page in Dagit will now display errors that were surfaced in the `dagster-daemon` process within the last 5 minutes. Previously, it would only display errors from the last 30 seconds.
- Hanging sensors and schedule functions will now raise a timeout exception after 60 seconds, instead of crashing the `dagster-daemon` process.
- The `DockerRunLauncher` now accepts a `container_kwargs` config parameter, allowing you to specify any argument to the run container that can be passed into the Docker containers.run method. See https://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.run for the full list of available options.
- Added clearer error messages for when a Partition cannot be found in a Partition Set.
- The `celery_k8s_job_executor` now accepts a `job_wait_timeout` allowing you to override the default of 24 hours.

### Bugfixes

- Fixed the raw compute logs in Dagit, which were not live updating as the selected step was executing.
- Fixed broken links in the Backfill table in Dagit when Dagit is started with a `--prefix-path` argument.
- Showed failed status of backfills in the Backfill table in Dagit, along with an error stack trace. Previously, the backfill jobs were stuck in a `Requested` state.
- Previously, if you passed a non-required Field to the `output_config_schema` or `input_config_schema` arguments of `@io_manager`, the config would still be required. Now, the config is not required.
- Fixed nested subdirectory views in the `Assets` catalog, where the view switcher would flip back from the directory view to the flat view when navigating into subdirectories.
- Fixed an issue where the `dagster-daemon` process would crash if it experienced a transient connection error while connecting to the Dagster database.
- Fixed an issue where the `dagster-airflow scaffold` command would raise an exception if a preset was specified.
- Fixed an issue where Dagit was not including the error stack trace in the Status page when a repository failed to load.

# 0.11.5

### New

- Resources in a `ModeDefinition` that are not required by a pipeline no longer require runtime configuration. This should make it easier to share modes or resources among multiple pipelines.
- Dagstermill solids now support retries when a `RetryRequested` is yielded from a notebook using `dagstermill.yield_event`.
- In Dagit, the asset catalog now supports both a flattened view of all assets as well as a hierarchical directory view.
- In Dagit, the asset catalog now supports bulk wiping of assets.

### Bugfixes

- In the Dagit left nav, schedules and sensors accurately reflect the filtered repositories.
- When executing a pipeline with a subset of solids, the config for solids not included in the subset is correctly made optional in more cases.
- URLs were sometimes not prefixed correctly when running Dagit using the `--path-prefix` option, leading to failed GraphQL requests and broken pages. This bug was introduced in 0.11.4, and is now fixed.
- The `update_timestamp` column in the runs table is now updated with a UTC timezone, making it consistent with the `create_timestamp` column.
- In Dagit, the main content pane now renders correctly on ultra-wide displays.
- The partition run matrix on the pipeline partition tab now shows step results for composite solids and dynamically mapped solids. Previously, the step status was not shown at all for these solids.
- Removed dependency constraint of `dagster-pandas` on `pandas`. You can now include any version of pandas. (https://github.com/dagster-io/dagster/issues/3350)
- Removed dependency on `requests` in `dagster`. Now only `dagit` depends on `requests.`
- Removed dependency on `pyrsistent` in `dagster`.

### Documentation

- Updated the “Deploying to Airflow” documentation to reflect the current state of the system.

# 0.11.4

### Community Contributions

- Fix typo in `--config` help message (thanks [@pawelad](https://github.com/pawelad) !)

### Breaking Changes

- Previously, when retrieving the outputs from a run of `execute_pipeline`, the system would use the io manager that handled each output to perform the retrieval. Now, when using `execute_pipeline` with the default in-process executor, the system directly captures the outputs of solids for use with the result object returned by `execute_pipeline`. This may lead to slightly different behavior when retrieving outputs if switching between executors and using custom IO managers.

### New

- The `K8sRunLauncher` and `CeleryK8sRunLauncher` now add a `dagster/image` tag to pipeline runs to document the image used. The `DockerRunLauncher` has also been modified to use this tag (previously it used `docker/image`).
- In Dagit, the left navigation is now collapsible on smaller viewports. You can use the `.` key shortcut to toggle visibility.
- `@solid` can now decorate async def functions.

### Bugfixes

- In Dagit, a GraphQL error on partition sets related to missing fragment `PartitionGraphFragment` has been fixed.
- The compute log manager now handles base directories containing spaces in the path.
- Fixed a bug where re-execution was not working if the initial execution failed, and execution was delegated to other machines/process (e.g. using the multiprocess executor)
- The same solid can now collect over multiple dynamic outputs

# 0.11.3

### Breaking Changes

- Schedules and sensors that target a `pipeline_name` that is not present in the current repository will now error out when the repository is created.

### New

- Assets are now included in Dagit global search. The search bar has also been moved to the top of the app.
- [helm] `generatePostgresqlPasswordSecret` toggle was added to allow the Helm chart to reference an external secret containing the Postgresql password (thanks @PenguinToast !)
- [helm] The Dagster Helm chart is now hosted on [Artifact Hub](https://artifacthub.io/packages/search?page=1&org=dagster).
- [helm] The workspace can now be specified under `dagit.workspace`, which can be useful if you are managing your user deployments in a separate Helm release.

### Bugfixes

- In Dagit, toggling schedules and sensors on or off will now immediately update the green dot in the left navigation, without requiring a refresh.
- When evaluating `dict` values in `run_config` targeting `Permissive` / `dict` config schemas, the ordering is now preserved.
- Integer values for `EventMetadataEntry.int` greater than 32 bits no longer cause `dagit` errors.
- `PresetDefinition.with_additional_config` no longer errors if the base config was empty (thanks @esztermarton !)
- Fixed limitation on gRPC message size when evaluating run requests for sensors, schedules, and backfills. Previously, a gRPC error would be thrown with status code `StatusCode.RESOURCE_EXHAUSTED` for a large number of run requests, especially when the requested run configs were large.
- Changed backfill job status to reflect the number of successful runs against the number of partitions requested instead of the number of runs requested. Normally these two numbers are the same, but they can differ if a pipeline run initiated by the backfill job is re-executed manually.

### Documentation

- Corrections from the community - thanks @mrdavidlaing & @a-cid !

# 0.11.2

**Community Contributions**

- `dagster new project` now scaffolds `setup.py` using your local `dagster` pip version (thanks @taljaards!)
- Fixed an issue where legacy examples were not ported over to the new documentation site (thanks @keypointt!)

**New**

- If a solid-decorated function has a docstring, and no `description` is provided to the solid decorator, the docstring will now be used as the solid’s description.

**Bugfixes**

- In 0.11.0, we introduced the ability to auto-generate Dagster Types from PEP 484 type annotations on solid arguments and return values. However, when clicked on in Dagit, these types would show “Type Not Found” instead of rendering a description. This has been fixed.
- Fixed an issue where the `dagster api execute_step` will mistakenly skip a step and output a non-DagsterEvent log. This affected the `celery_k8s_job_executor`.
- Fixed an issue where NaN floats were not properly handled by Dagit metadata entries.
- Fixed an issue where Dagit run tags were unclickable.
- Fixed an issue where backfills from failures were not able to be scheduled from Dagit.

**Integrations**

- [Helm] A global service account name can now be specified, which will result in the same service account name to be referenced across all parts of the Dagster Kubernetes deployment.
- [Helm] Fixed an issue where user deployments did not update, even if their dependent config maps had changed.

# 0.11.1

**Community Contributions**

- Fixed `dagster new-project`, which broke on the 0.11.0 release (Thank you @saulius!)
- Docs fixes (Thanks @michaellynton and @zuik!)

**New**

- The left navigation in Dagit now allows viewing more than one repository at a time. Click “Filter” to choose which repositories to show.
- In dagster-celery-k8s, you can now specify a custom container image to use for execution in executor config. This image will take precedence over the image used for the user code deployment.

**Bugfixes**

- Previously, fonts were not served correctly in Dagit when using the `--path-prefix option`. Custom fonts and their CSS have now been removed, and system fonts are now used for both normal and monospace text.
- In Dagit, table borders are now visible in Safari.
- Stopping and starting a sensor was preventing future sensor evaluations due to a timezone issue when calculating the minimum interval from the last tick timestamp. This is now fixed.
- The blank state for the backfill table is now updated to accurately describe the empty state.
- Asset catalog entries were returning an error if they had not been recently materialized since (since 0.11.0). Our asset queries are now backwards compatible to read from old materializations.
- Backfills can now successfully be created with step selections even for partitions that did not have an existing run.
- Backfill progress were sometimes showing negative counts for the “Skipped” category, when backfill runs were manually re-executed. This has now been amended to adjust the total run counts to include manually re-executed runs.

# 0.11.0

### Major Changes

- **MySQL is now supported as a backend for storages** you can now run your Dagster Instance on top of MySQL instead of Postgres. See the docs for how to configure MySQL for [Event Log Storage](https://docs.dagster.io/deployment/dagster-instance#mysqleventlogstorage), [Run Storage](https://docs.dagster.io/deployment/dagster-instance#mysqlrunstorage), and [Schedule Storage](https://docs.dagster.io/deployment/dagster-instance#mysqlschedulestorage).
- A new **backfills page** in Dagit lets you monitor and cancel currently running backfills. Backfills are now managed by the Dagster Daemon, which means you can launch backfills over thousands of partitions without risking crashing your Dagit server.
- [Experimental] Dagster now helps you track the **lineage of assets**. You can attach `AssetKeys` to solid outputs through either the `OutputDefinition` or `IOManager`, which allows Dagster to automatically generate asset lineage information for assets referenced in this way. Direct parents of an asset will appear in the Dagit Asset Catalog. See the [asset docs](https://docs.dagster.io/concepts/assets/asset-materializations) to learn more.
- [Experimental] A **collect operation for dynamic orchestration** allows you to run solids that take a set of dynamically mapped outputs as an input. Building on the dynamic orchestration features of `DynamicOutput` and `map` from the last release, this release includes the ability to `collect` over dynamically mapped outputs. You can see an example [here](http://docs.dagster.io/concepts/solids-pipelines/pipelines#dynamic-mapping%E2%80%94collect).
- Dagster has a new **documentation site**. The URL is still [https://docs.dagster.io](https://docs.dagster.io/), but the site has a new design and updated content. If you’re on an older version of Dagster, you can still view pre-0.11.0 documentation at [https://legacy-docs.dagster.io](https://legacy-docs.dagster.io/).
- **dagster new-project** is a new CLI command that generates a Dagster project with skeleton code on your filesystem. [Learn how to use it here.](https://docs.dagster.io/getting-started/create-new-project)

### Additions

#### Core

- Sensors and Schedules
  - Added a `partition_days_offset` argument to the `@daily_schedule` decorator that allows you to customize which partition is used for each execution of your schedule. The default value of this parameter is `1`, which means that a schedule that runs on day N will fill in the partition for day N-1. To create a schedule that uses the partition for the current day, set this parameter to `0`, or increase it to make the schedule use an earlier day’s partition. Similar arguments have also been added for the other partitioned schedule decorators (`@monthly_schedule`, `@weekly_schedule`, and `@hourly_schedule`).ar
  - Both sensors and schedule definitions support a `description` parameter that takes in a human-readable string description and displays it on the corresponding landing page in Dagit.
- Assets
  - [Experimental] `AssetMaterialization` now accepts a `tags` argument. Tags can be used to filter assets in Dagit.
  - Added support for assets to the default SQLite event log storage.
- Daemon
  - The `QueuedRunCoordinator` daemon is now more resilient to errors while dequeuing runs. Previously runs which could not launch would block the queue. They will now be marked as failed and removed from the queue.
  - The `dagster-daemon` process uses fewer resources and spins up fewer subprocesses to load pipeline information. Previously, the scheduler, sensor, and run queue daemon each spun up their own process for this–now they share a single process.
  - The `dagster-daemon` process now runs each of its daemons in its own thread. This allows the scheduler, sensor loop, and daemon for launching queued runs to run in parallel, without slowing each other down.
- Deployment
  - When specifying the location of a gRPC server in your `workspace.yaml` file to load your pipelines, you can now specify an environment variable for the server’s hostname and port.
  - When deploying your own gRPC server for your pipelines, you can now specify that connecting to that server should use a secure SSL connection.
- When a solid-decorated function has a Python type annotation and no Dagster type has been explicitly registered for that Python type, Dagster now automatically constructs a corresponding Dagster type instead of raising an error.
- Added a `dagster run delete` CLI command to delete a run and its associated event log entries.
- `fs_io_manager` now defaults the base directory to `base_dir` via the Dagster instance’s `local_artifact_storage` configuration. Previously, it defaulted to the directory where the pipeline was executed.
- When user code raises an error inside `handle_output`, `load_input`, or a type check function, the log output now includes context about which input or output the error occurred during.
- We have added the `BoolSource` config type (similar to the `StringSource` type). The config value for this type can be a boolean literal or a pointer to an environment variable that is set to a boolean value.
- When trying to run a pipeline where every step has been memoized, you now get a `DagsterNoStepsToExecuteException`.
- The `OutputContext` passed to the `has_output` method of `MemoizableIOManager` now includes a working `log`.

#### Dagit

- After manually reloading the current repository, users will now be prompted to regenerate preset-based or partition-set-based run configs in the Playground view. This helps ensure that the generated run config is up to date when launching new runs. The prompt does not occur when the repository is automatically reloaded.
- Added ability to preview runs for upcoming schedule ticks.
- Dagit now has a global search feature in the left navigation, allowing you to jump quickly to pipelines, schedules, sensors, and partition sets across your workspace. You can trigger search by clicking the search input or with the / keyboard shortcut.
- Timestamps in Dagit have been updated to be more consistent throughout the app, and are now localized based on your browser’s settings.
- In Dagit, a repository location reload button is now available in the header of every pipeline, schedule, and sensor page.
- You can now makes changes to your `workspace.yaml` file without restarting Dagit. To reload your workspace, navigate to the Status page and press the “Reload all” button in the Workspace section.
- When viewing a run in Dagit, log filtering behavior has been improved. `step` and `type` filtering now offers fuzzy search, all log event types are now searchable, and visual bugs within the input have been repaired. Additionally, the default setting for “Hide non-matches” has been flipped to `true`.
- When using a `grpc_server` repository location, Dagit will automatically detect changes and prompt you to reload when the remote server updates.
- When launching a backfill from Dagit, the “Re-execute From Last Run” option has been removed, because it had confusing semantics. “Re-execute From Failure” now includes a tooltip.
- Added a secondary index to improve performance when querying run status.
- The asset catalog now displays a flattened view of all assets, along with a filter field. Tags from AssetMaterializations can be used to filter the catalog view.
- The asset catalog now enables wiping an individual assets from an action in the menu. Bulk wipes of assets is still only supported with the CLI command `dagster asset wipe`.

#### Integrations

- [dagster-snowflake] `snowflake_resource` can now be configured to use the SQLAlchemy connector (thanks @basilvetas!)
- [dagster-pagerduty / dagster-slack] Added built-in hook integrations to create Pagerduty/Slack alerts when solids fail.
- [dagstermill] Users can now specify custom tags & descriptions for notebook solids.
- [dagster-dbt] The dbt commands `seed` and `docs generate` are now available as solids in the library `dagster-dbt`. (thanks [@dehume-drizly](https://github.com/dehume-drizly)!)
- [dagster-spark] - The `dagster-spark` config schemas now support loading values for all fields via environment variables.
- [dagster-gcp] The `gcs_pickle_io_manager` now also retries on 403 Forbidden errors, which previously would only retry on 429 TooManyRequests.

#### Kubernetes/Helm

- Users can set Kubernetes labels on Celery worker deployments
- Users can set environment variables for Flower deployment
- The Redis helm chart is now included as an optional dagster helm chart dependency
- `K8sRunLauncher` and `CeleryK8sRunLauncher` no longer reload the pipeline being executed just before launching it. The previous behavior ensured that the latest version of the pipeline was always being used, but was inconsistent with other run launchers. Instead, to ensure that you’re running the latest version of your pipeline, you can refresh your repository in Dagit by pressing the button next to the repository name.
- Added a flag to the Dagster helm chart that lets you specify that the cluster already has a redis server available, so the Helm chart does not need to create one in order to use redis as a messaging queue. For more information, see the Helm chart’s values.yaml file.
- Celery queues can now be configured with different node selectors. Previously, configuring a node selector applied it to all Celery queues.
- When setting `userDeployments.deployments` in the Helm chart, `replicaCount` now defaults to 1 if not specified.
- Changed our weekly docker image releases (the default images in the helm chart). `dagster/dagster-k8s` and `dagster/dagster-celery-k8s` can be used for all processes which don't require user code (Dagit, Daemon, and Celery workers when using the CeleryK8sExecutor). `user-code-example` can be used for a sample user repository. The prior images (`k8s-dagit`, `k8s-celery-worker`, `k8s-example`) are deprecated.
- All images used in our Helm chart are now fully qualified, including a registry name. If you are encountering rate limits when attempting to pull images from DockerHub, you can now edit the Helm chart to pull from a registry of your choice.
- We now officially use Helm 3 to manage our Dagster Helm chart.
- We are now publishing the `dagster-k8s`, `dagster-celery-k8s`, `user-code-example`, and `k8s-dagit-example` images to a public ECR registry in addition to DockerHub. If you are encountering rate limits when attempting to pull images from DockerHub, you should now be able to pull these images from public.ecr.aws/dagster.
- `.Values.dagsterHome` is now a global variable, available at `.Values.global.dagsterHome`.
- `.Values.global.postgresqlSecretName` has been introduced, for subcharts to access the Dagster Helm chart’s generated Postgres secret properly.
- `.Values.userDeployments` has been renamed `.Values.dagster-user-deployments` to reference the subchart’s values. When using Dagster User Deployments, enabling `.Values.dagster-user-deployments.enabled` will create a `workspace.yaml` for Dagit to locate gRPC servers with user code. To create the actual gRPC servers, `.Values.dagster-user-deployments.enableSubchart` should be enabled. To manage the gRPC servers in a separate Helm release, `.Values.dagster-user-deployments.enableSubchart` should be disabled, and the subchart should be deployed in its own helm release.

### Breaking changes

- Schedules now run in UTC (instead of the system timezone) if no timezone has been set on the schedule. If you’re using a deprecated scheduler like `SystemCronScheduler` or `K8sScheduler`, we recommend that you switch to the native Dagster scheduler. The deprecated schedulers will be removed in the next Dagster release.
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

#### Removal of deprecated APIs

- The `instance` argument to `RunLauncher.launch_run` has been removed. If you have written a custom RunLauncher, you’ll need to update the signature of that method. You can still access the `DagsterInstance` on the `RunLauncher` via the `_instance` parameter.
- The `has_config_entry`, `has_configurable_inputs`, and `has_configurable_outputs` properties of `solid` and `composite_solid` have been removed.
- The deprecated optionality of the `name` argument to `PipelineDefinition` has been removed, and the argument is now required.
- The `execute_run_with_structured_logs` and `execute_step_with_structured_logs` internal CLI entry points have been removed. Use `execute_run` or `execute_step` instead.
- The `python_environment` key has been removed from `workspace.yaml`. Instead, to specify that a repository location should use a custom python environment, set the `executable_path` key within a `python_file`, `python_module`, or `python_package` key. See [the docs](https://docs.dagster.io/concepts/code-locations/workspaces) for more information on configuring your `workspace.yaml` file.
- [dagster-dask] The deprecated schema for reading or materializing dataframes has been removed. Use the `read` or `to` keys accordingly.

# 0.10.9

**Bugfixes**

- Fixed an issue where postgres databases were unable to initialize the Dagster schema or migrate to a newer version of the Dagster schema. (Thanks [@wingyplus](https://github.com/wingyplus) for submitting the fix!)

# 0.10.8

**Community Contributions**

- [dagster-dbt] The dbt commands `seed` and `docs generate` are now available as solids in the
  library `dagster-dbt`. (thanks [@dehume-drizly](https://github.com/dehume-drizly)!)

**New**

- Dagit now has a global search feature in the left navigation, allowing you to jump quickly to
  pipelines, schedules, and sensors across your workspace. You can trigger search by clicking the
  search input or with the / keyboard shortcut.
- Timestamps in Dagit have been updated to be more consistent throughout the app, and are now
  localized based on your browser’s settings.
- Adding `SQLPollingEventWatcher` for alternatives to filesystem or DB-specific listen/notify
  functionality
- We have added the `BoolSource` config type (similar to the `StringSource` type). The config value for
  this type can be a boolean literal or a pointer to an environment variable that is set to a boolean
  value.
- The `QueuedRunCoordinator` daemon is now more resilient to errors while dequeuing runs. Previously
  runs which could not launch would block the queue. They will now be marked as failed and removed
  from the queue.
- When deploying your own gRPC server for your pipelines, you can now specify that connecting to that
  server should use a secure SSL connection. For example, the following `workspace.yaml` file specifies
  that a secure connection should be used:

  ```yaml
  load_from:
    - grpc_server:
        host: localhost
        port: 4266
        location_name: "my_grpc_server"
        ssl: true
  ```

- The `dagster-daemon` process uses fewer resources and spins up fewer subprocesses to load pipeline
  information. Previously, the scheduler, sensor, and run queue daemon each spun up their own process
  for this–now they share a single process.

**Integrations**

- [Helm] - All images used in our Helm chart are now fully qualified, including a registry name.
  If you are encountering rate limits when attempting to pull images from DockerHub, you can now
  edit the Helm chart to pull from a registry of your choice.
- [Helm] - We now officially use Helm 3 to manage our Dagster Helm chart.
- [ECR] - We are now publishing the `dagster-k8s`, `dagster-celery-k8s`, `user-code-example`, and
  `k8s-dagit-example` images to a public ECR registry in addition to DockerHub. If you are
  encountering rate limits when attempting to pull images from DockerHub, you should now be able to
  pull these images from public.ecr.aws/dagster.
- [dagster-spark] - The `dagster-spark` config schemas now support loading values for all fields via
  environment variables.

**Bugfixes**

- Fixed a bug in the helm chart that would cause a Redis Kubernetes pod to be created even when an
  external Redis is configured. Now, the Redis Kubernetes pod is only created when `redis.internal`
  is set to `True` in helm chart.
- Fixed an issue where the `dagster-daemon` process sometimes left dangling subprocesses running
  during sensor execution, causing excess resource usage.
- Fixed an issue where Dagster sometimes left hanging threads running after pipeline execution.
- Fixed an issue where the sensor daemon would mistakenly mark itself as in an unhealthy state even
  after recovering from an error.
- Tags applied to solid invocations using the `tag` method on solid invocations (as opposed to solid
  definitions) are now correctly propagated during execution. They were previously being ignored.

**Experimental**

- MySQL (via dagster-mysql) is now supported as a backend for event log, run, & schedule storages.
  Add the following to your dagster.yaml to use MySQL for storage:

  ```yaml
  run_storage:
    module: dagster_mysql.run_storage
    class: MySQLRunStorage
    config:
      mysql_db:
        username: { username }
        password: { password }
        hostname: { hostname }
        db_name: { database }
        port: { port }

  event_log_storage:
    module: dagster_mysql.event_log
    class: MySQLEventLogStorage
    config:
      mysql_db:
        username: { username }
        password: { password }
        hostname: { hostname }
        db_name: { db_name }
        port: { port }

  schedule_storage:
    module: dagster_mysql.schedule_storage
    class: MySQLScheduleStorage
    config:
      mysql_db:
        username: { username }
        password: { password }
        hostname: { hostname }
        db_name: { db_name }
        port: { port }
  ```

# 0.10.7

**New**

- When user code raises an error inside handle_output, load_input, or a type check function, the log output now includes context about which input or output the error occurred during.
- Added a secondary index to improve performance when querying run status. Run `dagster instance migrate` to upgrade.
- [Helm] Celery queues can now be configured with different node selectors. Previously, configuring a node selector applied it to all Celery queues.
- In Dagit, a repository location reload button is now available in the header of every pipeline, schedule, and sensor page.
- When viewing a run in Dagit, log filtering behavior has been improved. `step` and `type` filtering now offer fuzzy search, all log event types are now searchable, and visual bugs within the input have been repaired. Additionally, the default setting for “Hide non-matches” has been flipped to `true`.
- After launching a backfill in Dagit, the success message now includes a link to view the runs for the backfill.
- The `dagster-daemon` process now runs faster when running multiple schedulers or sensors from the same repository.
- When launching a backfill from Dagit, the “Re-execute From Last Run” option has been removed, because it had confusing semantics. “Re-execute From Failure” now includes a tooltip.
- `fs_io_manager` now defaults the base directory to `base_dir` via the Dagster instance’s `local_artifact_storage` configuration. Previously, it defaults to the directory where the pipeline is executed.
- Experimental IO managers `versioned_filesystem_io_manager` and `custom_path_fs_io_manager` now require `base_dir` as part of the resource configs. Previously, the `base_dir` defaulted to the directory where the pipeline was executed.
- Added a backfill daemon that submits backfill runs in a daemon process. This should relieve memory / CPU requirements for scheduling large backfill jobs. Enabling this feature requires a schema migration to the runs storage via the CLI command `dagster instance migrate` and configuring your instance with the following settings in `dagster.yaml`:
- backfill:
  daemon_enabled: true

There is a corresponding flag in the Dagster helm chart to enable this instance configuration. See the Helm chart’s `values.yaml` file for more information.

- Both sensors and schedule definitions support a `description` parameter that takes in a human-readable string description and displays it on the corresponding landing page in Dagit.

**Integrations**

- [dagster-gcp] The `gcs_pickle_io_manager` now also retries on 403 Forbidden errors, which previously would only retry on 429 TooManyRequests.

**Bug Fixes**

- The use of `Tuple` with nested inner types in solid definitions no longer causes GraphQL errors
- When searching assets in Dagit, keyboard navigation to the highlighted suggestion now navigates to the correct asset.
- In some cases, run status strings in Dagit (e.g. “Queued”, “Running”, “Failed”) did not accurately match the status of the run. This has been repaired.
- The experimental CLI command `dagster new-repo` should now properly generate subdirectories and files, without needing to install `dagster` from source (e.g. with `pip install --editable`).
- Sensor minimum intervals now interact in a more compatible way with sensor daemon intervals to minimize evaluation ticks getting skipped. This should result in the cadence of sensor evaluations being less choppy.

**Dependencies**

- Removed Dagster’s pin of the `pendulum` datetime/timezone library.

**Documentation**

- Added an example of how to write a user-in-the-loop pipeline

# 0.10.6

**New**

- Added a `dagster run delete` CLI command to delete a run and its associated event log entries.
- Added a `partition_days_offset` argument to the `@daily_schedule` decorator that allows you to customize which partition is used for each execution of your schedule. The default value of this parameter is `1`, which means that a schedule that runs on day N will fill in the partition for day N-1. To create a schedule that uses the partition for the current day, set this parameter to `0`, or increase it to make the schedule use an earlier day’s partition. Similar arguments have also been added for the other partitioned schedule decorators (`@monthly_schedule`, `@weekly_schedule`, and `@hourly_schedule`).
- The experimental `dagster new-repo` command now includes a workspace.yaml file for your new repository.
- When specifying the location of a gRPC server in your `workspace.yaml` file to load your pipelines, you can now specify an environment variable for the server’s hostname and port. For example, this is now a valid workspace:

```
load_from:
  - grpc_server:
      host:
        env: FOO_HOST
      port:
        env: FOO_PORT
```

**Integrations**

- [Kubernetes] `K8sRunLauncher` and `CeleryK8sRunLauncher` no longer reload the pipeline being executed just before launching it. The previous behavior ensured that the latest version of the pipeline was always being used, but was inconsistent with other run launchers. Instead, to ensure that you’re running the latest version of your pipeline, you can refresh your repository in Dagit by pressing the button next to the repository name.
- [Kubernetes] Added a flag to the Dagster helm chart that lets you specify that the cluster already has a redis server available, so the Helm chart does not need to create one in order to use redis as a messaging queue. For more information, see the Helm chart’s values.yaml file.

**Bug Fixes**

- Schedules with invalid cron strings will now throw an error when the schedule definition is loaded, instead of when the cron string is evaluated.
- Starting in the 0.10.1 release, the Dagit playground did not load when launched with the `--path-prefix` option. This has been fixed.
- In the Dagit playground, when loading the run preview results in a Python error, the link to view the error is now clickable.
- When using the “Refresh config” button in the Dagit playground after reloading a pipeline’s repository, the user’s solid selection is now preserved.
- When executing a pipeline with a `ModeDefinition` that contains a single executor, that executor is now selected by default.
- Calling `reconstructable` on pipelines with that were also decorated with hooks no longer raises an error.
- The `dagster-daemon liveness-check` command previously returned false when daemons surfaced non-fatal errors to be displayed in Dagit, leading to crash loops in Kubernetes. The command has been fixed to return false only when the daemon has stopped running.
- When a pipeline definition includes `OutputDefinition`s with `io_manager_key`s, or `InputDefinition`s with `root_manager_key`s, but any of the modes provided for the pipeline definition do not include a resource definition for the required key, Dagster now raises an error immediately instead of when the pipeline is executed.
- dbt 0.19.0 introduced breaking changes to the JSON schema of [dbt Artifacts](https://docs.getdbt.com/reference/artifacts/dbt-artifacts/). `dagster-dbt` has been updated to handle the new `run_results.json` schema for dbt 0.19.0.

**Dependencies**

- The astroid library has been pinned to version 2.4 in dagster, due to version 2.5 causing problems with our pylint test suite.

**Documentation**

- Added an example of how to trigger a Dagster pipeline in GraphQL at https://github.com/dagster-io/dagster/tree/0.10.6/examples/trigger_pipeline.
- Added better documentation for customizing sensor intervals at https://docs.dagster.io/overview/schedules-sensors/sensors.

# 0.10.5

**Community Contributions**

- Add `/License` for packages that claim distribution under Apache-2.0 (thanks [@bollwyvl](https://github.com/dagster-io/dagster/commits?author=bollwyvl)!)

**New**

- [k8s] Changed our weekly docker image releases (the default images in the helm chart). `dagster/dagster-k8s` and `dagster/dagster-celery-k8s` can be
  used for all processes which don't require user code (Dagit, Daemon, and Celery workers when using the CeleryK8sExecutor). `user-code-example` can
  be used for a sample user repository. The prior images (`k8s-dagit`, `k8s-celery-worker`, `k8s-example`)
  are deprecated.
- `configured` api on solids now enforces name argument as positional. The `name` argument remains a keyword argument on executors. `name` argument has been removed from resources, and loggers to reflect that they are anonymous. Previously, you would receive an error message if the `name` argument was provided to `configured` on resources or loggers.
- [sensors] In addition to the per-sensor `minimum_interval_seconds` field, the overall sensor daemon interval can now be configured in the `dagster.yaml` instance settings with:

```yaml
sensor_settings:
  interval_seconds: 30 # (default)
```

This changes the interval at which the daemon checks for sensors which haven't run within their `minimum_interval_seconds`.

- The message logged for type check failures now includes the description included in the `TypeCheck`
- The `dagster-daemon` process now runs each of its daemons in its own thread. This allows the scheduler, sensor loop, and daemon for launching queued runs to run in parallel, without slowing each other down. The `dagster-daemon` process will shut down if any of the daemon threads crash or hang, so that the execution environment knows that it needs to be restarted.
- `dagster new-repo` is a new CLI command that generates a Dagster repository with skeleton code in your filesystem. This CLI command is experimental and it may generate different files in future versions, even between dot releases. As of 0.10.5, `dagster new-repo` does not support Windows. [See here for official API docs.](http://localhost:3001/_apidocs/cli#dagster-new-repo)
- When using a `grpc_server` repository location, Dagit will automatically detect changes and prompt you to reload when the remote server updates.
- Improved consistency of headers across pages in Dagit.
- Added support for assets to the default SQLite event log storage.

**Integrations**

- [dagster-pandas] - Improved the error messages on failed pandas type checks.
- [dagster-postgres] - postgres_url is now a StringSource and can be loaded by environment variable
- [helm] - Users can set Kubernetes labels on Celery worker deployments
- [helm] - Users can set environment variables for Flower deployment
- [helm] - The redis helm chart is now included as an optional dagster helm chart dependency

**Bugfixes**

- Resolved an error preventing dynamic outputs from being passed to composite_solid inputs
- Fixed the tick history graph for schedules defined in a lazy-loaded repository ([#3626](https://github.com/dagster-io/dagster/issues/3626))
- Fixed performance regression of the Runs page on dagit.
- Fixed Gantt chart on Dagit run view to use the correct start time, repairing how steps are rendered within the chart.
- On Instance status page in Dagit, correctly handle states where daemons have multiple errors.
- Various Dagit bugfixes and improvements.

# 0.10.4

**Bugfixes**

- Fixed an issue with daemon heartbeat backwards compatibility. Resolves an error on Dagit's Daemon Status page

# 0.10.3

**New**

- [dagster] Sensors can now specify a `minimum_interval_seconds` argument, which determines the minimum amount of time between sensor evaluations.
- [dagit] After manually reloading the current repository, users will now be prompted to regenerate preset-based or partition-set based run configs in the Playground view. This helps ensure that the generated run config is up to date when launching new runs. The prompt does not occur when the repository is automatically reloaded.

**Bugfixes**

- Updated the `-n`/`--max_workers` default value for the `dagster api grpc` command to be `None`. When set to `None`, the gRPC server will use the default number of workers which is based on the CPU count. If you were previously setting this value to `1`, we recommend removing the argument or increasing the number.
- Fixed issue loading the schedule tick history graph for new schedules that have not been turned on.
- In Dagit, newly launched runs will open in the current tab instead of a new tab.
- Dagit bugfixes and improvements, including changes to loading state spinners.
- When a user specifies both an intermediate storage and an IO manager for a particular output, we no longer silently ignore the IO manager

# 0.10.2

**Community Contributions**

- [docs] Update URL to telemetry info (thanks @emilmelnikov (https://github.com/dagster-io/dagster/commits?author=emilmelnikov)!)
- [dagster-azure] Fix for listing files on ADL example (thanks @ericct!)

**New**

- [dagstermill] Users can now specify custom tags & descriptions for notebook solids.
- [dagster-pagerduty / dagster-slack] Added built-in hook integrations to create pagerduty/slack alerts when solids fail.
- [dagit] Added ability to preview runs for upcoming schedule ticks.

**Bugfixes**

- Fixed an issue where run start times and end times were displayed in the wrong timezone in Dagit when using Postgres storage.
- Schedules with partitions that weren’t able to execute due to not being able to find a partition will now display the name of the partition they were unable to find on the “Last tick” entry for that schedule.

- Improved timing information display for queued and canceled runs within the Runs table view and on individual Run pages in Dagit.
- Improvements to the tick history view for schedules and sensors.
- Fixed formatting issues on the Dagit instance configuration page.
- Miscellaneous Dagit bugfixes and improvements.
- The dagster pipeline launch command will now respect run concurrency limits if they are applied on your instance.
- Fixed an issue where re-executing a run created by a sensor would cause the daemon to stop executing any additional runs from that sensor.
- Sensor runs with invalid run configuration will no longer create a failed run - instead, an error will appear on the page for the sensor, allowing you to fix the configuration issue.
- General dagstermill housekeeping: test refactoring & type annotations, as well as repinning ipykernel to solve #3401

**Documentation**

- Improved dagster-dbt example.
- Added examples to demonstrate experimental features, including Memoized Development and Dynamic Graph.
- Added a PR template and how to pick an issue for the first time contributors

# 0.10.1

**Community Contributions**

- Reduced image size of `k8s-example` by 25% (104 MB) (thanks @alex-treebeard and @mrdavidlaing!)
- [dagster-snowflake] `snowflake_resource` can now be configured to use the SQLAlchemy connector (thanks @basilvetas!)

**New**

- When setting `userDeployments.deployments` in the Helm chart, `replicaCount` now defaults to 1 if not specified.

**Bugfixes**

- Fixed an issue where the Dagster daemon process couldn’t launch runs in repository locations containing more than one repository.
- Fixed an issue where Helm chart was not correctly templating `env`, `envConfigMaps`, and `envSecrets`.

**Documentation**

- Added new [troubleshooting guide](https://legacy-docs.dagster.io/troubleshooting) for problems encountered while using the `QueuedRunCoordinator` to limit run concurrency.
- Added documentation for the sensor command-line interface.

# 0.10.0 "The Edge of Glory"

### Major Changes

- A **native scheduler** with support for exactly-once, fault tolerant, timezone-aware scheduling.
  A new Dagster daemon process has been added to manage your schedules and sensors with a
  reconciliation loop, ensuring that all runs are executed exactly once, even if the Dagster daemon
  experiences occasional failure. See the
  [Migration Guide](https://github.com/dagster-io/dagster/blob/master/MIGRATION.md) for
  instructions on moving from `SystemCronScheduler` or `K8sScheduler` to the new scheduler.
- **First-class sensors**, built on the new Dagster daemon, allow you to instigate runs based on
  changes in external state - for example, files on S3 or assets materialized by other Dagster
  pipelines. See the [Sensors Overview](http://docs.dagster.io/overview/schedules-sensors/sensors)
  for more information.
- Dagster now supports **pipeline run queueing**. You can apply instance-level run concurrency
  limits and prioritization rules by adding the QueuedRunCoordinator to your Dagster instance. See
  the [Run Concurrency Overview](http://docs.dagster.io/overview/pipeline-runs/limiting-run-concurrency)
  for more information.
- The `IOManager` abstraction provides a new, streamlined primitive for granular control over where
  and how solid outputs are stored and loaded. This is intended to replace the (deprecated)
  intermediate/system storage abstractions, See the
  [IO Manager Overview](http://docs.dagster.io/overview/io-managers/io-managers) for more
  information.
- A new **Partitions page** in Dagit lets you view your your pipeline runs organized by partition.
  You can also **launch backfills from Dagit** and monitor them from this page.
- A new **Instance Status page** in Dagit lets you monitor the health of your Dagster instance,
  with repository location information, daemon statuses, instance-level schedule and sensor
  information, and linkable instance configuration.
- **Resources can now declare their dependencies on other resources** via the
  `required_resource_keys` parameter on `@resource`.
- Our support for deploying on **Kubernetes** is now mature and battle-tested Our Helm chart is
  now easier to configure and deploy, and we’ve made big investments in observability and
  reliability. You can view Kubernetes interactions in the structured event log and use Dagit to
  help you understand what’s happening in your deployment. The defaults in the Helm chart will
  give you graceful degradation and failure recovery right out of the box.
- Experimental support for **dynamic orchestration** with the new `DynamicOutputDefinition` API.
  Dagster can now map the downstream dependencies over a dynamic output at runtime.

### Breaking Changes

**Dropping Python 2 support**

- We’ve dropped support for Python 2.7, based on community usage and enthusiasm for Python 3-native
  public APIs.

**Removal of deprecated APIs**

_These APIs were marked for deprecation with warnings in the 0.9.0 release, and have been removed in
the 0.10.0 release._

- The decorator `input_hydration_config` has been removed. Use the `dagster_type_loader` decorator
  instead.
- The decorator `output_materialization_config` has been removed. Use `dagster_type_materializer`
  instead.
- The system storage subsystem has been removed. This includes `SystemStorageDefinition`,
  `@system_storage`, and `default_system_storage_defs` . Use the new `IOManagers` API instead. See
  the [IO Manager Overview](http://docs.dagster.io/overview/io-managers/io-managers) for more
  information.
- The `config_field` argument on decorators and definitions classes has been removed and replaced
  with `config_schema`. This is a drop-in rename.
- The argument `step_keys_to_execute` to the functions `reexecute_pipeline` and
  `reexecute_pipeline_iterator` has been removed. Use the `step_selection` argument to select
  subsets for execution instead.
- Repositories can no longer be loaded using the legacy `repository` key in your `workspace.yaml`;
  use `load_from` instead. See the
  [Workspaces Overview](https://docs.dagster.io/concepts/code-locations/workspace-files) for
  documentation about how to define a workspace.

**Breaking API Changes**

- `SolidExecutionResult.compute_output_event_dict` has been renamed to
  `SolidExecutionResult.compute_output_events_dict`. A solid execution result is returned from
  methods such as `result_for_solid`. Any call sites will need to be updated.
- The `.compute` suffix is no longer applied to step keys. Step keys that were previously named
  `my_solid.compute` will now be named `my_solid`. If you are using any API method that takes a
  step_selection argument, you will need to update the step keys accordingly.
- The `pipeline_def` property has been removed from the `InitResourceContext` passed to functions
  decorated with `@resource`.

**Dagstermill**

- If you are using `define_dagstermill_solid` with the `output_notebook` parameter set to `True`,
  you will now need to provide a file manager resource (subclass of
  `dagster.core.storage.FileManager`) on your pipeline mode under the resource key `"file_manager"`,
  e.g.:

  ```python
  from dagster import ModeDefinition, local_file_manager, pipeline
  from dagstermill import define_dagstermill_solid

  my_dagstermill_solid = define_dagstermill_solid("my_dagstermill_solid", output_notebook=True, ...)

  @pipeline(mode_defs=[ModeDefinition(resource_defs={"file_manager": local_file_manager})])
  def my_dagstermill_pipeline():
      my_dagstermill_solid(...)
  ```

**Helm Chart**

- The schema for the `scheduler` values in the helm chart has changed. Instead of a simple toggle
  on/off, we now require an explicit `scheduler.type` to specify usage of the
  `DagsterDaemonScheduler`, `K8sScheduler`, or otherwise. If your specified `scheduler.type` has
  required config, these fields must be specified under `scheduler.config`.
- `snake_case` fields have been changed to `camelCase`. Please update your `values.yaml` as follows:
  - `pipeline_run` → `pipelineRun`
  - `dagster_home` → `dagsterHome`
  - `env_secrets` → `envSecrets`
  - `env_config_maps` → `envConfigMaps`
- The Helm values `celery` and `k8sRunLauncher` have now been consolidated under the Helm value
  `runLauncher` for simplicity. Use the field `runLauncher.type` to specify usage of the
  `K8sRunLauncher`, `CeleryK8sRunLauncher`, or otherwise. By default, the `K8sRunLauncher` is
  enabled.
- All Celery message brokers (i.e. RabbitMQ and Redis) are disabled by default. If you are using
  the `CeleryK8sRunLauncher`, you should explicitly enable your message broker of choice.
- `userDeployments` are now enabled by default.

### Core

- Event log messages streamed to `stdout` and `stderr` have been streamlined to be a single line
  per event.
- Experimental support for memoization and versioning lets you execute pipelines incrementally,
  selecting which solids need to be rerun based on runtime criteria and versioning their outputs
  with configurable identifiers that capture their upstream dependencies.

  To set up memoized step selection, users can provide a `MemoizableIOManager`, whose `has_output`
  function decides whether a given solid output needs to be computed or already exists. To execute
  a pipeline with memoized step selection, users can supply the `dagster/is_memoized_run` run tag
  to `execute_pipeline`.

  To set the version on a solid or resource, users can supply the `version` field on the definition.
  To access the derived version for a step output, users can access the `version` field on the
  `OutputContext` passed to the `handle_output` and `load_input` methods of `IOManager` and the
  `has_output` method of `MemoizableIOManager`.

- Schedules that are executed using the new `DagsterDaemonScheduler` can now execute in any
  timezone by adding an `execution_timezone` parameter to the schedule. Daylight Savings Time
  transitions are also supported. See the
  [Schedules Overview](http://docs.dagster.io/overview/schedules-sensors/schedules#timezones) for
  more information and examples.

### Dagit

- Countdown and refresh buttons have been added for pages with regular polling queries (e.g. Runs,
  Schedules).
- Confirmation and progress dialogs are now presented when performing run terminations and
  deletions. Additionally, hanging/orphaned runs can now be forced to terminate, by selecting
  "Force termination immediately" in the run termination dialog.
- The Runs page now shows counts for "Queued" and "In progress" tabs, and individual run pages
  show timing, tags, and configuration metadata.
- The backfill experience has been improved with means to view progress and terminate the entire
  backfill via the partition set page. Additionally, errors related to backfills are now surfaced
  more clearly.
- Shortcut hints are no longer displayed when attempting to use the screen capture command.
- The asset page has been revamped to include a table of events and enable organizing events by
  partition. Asset key escaping issues in other views have been fixed as well.
- Miscellaneous bug fixes, frontend performance tweaks, and other improvements are also included.

### Kubernetes/Helm

- The [Dagster Kubernetes documentation](https://legacy-docs.dagster.io/deploying/kubernetes) has been refreshed.

**Helm**

- We've added schema validation to our Helm chart. You can now check that your values YAML file is
  correct by running:

  ```bash
  helm lint helm/dagster -f helm/dagster/values.yaml
  ```

- Added support for resource annotations throughout our Helm chart.
- Added Helm deployment of the dagster daemon & daemon scheduler.
- Added Helm support for configuring a compute log manager in your dagster instance.
- User code deployments now include a user `ConfigMap` by default.
- Changed the default liveness probe for Dagit to use `httpGet "/dagit_info"` instead of
  `tcpSocket:80`

**Dagster-K8s [Kubernetes]**

- Added support for user code deployments on Kubernetes.
- Added support for tagging pipeline executions.
- Fixes to support version 12.0.0 of the Python Kubernetes client.
- Improved implementation of Kubernetes+Dagster retries.
- Many logging improvements to surface debugging information and failures in the structured event
  log.

**Dagster-Celery-K8s**

- Improved interrupt/termination handling in Celery workers.

### Integrations & Libraries

- Added a new `dagster-docker` library with a `DockerRunLauncher` that launches each run in its own
  Docker container. (See [Deploying with Docker docs](https://docs.dagster.io/examples/deploy_docker)
  for an example.)
- Added support for AWS Athena. (Thanks @jmsanders!)
- Added mocks for AWS S3, Athena, and Cloudwatch in tests. (Thanks @jmsanders!)
- Allow setting of S3 endpoint through env variables. (Thanks @marksteve!)
- Various bug fixes and new features for the Azure, Databricks, and Dask integrations.
- Added a `create_databricks_job_solid` for creating solids that launch Databricks jobs.

# 0.9.22.post0

**Bugfixes**

- [Dask] Pin dask[dataframe] to <=2.30.0 and distributed to <=2.30.1

# 0.9.22

**New**

- When using a solid selection in the Dagit Playground, non-matching solids are hidden in the
  RunPreview panel.
- The CLI command dagster pipeline launch now accepts --run-id

**Bugfixes**

- [Helm/K8s] Fixed whitespacing bug in ingress.yaml Helm template.

# 0.9.21

**Community Contributions**

- Fixed helm chart to only add flower to the K8s ingress when enabled (thanks [@PenguinToast](https://github.com/PenguinToast)!)
- Updated helm chart to use more lenient timeouts for liveness probes on user code deployments (thanks [@PenguinToast](https://github.com/PenguinToast)!)

**Bugfixes**

- [Helm/K8s] Due to Flower being incompatible with Celery 5.0, the Helm chart for Dagster now uses a specific image `mher/flower:0.9.5` for the Flower pod.

# 0.9.20

**New**

- [Dagit] Show recent runs on individual schedule pages
- [Dagit] It’s no longer required to run `dagster schedule up` or press the Reconcile button before turning on a new schedule for the first time
- [Dagit] Various improvements to the asset view. Expanded the Last Materialization Event view. Expansions to the materializations over time view, allowing for both a list view and a graphical view of materialization data.

**Community Contributions**

- Updated many dagster-aws tests to use mocked resources instead of depending on real cloud resources, making it possible to run these tests locally. (thanks @jmsanders!)

**Bugfixes**

- fixed an issue with retries in step launchers
- [Dagit] bugfixes and improvements
- Fixed an issue where dagit sometimes left hanging processes behind after exiting

**Experimental**

- [K8s] The dagster daemon is now optionally deployed by the helm chart. This enables run-level queuing with the QueuedRunCoordinator.

# 0.9.19

**New**

- Improved error handling when the intermediate storage stores and retrieves objects.
- New URL scheme in Dagit, with repository details included on all paths for pipelines, solids, and schedules
- Relaxed constraints for the AssetKey constructor, to enable arbitrary strings as part of the key path.
- When executing a subset of a pipeline, configuration that does not apply to the current subset but would be valid in the original pipeline is now allowed and ignored.
- GCSComputeLogManager was added, allowing for compute logs to be persisted to Google cloud storage
- The step-partition matrix in Dagit now auto-reloads runs

**Bugfixes**

- Dagit bugfixes and improvements
- When specifying a namespace during helm install, the same namespace will now be used by the K8sScheduler or K8sRunLauncher, unless overridden.
- `@pipeline` decorated functions with -> None typing no longer cause unexpected problems.
- Fixed an issue where compute logs might not always be complete on Windows.

# 0.9.18

**Breaking Changes**

- `CliApiRunLauncher` and `GrpcRunLauncher` have been combined into `DefaultRunLauncher`.
  If you had one of these run launchers in your `dagster.yaml`, replace it with `DefaultRunLauncher`
  or remove the `run_launcher:` section entirely.

**New**

- Added a type loader for typed dictionaries: can now load typed dictionaries from config.

**Bugfixes**

- Dagit bugfixes and improvements
  - Added error handling for repository errors on startup and reload
  - Repaired timezone offsets
  - Fixed pipeline explorer state for empty pipelines
  - Fixed Scheduler table
- User-defined k8s config in the pipeline run tags (with key `dagster-k8s/config`) will now be
  passed to the k8s jobs when using the `dagster-k8s` and `dagster-celery-k8s` run launchers.
  Previously, only user-defined k8s config in the pipeline definition’s tag was passed down.

**Experimental**

- Run queuing: the new `QueuedRunCoordinator` enables limiting the number of concurrent runs.
  The `DefaultRunCoordinator` launches jobs directly from Dagit, preserving existing behavior.

# 0.9.17

**New**

- [dagster-dask] Allow connecting to an existing scheduler via its address
- [dagster-aws] Importing dagster_aws.emr no longer transitively importing dagster_spark
- [dagster-dbr] CLI solids now emit materializations

**Community contributions**

- Docs fix (Thanks @kaplanbora!)

**Bug fixes**

- `PipelineDefinition` 's that do not meet resource requirements for its types will now fail at definition time
- Dagit bugfixes and improvements
- Fixed an issue where a run could be left hanging if there was a failure during launch

**Deprecated**

- We now warn if you return anything from a function decorated with `@pipeline`. This return value actually had no impact at all and was ignored, but we are making changes that will use that value in the future. By changing your code to not return anything now you will avoid any breaking changes with zero user-visible impact.

# 0.9.16

**Breaking Changes**

- Removed `DagsterKubernetesPodOperator` in `dagster-airflow`.
- Removed the `execute_plan` mutation from `dagster-graphql`.
- `ModeDefinition`, `PartitionSetDefinition`, `PresetDefinition`, `@repository`, `@pipeline`, and `ScheduleDefinition` names must pass the regular expression `r"^[A-Za-z0-9_]+$"` and not be python keywords or disallowed names. See `DISALLOWED_NAMES` in `dagster.core.definitions.utils` for exhaustive list of illegal names.
- `dagster-slack` is now upgraded to use slackclient 2.x - this means that this resource will only support Python 3.6 and above.
- [K8s] Added a health check to the helm chart for user deployments, which relies on a new `dagster api grpc-health-check` cli command present in Dagster `0.9.16` and later.

**New**

- Add helm chart configurations to allow users to configure a `K8sRunLauncher`, in place of the `CeleryK8sRunLauncher`.
- “Copy URL” button to preserve filter state on Run page in dagit

**Community Contributions**

- Dagster CLI options can now be passed in via environment variables (Thanks @xinbinhuang!)
- New `--limit` flag on the `dagster run list` command (Thanks @haydarai!)

**Bugfixes**

- Addressed performance issues loading the /assets table in dagit. Requires a data migration to create a secondary index by running dagster instance reindex.
- Dagit bugfixes and improvements

# 0.9.15

**Breaking Changes**

- CeleryDockerExecutor no longer requires a repo_location_name config field.
- `executeRunInProcess` was removed from `dagster-graphql`.

**New**

- Dagit: Warn on tab removal in playground
- Display versions CLI: Added a new CLI that displays version information for a memoized run. Called via dagster pipeline list_versions.
- CeleryDockerExecutor accepts a network field to configure the network settings for the Docker container it connects to for execution.
- Dagit will now set a statement timeout on supported instance DBs. Defaults to 5s and can be controlled with the --db-statement-timeout flag

**Community Contributions**

- dagster grpc requirements are now more friendly for users (thanks @jmo-qap!)
- dagster.utils now has is_str (thanks @monicayao!)
- dagster-pandas can now load dataframes from pickle (thanks @mrdrprofuroboros!)
- dagster-ge validation solid factory now accepts name (thanks @haydarai!)

**Bugfixes**

- Dagit bugfixes and improvements
- Fixed an issue where dagster could fail to load large pipelines.
- Fixed a bug where experimental arg warning would be thrown even when not using versioned dagster type loaders.
- Fixed a bug where CeleryDockerExecutor was failing to execute pipelines unless they used a legacy workspace config.
- Fixed a bug where pipeline runs using IntMetadataEntryData could not be visualized in dagit.

**Experimental**

- Improve the output structure of dagster-dbt solids.
- Version-based memoization over outputs stored in the intermediate store now works

**Documentation**

- Fix a code snippet rendering issue in Overview: Assets & Materializations
- Fixed all python code snippets alignment across docs examples

# 0.9.14

**New**

- Steps down stream of a failed step no longer report skip events and instead simply do not execute.
- dagit-debug can load multiple debug files.
- dagit now has a Debug Console Logging feature flag accessible at /flags .
- Telemetry metrics are now taken when scheduled jobs are executed.
- With memoized reexecution, we now only copy outputs that current plan won't generate
- Document titles throughout dagit

**Community Contributions**

- [dagster-ge] solid factory can now handle arbitrary types (thanks @sd2k!)
- [dagster-dask] utility options are now available in loader/materializer for Dask DataFrame (thanks @kinghuang!)

**Bugfixes**

- Fixed an issue where run termination would sometimes be ignored or leave the execution process hanging
- [dagster-k8s] fixed issue that would cause timeouts on clusters with many jobs
- Fixed an issue where reconstructable was unusable in an interactive environment, even when the pipeline is defined in a different module.
- Bugfixes and UX improvements in dagit

**Experimental**

- AssetMaterializations now have an optional “partition” attribute

# 0.9.13

**Bugfixes**

- Fixes an issue using `build_reconstructable_pipeline`.
- Improved loading times for the asset catalog in Dagit.

**Documentations**

- Improved error messages when invoking dagit from the CLI with bad arguments.

# 0.9.12

**Breaking Changes**

- Dagster now warns when a solid, pipeline, or other definition is created with an invalid name (for example, a Python keyword). This warning will become an error in the 0.9.13 release.

**Community Contributions**

- Added an int type to `EventMetadataEntry` (Thanks @[ChocoletMousse](https://github.com/ChocoletMousse)!)
- Added a `build_composite_solid_definition` method to Lakehouse (Thanks @[sd2k](https://github.com/sd2k)!)
- Improved broken link detection in Dagster docs (Thanks @[keyz](https://github.com/keyz)!)

**New**

- Improvements to log filtering on Run view in Dagit
- Improvements to instance level scheduler page
- Log engine events when pipeline termination is initiated

**Bugfixes**

- Syntax errors in user code now display the file and line number with the error in Dagit
- Dask executor no longer fails when using intermediate_storage
- In the Celery K8s executor, we now mark the step as failed when the step job fails
- Changed the `DagsterInvalidAssetKey` error so that it no longer fails upon being thrown

**Documentation**

- Added API docs for dagster-dbt experimental library
- Fixed some cosmetic issues with docs.dagster.io
- Added code snippets from Solids examples to test path, and fixed some inconsistencies regarding parameter ordering
- Changed to using markers instead of exact line numbers to mark out code snippets

# 0.9.10

**Breaking Changes**

- [dagster-dask] Removed the `compute` option from Dask DataFrame materialization configs for all output types. Setting this option to `False` (default `True`) would result in a future that is never computed, leading to missing materializations

**Community Contributions**

- Added a Dask resource (Thanks @[kinghuang](https://github.com/kinghuang)!)

**New**

- Console log messages are now streamlined to live on a single line per message
- Added better messaging around `$DAGSTER_HOME` if it is not set or improperly setup when starting up a Dagster instance
- Tools for exporting a file for debugging a run have been added:
  - `dagster debug export` - a new CLI entry added for exporting a run by id to a file
  - `dagit-debug` - a new CLI added for loading dagit with a run to debug
  - `dagit` now has a button to download the debug file for a run via the action menu on the runs page
- The `dagster api grpc` command now defaults to the current working directory if none is specified
- Added retries to dagster-postgres connections
- Fixed faulty warning message when invoking the same solid multiple times in the same context
- Added ability to specify custom liveness probe for celery workers in kubernetes deployment

**Bugfixes**

- Fixed a bug where Dagster types like List/Set/Tuple/Dict/Optional were not displaying properly on dagit logs
- Fixed endless spinners on `dagit --empty-workspace`
- Fixed incorrect snapshot banner on pipeline view
- Fixed visual overlapping of overflowing dagit logs
- Fixed a bug where hanging runs when executing against a gRPC server could cause the Runs page to be unable to load
- Fixed a bug in celery integration where celery tasks could return `None` when an iterable is expected, causing errors in the celery execution loop.

**Experimental**

- [lakehouse] Each time a Lakehouse solid updates an asset, it automatically generates an AssetMaterialization event
- [lakehouse] Lakehouse computed_assets now accept a version argument that describes the version of the computation
- Setting the “dagster/is_memoized_run” tag to true will cause the run to skip any steps whose versions match the versions of outputs produced in prior runs.
- [dagster-dbt] Solids for running dbt CLI commands
- Added extensive documentation to illuminate how versions are computed
- Added versions for step inputs from config, default values, and from other step outputs

# 0.9.9

**New**

- [Databricks] solids created with create_databricks_job_solid now log a URL for accessing the job in the Databricks UI.
- The pipeline execute command now defaults to using your current directory if you don’t specify a working directory.

**Bugfixes**

- [Celery-K8s] Surface errors to Dagit that previously were not caught in the Celery workers.
- Fix issues with calling add_run_tags on tags that already exist.
- Add “Unknown” step state in Dagit’s pipeline run logs view for when pipeline has completed but step has not emitted a completion event

**Experimental**

- Version tags for resources and external inputs.

**Documentation**

- Fix rendering of example solid config in “Basics of Solids” tutorial.

# 0.9.8

**New**

- Support for the Dagster step selection DSL: `reexecute_pipeline` now takes `step_selection`, which accepts queries like `*solid_a.compute++` (i.e., `solid_a.compute`, all of its ancestors, its immediate descendants, and their immediate descendants). `steps_to_execute` is deprecated and will be removed in 0.10.0.

**Community contributions**

- [dagster-databricks] Improved setup of Databricks environment (Thanks @[sd2k](https://github.com/sd2k)!)
- Enabled frozenlist pickling (Thanks @[kinghuang](https://github.com/kinghuang)!)

**Bugfixes**

- Fixed a bug that pipeline-level hooks were not correctly applied on a pipeline subset.
- Improved error messages when execute command can't load a code pointer.
- Fixed a bug that prevented serializing Spark intermediates with configured intermediate storages.

**Dagit**

- Enabled subset reexecution via Dagit when part of the pipeline is still running.
- Made `Schedules` clickable and link to View All page in the schedule section.
- Various Dagit UI improvements.

**Experimental**

- [lakehouse] Added CLI command for building and executing a pipeline that updates a given set of assets: `house update --module package.module —assets my_asset*`

**Documentation**

- Fixes and improvements.

# 0.9.7

**Bugfixes**

- Fixed an issue in the dagstermill library that caused solid config fetch to be non-deterministic.
- Fixed an issue in the K8sScheduler where multiple pipeline runs were kicked off for each scheduled
  execution.

# 0.9.6

**New**

- Added ADLS2 storage plugin for Spark DataFrame (Thanks @sd2k!)
- Added feature in the Dagit Playground to automatically remove extra configuration that does not conform to a pipeline’s config schema.
- [Dagster-Celery/Celery-K8s/Celery-Docker] Added Celery worker names and pods to the logs for each step execution

**Community contributions**

- Re-enabled dagster-azure integration tests in dagster-databricks tests (Thanks @sd2k!)
- Moved dict_without_keys from dagster-pandas into dagster.utils (Thanks @DavidKatz-il)
- Moved Dask DataFrame read/to options under read/to keys (Thanks @kinghuang)

**Bugfixes**

- Fixed helper for importing data from GCS paths into Bigquery (Thanks @grabangomb (https://github.com/grabangomb)!)
- Postgres event storage now waits to open a thread to watch runs until it is needed

**Experimental**

- Added version computation function for DagsterTypeLoader. (Actual versioning will be supported in 0.10.0)
- Added version attribute to solid and SolidDefinition. (Actual versioning will be supported in 0.10.0)

# 0.9.5

**New**

- UI improvements to the backfill partition selector
- Enabled sorting of steps by failure in the partition run matrix in Dagit

**Bugfixes**

- [dagstermill] fixes an issue with output notebooks and s3 storage
- [dagster_celery] bug fixed in pythonpath calculation (thanks @enima2648!)
- [dagster_pandas] marked create_structured_dataframe_type and ConstraintWithMetadata as experimental APIs
- [dagster_k8s] reduced default job backoff limit to 0

**Docs**

- Various docs site improvements

# 0.9.4

**Breaking Changes**

- When using the `configured` API on a solid or composite solid, a new solid name must be provided.
- The image used by the K8sScheduler to launch scheduled executions is now specified under the “scheduler” section of the Helm chart (previously under “pipeline_run” section).

**New**

- Added an experimental mode that speeds up interactions in dagit by launching a gRPC server on startup for each repository location in your workspace. To enable it, add the following to your `dagster.yaml`:

```yaml
opt_in:
  local_servers: true
```

- Intermediate Storage and System Storage now default to the first provided storage definition when no configuration is provided. Previously, it would be necessary to provide a run config for storage whenever providing custom storage definitions, even if that storage required no run configuration. Now, if the first provided storage definition requires no run configuration, the system will default to using it.
- Added a timezone picker to Dagit, and made all timestamps timezone-aware
- Added solid_config to hook context which provides the access to the config schema variable of the corresponding solid.
- Hooks can be directly set on `PipelineDefinition` or `@pipeline`, e.g. `@pipeline(hook_defs={hook_a})`. It will apply the hooks on every single solid instance within the pipeline.
- Added Partitions tab for partitioned pipelines, with new backfill selector.

# 0.9.3

**Breaking Changes**

- Removed deprecated `--env` flag from CLI
- The `--host` CLI param has been renamed to `--grpc_host` to avoid conflict with the dagit `--host` param.

**New**

- Descriptions for solid inputs and outputs will now be inferred from doc blocks if available (thanks [@AndersonReyes](https://github.com/dagster-io/dagster/commits?author=AndersonReyes) !)
- Various documentation improvements (thanks [@jeriscc](https://github.com/dagster-io/dagster/commits?author=jeriscc) !)
- Load inputs from pyspark dataframes (thanks [@davidkatz-il](https://github.com/dagster-io/dagster/commits?author=davidkatz-il) !)
- Added step-level run history for partitioned schedules on the schedule view
- Added great_expectations integration, through the `dagster_ge` library. Example usage is under a new example, called `ge_example`, and documentation for the library can be found under the libraries section of the api docs.
- `PythonObjectDagsterType` can now take a tuple of types as well as a single type, more closely mirroring `isinstance` and allowing Union types to be represented in Dagster.
- The `configured` API can now be used on all definition types (including `CompositeDefinition`). Example usage has been updated in the [configuration documentation](https://legacy-docs.dagster.io/overview/configuration/configured).
- Updated Helm chart to include auto-generated user code configmap in user code deployment by default

**Bugfixes**

- Databricks now checks intermediate storage instead of system storage
- Fixes a bug where applying hooks on a pipeline with composite solids would flatten the top-level solids. Now applying hooks on pipelines or composite solids means attaching hooks to every single solid instance within the pipeline or the composite solid.
- Fixes the GraphQL playground hosted by dagit
- Fixes a bug where K8s CronJobs were stopped unnecessarily during schedule reconciliation

**Experimental**

- New `dagster-k8s/config` tag that lets users pass in custom configuration to the Kubernetes `Job`, `Job` metadata, `JobSpec`, `PodSpec`, and `PodTemplateSpec` metadata.
  - This allows users to specify settings like eviction policy annotations and node affinities.
  - Example:
  ```python
    @solid(
      tags = {
        'dagster-k8s/config': {
          'container_config': {
            'resources': {
              'requests': { 'cpu': '250m', 'memory': '64Mi' },
              'limits': { 'cpu': '500m', 'memory': '2560Mi' },
            }
          },
          'pod_template_spec_metadata': {
            'annotations': { "cluster-autoscaler.kubernetes.io/safe-to-evict": "true"}
          },
          'pod_spec_config': {
            'affinity': {
              'nodeAffinity': {
                'requiredDuringSchedulingIgnoredDuringExecution': {
                  'nodeSelectorTerms': [{
                    'matchExpressions': [{
                      'key': 'beta.kubernetes.io/os', 'operator': 'In', 'values': ['windows', 'linux'],
                    }]
                  }]
                }
              }
            }
          },
        },
      },
    )
    def my_solid(context):
      context.log.info('running')
  ```

# 0.9.2

**Breaking Changes**

- The `--env` flag no longer works for the `pipeline launch` or `pipeline execute` commands. Use `--config` instead.
- The `pipeline execute` command no longer accepts the `--workspace` argument.
  To execute pipelines in a workspace, use `pipeline launch` instead.

**New**

- Added `ResourceDefinition.mock_resource` helper for magic mocking resources. Example usage can be found [here](https://git.io/JJ7tz)
- Remove the `row_count` metadata entry from the Dask DataFrame type check (thanks [@kinghuang](https://github.com/kinghuang)!)
- Add [`orient`](https://docs.dask.org/en/latest/dataframe-api.html#dask.dataframe.to_json) to the config options when materializing a Dask DataFrame to `json` (thanks [@kinghuang](https://github.com/kinghuang)!)

**Bugfixes**

- Fixed a bug where applying `configured` to a solid definition would overwrite inputs from run config.
- Fixed a bug where pipeline tags would not apply to solid subsets.
- Improved error messages for repository-loading errors in CLI commands.
- Fixed a bug where pipeline execution error messages were not being surfaced in Dagit.

# 0.9.1

**Bugfixes**

- Fixes an issue in the `dagster-k8s-celery` executor when executing solid subsets

**Breaking Changes**

- Deprecated the `IntermediateStore` API. `IntermediateStorage` now wraps an ObjectStore, and `TypeStoragePlugin` now accepts an `IntermediateStorage` instance instead of an `IntermediateStore` instance. (Noe that `IntermediateStore` and `IntermediateStorage` are both internal APIs that are used in some non-core libraries).

# 0.9.0 “Laundry Service”

**Breaking Changes**

- The `dagit` key is no longer part of the instance configuration schema and must be removed from `dagster.yaml` files before they can be used.
- `-d` can no longer be used as a command-line argument to specify a mode. Use `--mode` instead.
- Use `--preset` instead of `--preset-name` to specify a preset to the `pipeline launch` command.
- We have removed the `config` argument to the `ConfigMapping`, `@composite_solid`, `@solid`, `SolidDefinition`, `@executor`, `ExecutorDefinition`, `@logger`, `LoggerDefinition`, `@resource`, and `ResourceDefinition` APIs, which we deprecated in 0.8.0. Use `config_schema` instead.

**New**

- Python 3.8 is now fully supported.
- `-d` or `--working-directory` can be used to specify a working directory in any command that
  takes in a `-f` or `--python_file` argument.
- Removed the deprecation of `create_dagster_pandas_dataframe_type`. This is the currently
  supported API for custom pandas data frame type creation.
- Removed gevent dependency from dagster
- New `configured` API for predefining configuration for various definitions: https://legacy-docs.dagster.io/overview/configuration/#configured
- Added hooks to enable success and failure handling policies on pipelines. This enables users to set up policies on all solids within a pipeline or on a per solid basis. Example usage can be found [here](https://legacy-docs.dagster.io/examples/hooks)
- New instance level view of Scheduler and running schedules
- dagster-graphql is now only required in dagit images.

# 0.8.11

**Breaking Changes**

- `AssetMaterializations` no longer accepts a `dagster_type` argument. This reverts the change
  billed as "`AssetMaterializations` can now have type information attached as metadata." in the
  previous release.

# 0.8.10

**New**

- Added new GCS and Azure file manager resources
- `AssetMaterializations` can now have type information attached as metadata. See the materializations tutorial for more
- Added verification for resource arguments (previously only validated at runtime)

**Bugfixes**

- Fixed bug with order-dependent python module resolution seen with some packages (e.g. numpy)
- Fixed bug where Airflow's `context['ts']` was not passed properly
- Fixed a bug in celery-k8s when using `task_acks_late: true` that resulted in a `409 Conflict error` from Kubernetes. The creation of a Kubernetes Job will now be aborted if another Job with the same name exists
- Fixed a bug with composite solid output results when solids are skipped
- Hide the re-execution button in Dagit when the pipeline is not re-executable in the currently loaded repository

**Docs**

- Fixed code example in the advanced scheduling doc (Thanks @wingyplus!)
- Various other improvements

# 0.8.9

**New**

- `CeleryK8sRunLauncher` supports termination of pipeline runs. This can be accessed via the
  “Terminate” button in Dagit’s Pipeline Run view or via “Cancel” in Dagit’s All Runs page. This
  will terminate the run master K8s Job along with all running step job K8s Jobs; steps that are
  still in the Celery queue will not create K8s Jobs. The pipeline and all impacted steps will
  be marked as failed. We recommend implementing resources as context managers and we will execute
  the finally block upon termination.
- `K8sRunLauncher` supports termination of pipeline runs.
- `AssetMaterialization` events display the asset key in the Runs view.
- Added a new "Actions" button in Dagit to allow to cancel or delete mulitple runs.

**Bugfixes**

- Fixed an issue where `DagsterInstance` was leaving database connections open due to not being
  garbage collected.
- Fixed an issue with fan-in inputs skipping when upstream solids have skipped.
- Fixed an issue with getting results from composites with skippable outputs in python API.
- Fixed an issue where using `Enum` in resource config schemas resulted in an error.

# 0.8.8

**New**

- The new `configured` API makes it easy to create configured versions of resources.
- Deprecated the `Materialization` event type in favor of the new `AssetMaterialization` event type,
  which requires the `asset_key` parameter. Solids yielding `Materialization` events will continue
  to work as before, though the `Materialization` event will be removed in a future release.
- We are starting to deprecate "system storages" - instead of pipelines having a system storage
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
- The help panel in the dagit config editor can now be resized and toggled open or closed, to
  enable easier editing on smaller screens.

**Bugfixes**

- Opening new Dagit browser windows maintains your current repository selection. #2722
- Pipelines with the same name in different repositories no longer incorrectly share playground state. #2720
- Setting `default_value` config on a field now works as expected. #2725
- Fixed rendering bug in the dagit run reviewer where yet-to-be executed execution steps were
  rendered on left-hand side instead of the right.

# 0.8.7

**Breaking Changes**

- Loading python modules reliant on the working directory being on the PYTHONPATH is no longer
  supported. The `dagster` and `dagit` CLI commands no longer add the working directory to the
  PYTHONPATH when resolving modules, which may break some imports. Explicitly installed python
  packages can be specified in workspaces using the `python_package` workspace yaml config option.
  The `python_module` config option is deprecated and will be removed in a future release.

**New**

- Dagit can be hosted on a sub-path by passing `--path-prefix` to the dagit CLI. #2073
- The `date_partition_range` util function now accepts an optional `inclusive` boolean argument. By default, the function does not return include the partition for which the end time of the date range is greater than the current time. If `inclusive=True`, then the list of partitions returned will include the extra partition.
- `MultiDependency` or fan-in inputs will now only cause the solid step to skip if all of the
  fanned-in inputs upstream outputs were skipped

**Bugfixes**

- Fixed accidental breaking change with `input_hydration_config` arguments
- Fixed an issue with yaml merging (thanks @shasha79!)
- Invoking `alias` on a solid output will produce a useful error message (thanks @iKintosh!)
- Restored missing run pagination controls
- Fixed error resolving partition-based schedules created via dagster schedule decorators (e.g. `daily_schedule`) for certain workspace.yaml formats

# 0.8.6

**Breaking Changes**

- The `dagster-celery` module has been broken apart to manage dependencies more coherently. There
  are now three modules: `dagster-celery`, `dagster-celery-k8s`, and `dagster-celery-docker`.
- Related to above, the `dagster-celery worker start` command now takes a required `-A` parameter
  which must point to the `app.py` file within the appropriate module. E.g if you are using the
  `celery_k8s_job_executor` then you must use the `-A dagster_celery_k8s.app` option when using the
  `celery` or `dagster-celery` cli tools. Similar for the `celery_docker_executor`:
  `-A dagster_celery_docker.app` must be used.
- Renamed the `input_hydration_config` and `output_materialization_config` decorators to
  `dagster_type_` and `dagster_type_materializer` respectively. Renamed DagsterType's
  `input_hydration_config` and `output_materialization_config` arguments to `loader` and `materializer` respectively.

**New**

- New pipeline scoped runs tab in Dagit
- Add the following Dask Job Queue clusters: moab, sge, lsf, slurm, oar (thanks @DavidKatz-il!)
- K8s resource-requirements for run coordinator pods can be specified using the `dagster-k8s/ resource_requirements` tag on pipeline definitions:

  ```python
  @pipeline(
      tags={
          'dagster-k8s/resource_requirements': {
              'requests': {'cpu': '250m', 'memory': '64Mi'},
              'limits': {'cpu': '500m', 'memory': '2560Mi'},
          }
      },
  )
  def foo_bar_pipeline():
  ```

- Added better error messaging in dagit for partition set and schedule configuration errors
- An initial version of the CeleryDockerExecutor was added (thanks @mrdrprofuroboros!). The celery
  workers will launch tasks in docker containers.
- **Experimental:** Great Expectations integration is currently under development in the new library
  dagster-ge. Example usage can be found [here](https://github.com/dagster-io/dagster/blob/master/python_modules/libraries/dagster-ge/dagster_ge/examples/ge_demo.py)

# 0.8.5

**Breaking Changes**

- Python 3.5 is no longer under test.
- `Engine` and `ExecutorConfig` have been deleted in favor of `Executor`. Instead of the `@executor` decorator decorating a function that returns an `ExecutorConfig` it should now decorate a function that returns an `Executor`.

**New**

- The python built-in `dict` can be used as an alias for `Permissive()` within a config schema declaration.
- Use `StringSource` in the `S3ComputeLogManager` configuration schema to support using environment variables in the configuration (Thanks @mrdrprofuroboros!)
- Improve Backfill CLI help text
- Add options to spark_df_output_schema (Thanks @DavidKatz-il!)
- Helm: Added support for overriding the PostgreSQL image/version used in the init container checks.
- Update celery k8s helm chart to include liveness checks for celery workers and flower
- Support step level retries to celery k8s executor

**Bugfixes**

- Improve error message shown when a RepositoryDefinition returns objects that are not one of the allowed definition types (Thanks @sd2k!)
- Show error message when `$DAGSTER_HOME` environment variable is not an absolute path (Thanks @AndersonReyes!)
- Update default value for `staging_prefix` in the `DatabricksPySparkStepLauncher` configuration to be an absolute path (Thanks @sd2k!)
- Improve error message shown when Databricks logs can't be retrieved (Thanks @sd2k!)
- Fix errors in documentation fo `input_hydration_config` (Thanks @joeyfreund!)

# 0.8.4

**Bugfix**

- Reverted changed in 0.8.3 that caused error during run launch in certain circumstances
- Updated partition graphs on schedule page to select most recent run
- Forced reload of partitions for partition sets to ensure not serving stale data

**New**

- Added reload button to dagit to reload current repository
- Added option to wipe a single asset key by using `dagster asset wipe <asset_key>`
- Simplified schedule page, removing ticks table, adding tags for last tick attempt
- Better debugging tools for launch errors

# 0.8.3

**Breaking Changes**

- Previously, the `gcs_resource` returned a `GCSResource` wrapper which had a single `client` property that returned a `google.cloud.storage.client.Client`. Now, the `gcs_resource` returns the client directly.

  To update solids that use the `gcp_resource`, change:

  ```
  context.resources.gcs.client
  ```

  To:

  ```
  context.resources.gcs
  ```

**New**

- Introduced a new Python API `reexecute_pipeline` to reexecute an existing pipeline run.
- Performance improvements in Pipeline Overview and other pages.
- Long metadata entries in the asset details view are now scrollable.
- Added a `project` field to the `gcs_resource` in `dagster_gcp`.
- Added new CLI command `dagster asset wipe` to remove all existing asset keys.

**Bugfix**

- Several Dagit bugfixes and performance improvements
- Fixes pipeline execution issue with custom run launchers that call `executeRunInProcess`.
- Updates `dagster schedule up` output to be repository location scoped

# 0.8.2

**Bugfix**

- Fixes issues with `dagster instance migrate`.
- Fixes bug in `launch_scheduled_execution` that would mask configuration errors.
- Fixes bug in dagit where schedule related errors were not shown.
- Fixes JSON-serialization error in `dagster-k8s` when specifying per-step resources.

**New**

- Makes `label` optional parameter for materializations with `asset_key` specified.
- Changes `Assets` page to have a typeahead selector and hierarchical views based on asset_key path.
- _dagster-ssh_
  - adds SFTP get and put functions to `SSHResource`, replacing sftp_solid.

**Docs**

- Various docs corrections

# 0.8.1

**Bugfix**

- Fixed a file descriptor leak that caused `OSError: [Errno 24] Too many open files` when enough
  temporary files were created.
- Fixed an issue where an empty config in the Playground would unexpectedly be marked as invalid
  YAML.
- Removed "config" deprecation warnings for dask and celery executors.

**New**

- Improved performance of the Assets page.

# 0.8.0 "In The Zone"

**Major Changes**

Please see the `080_MIGRATION.md` migration guide for details on updating existing code to be
compatible with 0.8.0

- _Workspace, host and user process separation, and repository definition_ Dagit and other tools no
  longer load a single repository containing user definitions such as pipelines into the same
  process as the framework code. Instead, they load a "workspace" that can contain multiple
  repositories sourced from a variety of different external locations (e.g., Python modules and
  Python virtualenvs, with containers and source control repositories soon to come).

  The repositories in a workspace are loaded into their own "user" processes distinct from the
  "host" framework process. Dagit and other tools now communicate with user code over an IPC
  mechanism. This architectural change has a couple of advantages:

  - Dagit no longer needs to be restarted when there is an update to user code.
  - Users can use repositories to organize their pipelines, but still work on all of their
    repositories using a single running Dagit.
  - The Dagit process can now run in a separate Python environment from user code so pipeline
    dependencies do not need to be installed into the Dagit environment.
  - Each repository can be sourced from a separate Python virtualenv, so teams can manage their
    dependencies (or even their own Python versions) separately.

  We have introduced a new file format, `workspace.yaml`, in order to support this new architecture.
  The workspace yaml encodes what repositories to load and their location, and supersedes the
  `repository.yaml` file and associated machinery.

  As a consequence, Dagster internals are now stricter about how pipelines are loaded. If you have
  written scripts or tests in which a pipeline is defined and then passed across a process boundary
  (e.g., using the `multiprocess_executor` or dagstermill), you may now need to wrap the pipeline
  in the `reconstructable` utility function for it to be reconstructed across the process boundary.

  In addition, rather than instantiate the `RepositoryDefinition` class directly, users should now
  prefer the `@repository` decorator. As part of this change, the `@scheduler` and
  `@repository_partitions` decorators have been removed, and their functionality subsumed under
  `@repository`.

* _Dagit organization_ The Dagit interface has changed substantially and is now oriented around
  pipelines. Within the context of each pipeline in an environment, the previous "Pipelines" and
  "Solids" tabs have been collapsed into the "Definition" tab; a new "Overview" tab provides
  summary information about the pipeline, its schedules, its assets, and recent runs; the previous
  "Playground" tab has been moved within the context of an individual pipeline. Related runs (e.g.,
  runs created by re-executing subsets of previous runs) are now grouped together in the Playground
  for easy reference. Dagit also now includes more advanced support for display of scheduled runs
  that may not have executed ("schedule ticks"), as well as longitudinal views over scheduled runs,
  and asset-oriented views of historical pipeline runs.

* _Assets_ Assets are named materializations that can be generated by your pipeline solids, which
  support specialized views in Dagit. For example, if we represent a database table with an asset
  key, we can now index all of the pipelines and pipeline runs that materialize that table, and
  view them in a single place. To use the asset system, you must enable an asset-aware storage such
  as Postgres.

* _Run launchers_ The distinction between "starting" and "launching" a run has been effaced. All
  pipeline runs instigated through Dagit now make use of the `RunLauncher` configured on the
  Dagster instance, if one is configured. Additionally, run launchers can now support termination of
  previously launched runs. If you have written your own run launcher, you may want to update it to
  support termination. Note also that as of 0.7.9, the semantics of `RunLauncher.launch_run` have
  changed; this method now takes the `run_id` of an existing run and should no longer attempt to
  create the run in the instance.

* _Flexible reexecution_ Pipeline re-execution from Dagit is now fully flexible. You may
  re-execute arbitrary subsets of a pipeline's execution steps, and the re-execution now appears
  in the interface as a child run of the original execution.

* _Support for historical runs_ Snapshots of pipelines and other Dagster objects are now persisted
  along with pipeline runs, so that historial runs can be loaded for review with the correct
  execution plans even when pipeline code has changed. This prepares the system to be able to diff
  pipeline runs and other objects against each other.

* _Step launchers and expanded support for PySpark on EMR and Databricks_ We've introduced a new
  `StepLauncher` abstraction that uses the resource system to allow individual execution steps to
  be run in separate processes (and thus on separate execution substrates). This has made extensive
  improvements to our PySpark support possible, including the option to execute individual PySpark
  steps on EMR using the `EmrPySparkStepLauncher` and on Databricks using the
  `DatabricksPySparkStepLauncher` The `emr_pyspark` example demonstrates how to use a step launcher.

* _Clearer names_ What was previously known as the environment dictionary is now called the
  `run_config`, and the previous `environment_dict` argument to APIs such as `execute_pipeline` is
  now deprecated. We renamed this argument to focus attention on the configuration of the run
  being launched or executed, rather than on an ambiguous "environment". We've also renamed the
  `config` argument to all use definitions to be `config_schema`, which should reduce ambiguity
  between the configuration schema and the value being passed in some particular case. We've also
  consolidated and improved documentation of the valid types for a config schema.

* _Lakehouse_ We're pleased to introduce Lakehouse, an experimental, alternative programming model
  for data applications, built on top of Dagster core. Lakehouse allows developers to define data
  applications in terms of data assets, such as database tables or ML models, rather than in terms
  of the computations that produce those assets. The `simple_lakehouse` example gives a taste of
  what it's like to program in Lakehouse. We'd love feedback on whether this model is helpful!

* _Airflow ingest_ We've expanded the tooling available to teams with existing Airflow installations
  that are interested in incrementally adopting Dagster. Previously, we provided only injection
  tools that allowed developers to write Dagster pipelines and then compile them into Airflow DAGs
  for execution. We've now added ingestion tools that allow teams to move to Dagster for execution
  without having to rewrite all of their legacy pipelines in Dagster. In this approach, Airflow
  DAGs are kept in their own container/environment, compiled into Dagster pipelines, and run via
  the Dagster orchestrator. See the `airflow_ingest` example for details!

**Breaking Changes**

- _dagster_

  - The `@scheduler` and `@repository_partitions` decorators have been removed. Instances of
    `ScheduleDefinition` and `PartitionSetDefinition` belonging to a repository should be specified
    using the `@repository` decorator instead.
  - Support for the Dagster solid selection DSL, previously introduced in Dagit, is now uniform
    throughout the Python codebase, with the previous `solid_subset` arguments (`--solid-subset` in
    the CLI) being replaced by `solid_selection` (`--solid-selection`). In addition to the names of
    individual solids, this argument now supports selection queries like `*solid_name++` (i.e.,
    `solid_name`, all of its ancestors, its immediate descendants, and their immediate descendants).
  - The built-in Dagster type `Path` has been removed.
  - `PartitionSetDefinition` names, including those defined by a `PartitionScheduleDefinition`,
    must now be unique within a single repository.
  - Asset keys are now sanitized for non-alphanumeric characters. All characters besides
    alphanumerics and `_` are treated as path delimiters. Asset keys can also be specified using
    `AssetKey`, which accepts a list of strings as an explicit path. If you are running 0.7.10 or
    later and using assets, you may need to migrate your historical event log data for asset keys
    from previous runs to be attributed correctly. This `event_log` data migration can be invoked
    as follows:

    ```python
    from dagster.core.storage.event_log.migration import migrate_event_log_data
    from dagster import DagsterInstance

    migrate_event_log_data(instance=DagsterInstance.get())
    ```

  - The interface of the `Scheduler` base class has changed substantially. If you've written a
    custom scheduler, please get in touch!
  - The partitioned schedule decorators now generate `PartitionSetDefinition` names using
    the schedule name, suffixed with `_partitions`.
  - The `repository` property on `ScheduleExecutionContext` is no longer available. If you were
    using this property to pass to `Scheduler` instance methods, this interface has changed
    significantly. Please see the `Scheduler` class documentation for details.
  - The CLI option `--celery-base-priority` is no longer available for the command:
    `dagster pipeline backfill`. Use the tags option to specify the celery priority, (e.g.
    `dagster pipeline backfill my_pipeline --tags '{ "dagster-celery/run_priority": 3 }'`
  - The `execute_partition_set` API has been removed.
  - The deprecated `is_optional` parameter to `Field` and `OutputDefinition` has been removed.
    Use `is_required` instead.
  - The deprecated `runtime_type` property on `InputDefinition` and `OutputDefinition` has been
    removed. Use `dagster_type` instead.
  - The deprecated `has_runtime_type`, `runtime_type_named`, and `all_runtime_types` methods on
    `PipelineDefinition` have been removed. Use `has_dagster_type`, `dagster_type_named`, and
    `all_dagster_types` instead.
  - The deprecated `all_runtime_types` method on `SolidDefinition` and `CompositeSolidDefinition`
    has been removed. Use `all_dagster_types` instead.
  - The deprecated `metadata` argument to `SolidDefinition` and `@solid` has been removed. Use
    `tags` instead.
  - The graphviz-based DAG visualization in Dagster core has been removed. Please use Dagit!

- _dagit_

  - `dagit-cli` has been removed, and `dagit` is now the only console entrypoint.

- _dagster-aws_

  - The AWS CLI has been removed.
  - `dagster_aws.EmrRunJobFlowSolidDefinition` has been removed.

- _dagster-bash_

  - This package has been renamed to dagster-shell. The`bash_command_solid` and `bash_script_solid`
    solid factory functions have been renamed to `create_shell_command_solid` and
    `create_shell_script_solid`.

- _dagster-celery_

  - The CLI option `--celery-base-priority` is no longer available for the command:
    `dagster pipeline backfill`. Use the tags option to specify the celery priority, (e.g.
    `dagster pipeline backfill my_pipeline --tags '{ "dagster-celery/run_priority": 3 }'`

- _dagster-dask_

  - The config schema for the `dagster_dask.dask_executor` has changed. The previous config should
    now be nested under the key `local`.

- _dagster-gcp_

  - The `BigQueryClient` has been removed. Use `bigquery_resource` instead.

- _dagster-dbt_

  - The dagster-dbt package has been removed. This was inadequate as a reference integration, and
    will be replaced in 0.8.x.

- _dagster-spark_

  - `dagster_spark.SparkSolidDefinition` has been removed - use `create_spark_solid` instead.
  - The `SparkRDD` Dagster type, which only worked with an in-memory engine, has been removed.

- _dagster-twilio_

  - The `TwilioClient` has been removed. Use `twilio_resource` instead.

**New**

- _dagster_

  - You may now set `asset_key` on any `Materialization` to use the new asset system. You will also
    need to configure an asset-aware storage, such as Postgres. The `longitudinal_pipeline` example
    demonstrates this system.
  - The partitioned schedule decorators now support an optional `end_time`.
  - Opt-in telemetry now reports the Python version being used.

- _dagit_

  - Dagit's GraphQL playground is now available at `/graphiql` as well as at `/graphql`.

- _dagster-aws_

  - The `dagster_aws.S3ComputeLogManager` may now be configured to override the S3 endpoint and
    associated SSL settings.
  - Config string and integer values in the S3 tooling may now be set using either environment
    variables or literals.

- _dagster-azure_

  - We've added the dagster-azure package, with support for Azure Data Lake Storage Gen2; you can
    use the `adls2_system_storage` or, for direct access, the `adls2_resource` resource. (Thanks
    @sd2k!)

- _dagster-dask_

  - Dask clusters are now supported by `dagster_dask.dask_executor`. For full support, you will need
    to install extras with `pip install dagster-dask[yarn, pbs, kube]`. (Thanks @DavidKatz-il!)

- _dagster-databricks_

  - We've added the dagster-databricks package, with support for running PySpark steps on Databricks
    clusters through the `databricks_pyspark_step_launcher`. (Thanks @sd2k!)

- _dagster-gcp_

  - Config string and integer values in the BigQuery, Dataproc, and GCS tooling may now be set
    using either environment variables or literals.

- _dagster-k8s_

  - Added the `CeleryK8sRunLauncher` to submit execution plan steps to Celery task queues for
    execution as k8s Jobs.
  - Added the ability to specify resource limits on a per-pipeline and per-step basis for k8s Jobs.
  - Many improvements and bug fixes to the dagster-k8s Helm chart.

- _dagster-pandas_

  - Config string and integer values in the dagster-pandas input and output schemas may now be set
    using either environment variables or literals.

- _dagster-papertrail_

  - Config string and integer values in the `papertrail_logger` may now be set using either
    environment variables or literals.

- _dagster-pyspark_

  - PySpark solids can now run on EMR, using the `emr_pyspark_step_launcher`, or on Databricks using
    the new dagster-databricks package. The `emr_pyspark` example demonstrates how to use a step
    launcher.

- _dagster-snowflake_

  - Config string and integer values in the `snowflake_resource` may now be set using either
    environment variables or literals.

- _dagster-spark_

  - `dagster_spark.create_spark_solid` now accepts a `required_resource_keys` argument, which
    enables setting up a step launcher for Spark solids, like the `emr_pyspark_step_launcher`.

**Bugfix**

- `dagster pipeline execute` now sets a non-zero exit code when pipeline execution fails.

# 0.7.16

**Bugfix**

- Enabled `NoOpComputeLogManager` to be configured as the `compute_logs` implementation in
  `dagster.yaml`
- Suppressed noisy error messages in logs from skipped steps

# 0.7.15

**New**

- Improve dagster scheduler state reconciliation.

# 0.7.14

**New**

- Dagit now allows re-executing arbitrary step subset via step selector syntax, regardless of
  whether the previous pipeline failed or not.
- Added a search filter for the root Assets page
- Adds tooltip explanations for disabled run actions
- The last output of the cron job command created by the scheduler is now stored in a file. A new
  `dagster schedule logs {schedule_name}` command will show the log file for a given schedule. This
  helps uncover errors like missing environment variables and import errors.
- The Dagit schedule page will now show inconsistency errors between schedule state and the cron
  tab that were previously only displayed by the `dagster schedule debug` command. As before, these
  errors can be resolve using `dagster schedule up`

**Bugfix**

- Fixes an issue with config schema validation on Arrays
- Fixes an issue with initializing K8sRunLauncher when configured via `dagster.yaml`
- Fixes a race condition in Airflow injection logic that happens when multiple Operators try to
  create PipelineRun entries simultaneously.
- Fixed an issue with schedules that had invalid config not logging the appropriate error.

# 0.7.13

**Breaking Changes**

- `dagster pipeline backfill` command no longer takes a `mode` flag. Instead, it uses the mode
  specified on the `PartitionSetDefinition`. Similarly, the runs created from the backfill also use
  the `solid_subset` specified on the `PartitionSetDefinition`

**BugFix**

- Fixes a bug where using solid subsets when launching pipeline runs would fail config validation.
- (dagster-gcp) allow multiple "bq_solid_for_queries" solids to co-exist in a pipeline
- Improve scheduler state reconciliation with dagster-cron scheduler. `dagster schedule` debug
  command will display issues related to missing crob jobs, extraneous cron jobs, and duplicate cron
  jobs. Running `dagster schedule up` will fix any issues.

**New**

- The dagster-airflow package now supports loading Airflow dags without depending on initialized
  Airflow db
- Improvements to the longitudinal partitioned schedule view, including live updates, run filtering,
  and better default states.
- Added user warning for dagster library packages that are out of sync with the core `dagster`
  package.

# 0.7.12

**Bugfix**

- We now only render the subset of an execution plan that has actually executed, and persist that
  subset information along with the snapshot.
- @pipeline and @composite_solid now correctly capture `__doc__` from the function they decorate.
- Fixed a bug with using solid subsets in the Dagit playground

# 0.7.11

**Bugfix**

- Fixed an issue with strict snapshot ID matching when loading historical snapshots, which caused
  errors on the Runs page when viewing historical runs.
- Fixed an issue where `dagster_celery` had introduced a spurious dependency on `dagster_k8s`
  (#2435)
- Fixed an issue where our Airflow, Celery, and Dask integrations required S3 or GCS storage and
  prevented use of filesystem storage. Filesystem storage is now also permitted, to enable use of
  these integrations with distributed filesystems like NFS (#2436).

# 0.7.10

**New**

- `RepositoryDefinition` now takes `schedule_defs` and `partition_set_defs` directly. The loading
  scheme for these definitions via `repository.yaml` under the `scheduler:` and `partitions:` keys
  is deprecated and expected to be removed in 0.8.0.
- Mark published modules as python 3.8 compatible.
- The dagster-airflow package supports loading all Airflow DAGs within a directory path, file path,
  or Airflow DagBag.
- The dagster-airflow package supports loading all 23 DAGs in Airflow example_dags folder and
  execution of 17 of them (see: `make_dagster_repo_from_airflow_example_dags`).
- The dagster-celery CLI tools now allow you to pass additional arguments through to the underlying
  celery CLI, e.g., running `dagster-celery worker start -n my-worker -- --uid=42` will pass the
  `--uid` flag to celery.
- It is now possible to create a `PresetDefinition` that has no environment defined.
- Added `dagster schedule debug` command to help debug scheduler state.
- The `SystemCronScheduler` now verifies that a cron job has been successfully been added to the
  crontab when turning a schedule on, and shows an error message if unsuccessful.

**Breaking Changes**

- A `dagster instance migrate` is required for this release to support the new experimental assets
  view.
- Runs created prior to 0.7.8 will no longer render their execution plans as DAGs. We are only
  rendering execution plans that have been persisted. Logs are still available.
- `Path` is no longer valid in config schemas. Use `str` or `dagster.String` instead.
- Removed the `@pyspark_solid` decorator - its functionality, which was experimental, is subsumed by
  requiring a StepLauncher resource (e.g. emr_pyspark_step_launcher) on the solid.

**Dagit**

- Merged "re-execute", "single-step re-execute", "resume/retry" buttons into one "re-execute" button
  with three dropdown selections on the Run page.

**Experimental**

- Added new `asset_key` string parameter to Materializations and created a new “Assets” tab in Dagit
  to view pipelines and runs associated with these keys. The API and UI of these asset-based are
  likely to change, but feedback is welcome and will be used to inform these changes.
- Added an `emr_pyspark_step_launcher` that enables launching PySpark solids in EMR. The
  "simple_pyspark" example demonstrates how it’s used.

**Bugfix**

- Fixed an issue when running Jupyter notebooks in a Python 2 kernel through dagstermill with
  Dagster running in Python 3.
- Improved error messages produced when dagstermill spins up an in-notebook context.
- Fixed an issue with retrieving step events from `CompositeSolidResult` objects.

# 0.7.9

**Breaking Changes**

- If you are launching runs using `DagsterInstance.launch_run`, this method now takes a run id
  instead of an instance of `PipelineRun`. Additionally, `DagsterInstance.create_run` and
  `DagsterInstance.create_empty_run` have been replaced by `DagsterInstance.get_or_create_run` and
  `DagsterInstance.create_run_for_pipeline`.
- If you have implemented your own `RunLauncher`, there are two required changes:
  - `RunLauncher.launch_run` takes a pipeline run that has already been created. You should remove
    any calls to `instance.create_run` in this method.
  - Instead of calling `startPipelineExecution` (defined in the
    `dagster_graphql.client.query.START_PIPELINE_EXECUTION_MUTATION`) in the run launcher, you
    should call `startPipelineExecutionForCreatedRun` (defined in
    `dagster_graphql.client.query.START_PIPELINE_EXECUTION_FOR_CREATED_RUN_MUTATION`).
  - Refer to the `RemoteDagitRunLauncher` for an example implementation.

**New**

- Improvements to preset and solid subselection in the playground. An inline preview of the pipeline
  instead of a modal when doing subselection, and the correct subselection is chosen when selecting
  a preset.
- Improvements to the log searching. Tokenization and autocompletion for searching messages types
  and for specific steps.
- You can now view the structure of pipelines from historical runs, even if that pipeline no longer
  exists in the loaded repository or has changed structure.
- Historical execution plans are now viewable, even if the pipeline has changed structure.
- Added metadata link to raw compute logs for all StepStart events in PipelineRun view and Step
  view.
- Improved error handling for the scheduler. If a scheduled run has config errors, the errors are
  persisted to the event log for the run and can be viewed in Dagit.

**Bugfix**

- No longer manually dispose sqlalchemy engine in dagster-postgres
- Made boto3 dependency in dagster-aws more flexible (#2418)
- Fixed tooltip UI cleanup in partitioned schedule view

**Documentation**

- Brand new documentation site, available at https://docs.dagster.io
- The tutorial has been restructured to multiple sections, and the examples in intro_tutorial have
  been rearranged to separate folders to reflect this.

# 0.7.8

**Breaking Changes**

- The `execute_pipeline_with_mode` and `execute_pipeline_with_preset` APIs have been dropped in
  favor of new top level arguments to `execute_pipeline`, `mode` and `preset`.
- The use of `RunConfig` to pass options to `execute_pipeline` has been deprecated, and `RunConfig`
  will be removed in 0.8.0.
- The `execute_solid_within_pipeline` and `execute_solids_within_pipeline` APIs, intended to support
  tests, now take new top level arguments `mode` and `preset`.

**New**

- The dagster-aws Redshift resource now supports providing an error callback to debug failed
  queries.
- We now persist serialized execution plans for historical runs. They will render correctly even if
  the pipeline structure has changed or if it does not exist in the current loaded repository.
- Clicking on a pipeline tag in the `Runs` view will apply that tag as a filter.

**Bugfix**

- Fixed a bug where telemetry logger would create a log file (but not write any logs) even when
  telemetry was disabled.

**Experimental**

- The dagster-airflow package supports ingesting Airflow dags and running them as dagster pipelines
  (see: `make_dagster_pipeline_from_airflow_dag`). This is in the early experimentation phase.
- Improved the layout of the experimental partition runs table on the `Schedules` detailed view.

**Documentation**

- Fixed a grammatical error (Thanks @flowersw!)

# 0.7.7

**Breaking Changes**

- The default sqlite and `dagster-postgres` implementations have been altered to extract the
  event `step_key` field as a column, to enable faster per-step queries. You will need to run
  `dagster instance migrate` to update the schema. You may optionally migrate your historical event
  log data to extract the `step_key` using the `migrate_event_log_data` function. This will ensure
  that your historical event log data will be captured in future step-key based views. This
  `event_log` data migration can be invoked as follows:

  ```python
  from dagster.core.storage.event_log.migration import migrate_event_log_data
  from dagster import DagsterInstance

  migrate_event_log_data(instance=DagsterInstance.get())
  ```

- We have made pipeline metadata serializable and persist that along with run information.
  While there are no user-facing features to leverage this yet, it does require an instance
  migration. Run `dagster instance migrate`. If you have already run the migration for the
  `event_log` changes above, you do not need to run it again. Any unforeseen errors related to the
  new `snapshot_id` in the `runs` table or the new `snapshots` table are related to this migration.
- dagster-pandas `ColumnTypeConstraint` has been removed in favor of `ColumnDTypeFnConstraint` and
  `ColumnDTypeInSetConstraint`.

**New**

- You can now specify that dagstermill output notebooks be yielded as an output from dagstermill
  solids, in addition to being materialized.
- You may now set the extension on files created using the `FileManager` machinery.
- dagster-pandas typed `PandasColumn` constructors now support pandas 1.0 dtypes.
- The Dagit Playground has been restructured to make the relationship between Preset, Partition
  Sets, Modes, and subsets more clear. All of these buttons have be reconciled and moved to the
  left side of the Playground.
- Config sections that are required but not filled out in the Dagit playground are now detected
  and labeled in orange.
- dagster-celery config now support using `env:` to load from environment variables.

**Bugfix**

- Fixed a bug where selecting a preset in `dagit` would not populate tags specified on the pipeline
  definition.
- Fixed a bug where metadata attached to a raised `Failure` was not displayed in the error modal in
  `dagit`.
- Fixed an issue where reimporting dagstermill and calling `dagstermill.get_context()` outside of
  the parameters cell of a dagstermill notebook could lead to unexpected behavior.
- Fixed an issue with connection pooling in dagster-postgres, improving responsiveness when using
  the Postgres-backed storages.

**Experimental**

- Added a longitudinal view of runs for on the `Schedule` tab for scheduled, partitioned pipelines.
  Includes views of run status, execution time, and materializations across partitions. The UI is
  in flux and is currently optimized for daily schedules, but feedback is welcome.

# 0.7.6

**Breaking Changes**

- `default_value` in `Field` no longer accepts native instances of python enums. Instead
  the underlying string representation in the config system must be used.
- `default_value` in `Field` no longer accepts callables.
- The `dagster_aws` imports have been reorganized; you should now import resources from
  `dagster_aws.<AWS service name>`. `dagster_aws` provides `s3`, `emr`, `redshift`, and `cloudwatch`
  modules.
- The `dagster_aws` S3 resource no longer attempts to model the underlying boto3 API, and you can
  now just use any boto3 S3 API directly on a S3 resource, e.g.
  `context.resources.s3.list_objects_v2`. (#2292)

**New**

- New `Playground` view in `dagit` showing an interactive config map
- Improved storage and UI for showing schedule attempts
- Added the ability to set default values in `InputDefinition`
- Added CLI command `dagster pipeline launch` to launch runs using a configured `RunLauncher`
- Added ability to specify pipeline run tags using the CLI
- Added a `pdb` utility to `SolidExecutionContext` to help with debugging, available within a solid
  as `context.pdb`
- Added `PresetDefinition.with_additional_config` to allow for config overrides
- Added resource name to log messages generated during resource initialization
- Added grouping tags for runs that have been retried / reexecuted.

**Bugfix**

- Fixed a bug where date range partitions with a specified end date was clipping the last day
- Fixed an issue where some schedule attempts that failed to start would be marked running forever.
- Fixed the `@weekly` partitioned schedule decorator
- Fixed timezone inconsistencies between the runs view and the schedules view
- Integers are now accepted as valid values for Float config fields
- Fixed an issue when executing dagstermill solids with config that contained quote characters.

**dagstermill**

- The Jupyter kernel to use may now be specified when creating dagster notebooks with the `--kernel`
  flag.

**dagster-dbt**

- `dbt_solid` now has a `Nothing` input to allow for sequencing

**dagster-k8s**

- Added `get_celery_engine_config` to select celery engine, leveraging Celery infrastructure

**Documentation**

- Improvements to the airline and bay bikes demos
- Improvements to our dask deployment docs (Thanks jswaney!!)

# 0.7.5

**New**

- Added the `IntSource` type, which lets integers be set from environment variables in config.
- You may now set tags on pipeline definitions. These will resolve in the following cases:

  1. Loading in the playground view in Dagit will pre-populate the tag container.
  2. Loading partition sets from the preset/config picker will pre-populate the tag container with
     the union of pipeline tags and partition tags, with partition tags taking precedence.
  3. Executing from the CLI will generate runs with the pipeline tags.
  4. Executing programmatically using the `execute_pipeline` api will create a run with the union
     of pipeline tags and `RunConfig` tags, with `RunConfig` tags taking precedence.
  5. Scheduled runs (both launched and executed) will have the union of pipeline tags and the
     schedule tags function, with the schedule tags taking precedence.

- Output materialization configs may now yield multiple Materializations, and the tutorial has
  been updated to reflect this.

- We now export the `SolidExecutionContext` in the public API so that users can correctly type hint
  solid compute functions.

**Dagit**

- Pipeline run tags are now preserved when resuming/retrying from Dagit.
- Scheduled run stats are now grouped by partition.
- A "preparing" section has been added to the execution viewer. This shows steps that are in
  progress of starting execution.
- Markers emitted by the underlying execution engines are now visualized in the Dagit execution
  timeline.

**Bugfix**

- Resume/retry now works as expected in the presence of solids that yield optional outputs.
- Fixed an issue where dagster-celery workers were failing to start in the presence of config
  values that were `None`.
- Fixed an issue with attempting to set `threads_per_worker` on Dask distributed clusters.

**dagster-postgres**

- All postgres config may now be set using environment variables in config.

**dagster-aws**

- The `s3_resource` now exposes a `list_objects_v2` method corresponding to the underlying boto3
  API. (Thanks, @basilvetas!)
- Added the `redshift_resource` to access Redshift databases.

**dagster-k8s**

- The `K8sRunLauncher` config now includes the `load_kubeconfig` and `kubeconfig_file` options.

**Documentation**

- Fixes and improvements.

**Dependencies**

- dagster-airflow no longer pins its werkzeug dependency.

**Community**

- We've added opt-in telemetry to Dagster so we can collect usage statistics in order to inform
  development priorities. Telemetry data will motivate projects such as adding features in
  frequently-used parts of the CLI and adding more examples in the docs in areas where users
  encounter more errors.

  We will not see or store solid definitions (including generated context) or pipeline definitions
  (including modes and resources). We will not see or store any data that is processed within solids
  and pipelines.

  If you'd like to opt in to telemetry, please add the following to `$DAGSTER_HOME/dagster.yaml`:

      telemetry:
        enabled: true

- Thanks to @basilvetas and @hspak for their contributions!

# 0.7.4

**New**

- It is now possible to use Postgres to back schedule storage by configuring
  `dagster_postgres.PostgresScheduleStorage` on the instance.
- Added the `execute_pipeline_with_mode` API to allow executing a pipeline in test with a specific
  mode without having to specify `RunConfig`.
- Experimental support for retries in the Celery executor.
- It is now possible to set run-level priorities for backfills run using the Celery executor by
  passing `--celery-base-priority` to `dagster pipeline backfill`.
- Added the `@weekly` schedule decorator.

**Deprecations**

- The `dagster-ge` library has been removed from this release due to drift from the underlying
  Great Expectations implementation.

**dagster-pandas**

- `PandasColumn` now includes an `is_optional` flag, replacing the previous
  `ColumnExistsConstraint`.
- You can now pass the `ignore_missing_values flag` to `PandasColumn` in order to apply column
  constraints only to the non-missing rows in a column.

**dagster-k8s**

- The Helm chart now includes provision for an Ingress and for multiple Celery queues.

**Documentation**

- Improvements and fixes.

# 0.7.3

**New**

- It is now possible to configure a Dagit instance to disable executing pipeline runs in a local
  subprocess.
- Resource initialization, teardown, and associated failure states now emit structured events
  visible in Dagit. Structured events for pipeline errors and multiprocess execution have been
  consolidated and rationalized.
- Support Redis queue provider in `dagster-k8s` Helm chart.
- Support external postgresql in `dagster-k8s` Helm chart.

**Bugfix**

- Fixed an issue with inaccurate timings on some resource initializations.
- Fixed an issue that could cause the multiprocess engine to spin forever.
- Fixed an issue with default value resolution when a config value was set using `SourceString`.
- Fixed an issue when loading logs from a pipeline belonging to a different repository in Dagit.
- Fixed an issue with where the CLI command `dagster schedule up` would fail in certain scenarios
  with the `SystemCronScheduler`.

**Pandas**

- Column constraints can now be configured to permit NaN values.

**Dagstermill**

- Removed a spurious dependency on sklearn.

**Docs**

- Improvements and fixes to docs.
- Restored dagster.readthedocs.io.

**Experimental**

- An initial implementation of solid retries, throwing a `RetryRequested` exception, was added.
  This API is experimental and likely to change.

**Other**

- Renamed property `runtime_type` to `dagster_type` in definitions. The following are deprecated
  and will be removed in a future version.
  - `InputDefinition.runtime_type` is deprecated. Use `InputDefinition.dagster_type` instead.
  - `OutputDefinition.runtime_type` is deprecated. Use `OutputDefinition.dagster_type` instead.
  - `CompositeSolidDefinition.all_runtime_types` is deprecated. Use
    `CompositeSolidDefinition.all_dagster_types` instead.
  - `SolidDefinition.all_runtime_types` is deprecated. Use `SolidDefinition.all_dagster_types`
    instead.
  - `PipelineDefinition.has_runtime_type` is deprecated. Use `PipelineDefinition.has_dagster_type`
    instead.
  - `PipelineDefinition.runtime_type_named` is deprecated. Use
    `PipelineDefinition.dagster_type_named` instead.
  - `PipelineDefinition.all_runtime_types` is deprecated. Use
    `PipelineDefinition.all_dagster_types` instead.

# 0.7.2

**Docs**

- New docs site at docs.dagster.io.
- dagster.readthedocs.io is currently stale due to availability issues.

**New**

- Improvements to S3 Resource. (Thanks @dwallace0723!)
- Better error messages in Dagit.
- Better font/styling support in Dagit.
- Changed `OutputDefinition` to take `is_required` rather than `is_optional` argument. This is to
  remain consistent with changes to `Field` in 0.7.1 and to avoid confusion
  with python's typing and dagster's definition of `Optional`, which indicates None-ability,
  rather than existence. `is_optional` is deprecated and will be removed in a future version.
- Added support for Flower in dagster-k8s.
- Added support for environment variable config in dagster-snowflake.

**Bugfixes**

- Improved performance in Dagit waterfall view.
- Fixed bug when executing solids downstream of a skipped solid.
- Improved navigation experience for pipelines in Dagit.
- Fixed for the dagster-aws CLI tool.
- Fixed issue starting Dagit without DAGSTER_HOME set on windows.
- Fixed pipeline subset execution in partition-based schedules.

# 0.7.1

**Dagit**

- Dagit now looks up an available port on which to run when the default port is
  not available. (Thanks @rparrapy!)

**dagster_pandas**

- Hydration and materialization are now configurable on `dagster_pandas` dataframes.

**dagster_aws**

- The `s3_resource` no longer uses an unsigned session by default.

**Bugfixes**

- Type check messages are now displayed in Dagit.
- Failure metadata is now surfaced in Dagit.
- Dagit now correctly displays the execution time of steps that error.
- Error messages now appear correctly in console logging.
- GCS storage is now more robust to transient failures.
- Fixed an issue where some event logs could be duplicated in Dagit.
- Fixed an issue when reading config from an environment variable that wasn't set.
- Fixed an issue when loading a repository or pipeline from a file target on Windows.
- Fixed an issue where deleted runs could cause the scheduler page to crash in Dagit.

**Documentation**

- Expanded and improved docs and error messages.

# 0.7.0 "Waiting to Exhale"

**Breaking Changes**

There are a substantial number of breaking changes in the 0.7.0 release.
Please see `070_MIGRATION.md` for instructions regarding migrating old code.

**_Scheduler_**

- The scheduler configuration has been moved from the `@schedules` decorator to `DagsterInstance`.
  Existing schedules that have been running are no longer compatible with current storage. To
  migrate, remove the `scheduler` argument on all `@schedules` decorators:

  instead of:

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

  Next, configure the scheduler on your instance by adding the following to
  `$DAGSTER_HOME/dagster.yaml`:

  ```
  scheduler:
    module: dagster_cron.cron_scheduler
    class: SystemCronScheduler
  ```

  Finally, if you had any existing schedules running, delete the existing `$DAGSTER_HOME/schedules`
  directory and run `dagster schedule wipe && dagster schedule up` to re-instatiate schedules in a
  valid state.

- The `should_execute` and `environment_dict_fn` argument to `ScheduleDefinition` now have a
  required first argument `context`, representing the `ScheduleExecutionContext`

**_Config System Changes_**

- In the config system, `Dict` has been renamed to `Shape`; `List` to `Array`; `Optional` to
  `Noneable`; and `PermissiveDict` to `Permissive`. The motivation here is to clearly delineate
  config use cases versus cases where you are using types as the inputs and outputs of solids as
  well as python typing types (for mypy and friends). We believe this will be clearer to users in
  addition to simplifying our own implementation and internal abstractions.

  Our recommended fix is _not_ to use `Shape` and `Array`, but instead to use our new condensed
  config specification API. This allow one to use bare dictionaries instead of `Shape`, lists with
  one member instead of `Array`, bare types instead of `Field` with a single argument, and python
  primitive types (`int`, `bool` etc) instead of the dagster equivalents. These result in
  dramatically less verbose config specs in most cases.

  So instead of

  ```
  from dagster import Shape, Field, Int, Array, String
  # ... code
  config=Shape({ # Dict prior to change
        'some_int' : Field(Int),
        'some_list: Field(Array[String]) # List prior to change
    })
  ```

  one can instead write:

  ```
  config={'some_int': int, 'some_list': [str]}
  ```

  No imports and much simpler, cleaner syntax.

- `config_field` is no longer a valid argument on `solid`, `SolidDefinition`, `ExecutorDefintion`,
  `executor`, `LoggerDefinition`, `logger`, `ResourceDefinition`, `resource`, `system_storage`, and
  `SystemStorageDefinition`. Use `config` instead.
- For composite solids, the `config_fn` no longer takes a `ConfigMappingContext`, and the context
  has been deleted. To upgrade, remove the first argument to `config_fn`.

  So instead of

  ```
  @composite_solid(config={}, config_fn=lambda context, config: {})
  ```

  one must instead write:

  ```
  @composite_solid(config={}, config_fn=lambda config: {})
  ```

- `Field` takes a `is_required` rather than a `is_optional` argument. This is to avoid confusion
  with python's typing and dagster's definition of `Optional`, which indicates None-ability,
  rather than existence. `is_optional` is deprecated and will be removed in a future version.

**_Required Resources_**

- All solids, types, and config functions that use a resource must explicitly list that
  resource using the argument `required_resource_keys`. This is to enable efficient
  resource management during pipeline execution, especially in a multiprocessing or
  remote execution environment.

- The `@system_storage` decorator now requires argument `required_resource_keys`, which was
  previously optional.

**_Dagster Type System Changes_**

- `dagster.Set` and `dagster.Tuple` can no longer be used within the config system.
- Dagster types are now instances of `DagsterType`, rather than a class than inherits from
  `RuntimeType`. Instead of dynamically generating a class to create a custom runtime type, just
  create an instance of a `DagsterType`. The type checking function is now an argument to the
  `DagsterType`, rather than an abstract method that has to be implemented in
  a subclass.
- `RuntimeType` has been renamed to `DagsterType` is now an encouraged API for type creation.
- Core type check function of DagsterType can now return a naked `bool` in addition
  to a `TypeCheck` object.
- `type_check_fn` on `DagsterType` (formerly `type_check` and `RuntimeType`, respectively) now
  takes a first argument `context` of type `TypeCheckContext` in addition to the second argument of
  `value`.
- `define_python_dagster_type` has been eliminated in favor of `PythonObjectDagsterType` .
- `dagster_type` has been renamed to `usable_as_dagster_type`.
- `as_dagster_type` has been removed and similar capabilities added as
  `make_python_type_usable_as_dagster_type`.
- `PythonObjectDagsterType` and `usable_as_dagster_type` no longer take a `type_check` argument. If
  a custom type_check is needed, use `DagsterType`.
- As a consequence of these changes, if you were previously using `dagster_pyspark` or
  `dagster_pandas` and expecting Pyspark or Pandas types to work as Dagster types, e.g., in type
  annotations to functions decorated with `@solid` to indicate that they are input or output types
  for a solid, you will need to call `make_python_type_usable_as_dagster_type` from your code in
  order to map the Python types to the Dagster types, or just use the Dagster types
  (`dagster_pandas.DataFrame` instead of `pandas.DataFrame`) directly.

**_Other_**

- We no longer publish base Docker images. Please see the updated deployment docs for an example
  Dockerfile off of which you can work.
- `step_metadata_fn` has been removed from `SolidDefinition` & `@solid`.
- `SolidDefinition` & `@solid` now takes `tags` and enforces that values are strings or
  are safely encoded as JSON. `metadata` is deprecated and will be removed in a future version.
- `resource_mapper_fn` has been removed from `SolidInvocation`.

**New**

- Dagit now includes a much richer execution view, with a Gantt-style visualization of step
  execution and a live timeline.
- Early support for Python 3.8 is now available, and Dagster/Dagit along with many of our libraries
  are now tested against 3.8. Note that several of our upstream dependencies have yet to publish
  wheels for 3.8 on all platforms, so running on Python 3.8 likely still involves building some
  dependencies from source.
- `dagster/priority` tags can now be used to prioritize the order of execution for the built-in
  in-process and multiprocess engines.
- `dagster-postgres` storages can now be configured with separate arguments and environment
  variables, such as:

  ```
  run_storage:
    module: dagster_postgres.run_storage
    class: PostgresRunStorage
    config:
      postgres_db:
        username: test
        password:
          env: ENV_VAR_FOR_PG_PASSWORD
        hostname: localhost
        db_name: test
  ```

- Support for `RunLauncher`s on `DagsterInstance` allows for execution to be "launched" outside of
  the Dagit/Dagster process. As one example, this is used by `dagster-k8s` to submit pipeline
  execution as a Kubernetes Job.
- Added support for adding tags to runs initiated from the `Playground` view in Dagit.
- Added `@monthly_schedule` decorator.
- Added `Enum.from_python_enum` helper to wrap Python enums for config. (Thanks @kdungs!)
- **[dagster-bash]** The Dagster bash solid factory now passes along `kwargs` to the underlying
  solid construction, and now has a single `Nothing` input by default to make it easier to create a
  sequencing dependency. Also, logs are now buffered by default to make execution less noisy.
- **[dagster-aws]** We've improved our EMR support substantially in this release. The
  `dagster_aws.emr` library now provides an `EmrJobRunner` with various utilities for creating EMR
  clusters, submitting jobs, and waiting for jobs/logs. We also now provide a
  `emr_pyspark_resource`, which together with the new `@pyspark_solid` decorator makes moving
  pyspark execution from your laptop to EMR as simple as changing modes.
  **[dagster-pandas]** Added `create_dagster_pandas_dataframe_type`, `PandasColumn`, and
  `Constraint` API's in order for users to create custom types which perform column validation,
  dataframe validation, summary statistics emission, and dataframe serialization/deserialization.
- **[dagster-gcp]** GCS is now supported for system storage, as well as being supported with the
  Dask executor. (Thanks @habibutsu!) Bigquery solids have also been updated to support the new API.

**Bugfix**

- Ensured that all implementations of `RunStorage` clean up pipeline run tags when a run
  is deleted. Requires a storage migration, using `dagster instance migrate`.
- The multiprocess and Celery engines now handle solid subsets correctly.
- The multiprocess and Celery engines will now correctly emit skip events for steps downstream of
  failures and other skips.
- The `@solid` and `@lambda_solid` decorators now correctly wrap their decorated functions, in the
  sense of `functools.wraps`.
- Performance improvements in Dagit when working with runs with large configurations.
- The Helm chart in `dagster_k8s` has been hardened against various failure modes and is now
  compatible with Helm 2.
- SQLite run and event log storages are more robust to concurrent use.
- Improvements to error messages and to handling of user code errors in input hydration and output
  materialization logic.
- Fixed an issue where the Airflow scheduler could hang when attempting to load dagster-airflow
  pipelines.
- We now handle our SQLAlchemy connections in a more canonical way (thanks @zzztimbo!).
- Fixed an issue using S3 system storage with certain custom serialization strategies.
- Fixed an issue leaking orphan processes from compute logging.
- Fixed an issue leaking semaphores from Dagit.
- Setting the `raise_error` flag in `execute_pipeline` now actually raises user exceptions instead
  of a wrapper type.

**Documentation**

- Our docs have been reorganized and expanded (thanks @habibutsu, @vatervonacht, @zzztimbo). We'd
  love feedback and contributions!

**Thank you**
Thank you to all of the community contributors to this release!! In alphabetical order: @habibutsu,
@kdungs, @vatervonacht, @zzztimbo.

# 0.6.9

**Bugfix**

- Improved SQLite concurrency issues, uncovered while using concurrent nodes in Airflow
- Fixed sqlalchemy warnings (thanks @zzztimbo!)
- Fixed Airflow integration issue where a Dagster child process triggered a signal handler of a
  parent Airflow process via a process fork
- Fixed GCS and AWS intermediate store implementations to be compatible with read/write mode
  serialization strategies
- Improve test stability

**Documentation**

- Improved descriptions for setting up the cron scheduler (thanks @zzztimbo!)

# 0.6.8

**New**

- Added the dagster-github library, a community contribution from @Ramshackle-Jamathon and
  @k-mahoney!

**dagster-celery**

- Simplified and improved config handling.
- An engine event is now emitted when the engine fails to connect to a broker.

**Bugfix**

- Fixes a file descriptor leak when running many concurrent dagster-graphql queries (e.g., for
  backfill).
- The `@pyspark_solid` decorator now handles inputs correctly.
- The handling of solid compute functions that accept kwargs but which are decorated with explicit
  input definitions has been rationalized.
- Fixed race conditions in concurrent execution using SQLite event log storage with concurrent
  execution, uncovered by upstream improvements in the Python inotify library we use.

**Documentation**

- Improved error messages when using system storages that don't fulfill executor requirements.

# 0.6.7

**New**

- We are now more permissive when specifying configuration schema in order make constructing
  configuration schema more concise.
- When specifying the value of scalar inputs in config, one can now specify that value directly as
  the key of the input, rather than having to embed it within a `value` key.

**Breaking**

- The implementation of SQL-based event log storages has been consolidated,
  which has entailed a schema change. If you have event logs stored in a
  Postgres- or SQLite-backed event log storage, and you would like to maintain
  access to these logs, you should run `dagster instance migrate`. To check
  what event log storages you are using, run `dagster instance info`.
- Type matches on both sides of an `InputMapping` or `OutputMapping` are now enforced.

**New**

- Dagster is now tested on Python 3.8
- Added the dagster-celery library, which implements a Celery-based engine for parallel pipeline
  execution.
- Added the dagster-k8s library, which includes a Helm chart for a simple Dagit installation on a
  Kubernetes cluster.

**Dagit**

- The Explore UI now allows you to render a subset of a large DAG via a new solid
  query bar that accepts terms like `solid_name+*` and `+solid_name+`. When viewing
  very large DAGs, nothing is displayed by default and `*` produces the original behavior.
- Performance improvements in the Explore UI and config editor for large pipelines.
- The Explore UI now includes a zoom slider that makes it easier to navigate large DAGs.
- Dagit pages now render more gracefully in the presence of inconsistent run storage and event logs.
- Improved handling of GraphQL errors and backend programming errors.
- Minor display improvements.

**dagster-aws**

- A default prefix is now configurable on APIs that use S3.
- S3 APIs now parametrize `region_name` and `endpoint_url`.

**dagster-gcp**

- A default prefix is now configurable on APIs that use GCS.

**dagster-postgres**

- Performance improvements for Postgres-backed storages.

**dagster-pyspark**

- Pyspark sessions may now be configured to be held open after pipeline execution completes, to
  enable extended test cases.

**dagster-spark**

- `spark_outputs` must now be specified when initializing a `SparkSolidDefinition`, rather than in
  config.
- Added new `create_spark_solid` helper and new `spark_resource`.
- Improved EMR implementation.

**Bugfix**

- Fixed an issue retrieving output values using `SolidExecutionResult` (e.g., in test) for
  dagster-pyspark solids.
- Fixes an issue when expanding composite solids in Dagit.
- Better errors when solid names collide.
- Config mapping in composite solids now works as expected when the composite solid has no top
  level config.
- Compute log filenames are now guaranteed not to exceed the POSIX limit of 255 chars.
- Fixes an issue when copying and pasting solid names from Dagit.
- Termination now works as expected in the multiprocessing executor.
- The multiprocessing executor now executes parallel steps in the expected order.
- The multiprocessing executor now correctly handles solid subsets.
- Fixed a bad error condition in `dagster_ssh.sftp_solid`.
- Fixed a bad error message giving incorrect log level suggestions.

**Documentation**

- Minor fixes and improvements.

**Thank you**
Thank you to all of the community contributors to this release!! In alphabetical order: @cclauss,
@deem0n, @irabinovitch, @pseudoPixels, @Ramshackle-Jamathon, @rparrapy, @yamrzou.

# 0.6.6

**Breaking**

- The `selector` argument to `PipelineDefinition` has been removed. This API made it possible to
  construct a `PipelineDefinition` in an invalid state. Use `PipelineDefinition.build_sub_pipeline`
  instead.

**New**

- Added the `dagster_prometheus` library, which exposes a basic Prometheus resource.
- Dagster Airflow DAGs may now use GCS instead of S3 for storage.
- Expanded interface for schedule management in Dagit.

**Dagit**

- Performance improvements when loading, displaying, and editing config for large pipelines.
- Smooth scrolling zoom in the explore tab replaces the previous two-step zoom.
- No longer depends on internet fonts to run, allowing fully offline dev.
- Typeahead behavior in search has improved.
- Invocations of composite solids remain visible in the sidebar when the solid is expanded.
- The config schema panel now appears when the config editor is first opened.
- Interface now includes hints for autocompletion in the config editor.
- Improved display of solid inputs and output in the explore tab.
- Provides visual feedback while filter results are loading.
- Better handling of pipelines that aren't present in the currently loaded repo.

**Bugfix**

- Dagster Airflow DAGs previously could crash while handling Python errors in DAG logic.
- Step failures when running Dagster Airflow DAGs were previously not being surfaced as task
  failures in Airflow.
- Dagit could previously get into an invalid state when switching pipelines in the context of a
  solid subselection.
- `frozenlist` and `frozendict` now pass Dagster's parameter type checks for `list` and `dict`.
- The GraphQL playground in Dagit is now working again.

**Nits**

- Dagit now prints its pid when it loads.
- Third-party dependencies have been relaxed to reduce the risk of version conflicts.
- Improvements to docs and example code.

# 0.6.5

**Breaking**

- The interface for type checks has changed. Previously the `type_check_fn` on a custom type was
  required to return None (=passed) or else raise `Failure` (=failed). Now, a `type_check_fn` may
  return `True`/`False` to indicate success/failure in the ordinary case, or else return a
  `TypeCheck`. The new`success` field on `TypeCheck` now indicates success/failure. This obviates
  the need for the `typecheck_metadata_fn`, which has been removed.
- Executions of individual composite solids (e.g. in test) now produce a
  `CompositeSolidExecutionResult` rather than a `SolidExecutionResult`.
- `dagster.core.storage.sqlite_run_storage.SqliteRunStorage` has moved to
  `dagster.core.storage.runs.SqliteRunStorage`. Any persisted `dagster.yaml` files should be updated
  with the new classpath.
- `is_secret` has been removed from `Field`. It was not being used to any effect.
- The `environmentType` and `configTypes` fields have been removed from the dagster-graphql
  `Pipeline` type. The `configDefinition` field on `SolidDefinition` has been renamed to
  `configField`.

**Bugfix**

- `PresetDefinition.from_files` is now guaranteed to give identical results across all Python
  minor versions.
- Nested composite solids with no config, but with config mapping functions, now behave as expected.
- The dagster-airflow `DagsterKubernetesPodOperator` has been fixed.
- Dagit is more robust to changes in repositories.
- Improvements to Dagit interface.

**New**

- dagster_pyspark now supports remote execution on EMR with the `@pyspark_solid` decorator.

**Nits**

- Documentation has been improved.
- The top level config field `features` in the `dagster.yaml` will no longer have any effect.
- Third-party dependencies have been relaxed to reduce the risk of version conflicts.

# 0.6.4

- Scheduler errors are now visible in Dagit
- Run termination button no longer persists past execution completion
- Fixes run termination for multiprocess execution
- Fixes run termination on Windows
- `dagit` no longer prematurely returns control to terminal on Windows
- `raise_on_error` is now available on the `execute_solid` test utility
- `check_dagster_type` added as a utility to help test type checks on custom types
- Improved support in the type system for `Set` and `Tuple` types
- Allow composite solids with config mapping to expose an empty config schema
- Simplified graphql API arguments to single-step re-execution to use `retryRunId`, `stepKeys`
  execution parameters instead of a `reexecutionConfig` input object
- Fixes missing step-level stdout/stderr from dagster CLI

# 0.6.3

- Adds a `type_check` parameter to `PythonObjectType`, `as_dagster_type`, and `@as_dagster_type` to
  enable custom type checks in place of default `isinstance` checks.
  See documentation here:
  https://dagster.readthedocs.io/en/latest/sections/learn/tutorial/types.html#custom-type-checks
- Improved the type inference experience by automatically wrapping bare python types as dagster
  types.
- Reworked our tutorial (now with more compelling/scary breakfast cereal examples) and public API
  documentation.
  See the new tutorial here:
  https://dagster.readthedocs.io/en/latest/sections/learn/tutorial/index.html
- New solids explorer in Dagit allows you to browse and search for solids used across the
  repository.

- Enabled solid dependency selection in the Dagit search filter.

  - To select a solid and its upstream dependencies, search `+{solid_name}`.
  - To select a solid and its downstream dependents, search `{solid_name}+`.
  - For both search `+{solid_name}+`.

- Added a terminate button in Dagit to terminate an active run.

- Added an `--output` flag to `dagster-graphql` CLI.
- Added confirmation step for `dagster run wipe` and `dagster schedule wipe` commands (Thanks
  @shahvineet98).
- Fixed a wrong title in the `dagster-snowflake` library README (Thanks @Step2Web).

# 0.6.2

- Changed composition functions `@pipeline` and `@composite_solid` to automatically give solids
  aliases with an incrementing integer suffix when there are conflicts. This removes to the need
  to manually alias solid definitions that are used multiple times.
- Add `dagster schedule wipe` command to delete all schedules and remove all schedule cron jobs
- `execute_solid` test util now works on composite solids.
- Docs and example improvements: https://dagster.readthedocs.io/
- Added `--remote` flag to `dagster-graphql` for querying remote Dagit servers.
- Fixed issue with duplicate run tag autocomplete suggestions in Dagit (#1839)
- Fixed Windows 10 / py3.6+ bug causing pipeline execution failures

# 0.6.1

- Fixed an issue where Dagster public images tagged `latest` on Docker Hub were erroneously
  published with an older version of Dagster (#1814)
- Fixed an issue where the most recent scheduled run was not displayed in Dagit (#1815)
- Fixed a bug with the `dagster schedule start --start-all` command (#1812)
- Added a new scheduler command to restart a schedule: `dagster schedule restart`. Also added a
  flag to restart all running schedules: `dagster schedule restart --restart-all-running`.

# 0.6.0 "Impossible Princess"

**New**

This major release includes features for scheduling, operating, and executing pipelines
that elevate Dagit and dagster from a local development tool to a deployable service.

- `DagsterInstance` introduced as centralized system to control run, event, compute log,
  and local intermediates storage.
- A `Scheduler` abstraction has been introduced along side an initial implementation of
  `SystemCronScheduler` in `dagster-cron`.
- `dagster-aws` has been extended with a CLI for deploying dagster to AWS. This can spin
  up a Dagit node and all the supporting infrastructure—security group, RDS PostgreSQL
  instance, etc.—without having to touch the AWS console, and for deploying your code
  to that instance.
- **Dagit**
  - `Runs`: a completely overhauled Runs history page. Includes the ability to `Retry`,
    `Cancel`, and `Delete` pipeline runs from the new runs page.
  - `Scheduler`: a page for viewing and interacting with schedules.
  - `Compute Logs`: stdout and stderr are now viewable on a per execution step basis in each run.
    This is available in real time for currently executing runs and for historical runs.
  - A `Reload` button in the top right in Dagit restarts the web-server process and updates
    the UI to reflect repo changes, including DAG structure, solid names, type names, etc.
    This replaces the previous file system watching behavior.

**Breaking Changes**

- `--log` and `--log-dir` no longer supported as CLI args. Existing runs and events stored
  via these flags are no longer compatible with current storage.
- `raise_on_error` moved from in process executor config to argument to arguments in
  python API methods such as `execute_pipeline`

# 0.5.9

- Fixes an issue using custom types for fan-in dependencies with intermediate storage.

# 0.5.8

- Fixes an issue running some Dagstermill notebooks on Windows.
- Fixes a transitive dependency issue with Airflow.
- Bugfixes, performance improvements, and better documentation.

# 0.5.7

- Fixed an issue with specifying composite output mappings (#1674)
- Added support for specifying
  [Dask worker resources](https://distributed.dask.org/en/latest/resources.html) (#1679)
- Fixed an issue with launching Dagit on Windows

# 0.5.6

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

# 0.5.5

- Dagit now accepts parameters via environment variables prefixed with `DAGIT_`, e.g. `DAGIT_PORT`.
- Fixes an issue with reexecuting Dagstermill notebooks from Dagit.
- Bug fixes and display improvments in Dagit.

# 0.5.4

- Reworked the display of structured log information and system events in Dagit, including support
  for structured rendering of client-provided event metadata.
- Dagster now generates events when intermediates are written to filesystem and S3 storage, and
  these events are displayed in Dagit and exposed in the GraphQL API.
- Whitespace display styling in Dagit can now be toggled on and off.
- Bug fixes, display nits and improvements, and improvements to JS build process, including better
  display for some classes of errors in Dagit and improvements to the config editor in Dagit.

# 0.5.3

- Pinned RxPY to 1.6.1 to avoid breaking changes in 3.0.0 (py3-only).
- Most definition objects are now read-only, with getters corresponding to the previous properties.
- The `valueRepr` field has been removed from `ExecutionStepInputEvent` and
  `ExecutionStepOutputEvent`.
- Bug fixes and Dagit UX improvements, including SQL highlighting and error handling.

# 0.5.2

- Added top-level `define_python_dagster_type` function.
- Renamed `metadata_fn` to `typecheck_metadata_fn` in all runtime type creation APIs.
- Renamed `result_value` and `result_values` to `output_value` and `output_values` on
  `SolidExecutionResult`
- Dagstermill: Reworked public API now contains only `define_dagstermill_solid`, `get_context`,
  `yield_event`, `yield_result`, `DagstermillExecutionContext`, `DagstermillError`, and
  `DagstermillExecutionError`. Please see the new
  [guide](https://dagster.readthedocs.io/en/0.5.2/sections/learn/guides/data_science/data_science.html)
  for details.
- Bug fixes, including failures for some dagster CLI invocations and incorrect handling of Airflow
  timestamps.
