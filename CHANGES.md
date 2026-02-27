# Changelog

## 1.12.17 (core) / 0.28.17 (libraries)

### Bugfixes

- Fix bug with inclusion of built webapp in `dagster-webserver` that caused the Dagster UI to fail to load.

## 1.12.16 (core) / 0.28.16 (libraries) (YANKED)

This version of Dagster inadvertently did not include the webapp code in the published `dagster-webserver` package.

### Bugfixes

- [ui] Fixed redirect to login when the user's session expires.
- [ui] Fixed console error noise during asset lineage navigation.

### Dagster Plus

- [ui] Improved loading states and autoscroll behavior in the AI chat UI.
- [ui] Fixed the icon selector in the saved selection creation flow.

## 1.12.15 (core) / 0.28.15 (libraries)

### New

- Pool names can now be any non-whitespace character, instead of requiring alphanumbeic characters, slashes, and underscores.
- [dagster-aws] The `EcsRunLauncher` will now retry a task launch when a RunTask API call fails due to a throttling error in an underlying EC2 API call.
- [dagster-tableau] Tableau workbooks and projects can now be filtered using the `workbook_selector` and `project_selector` in `TableauComponent`.

### Bugfixes

- [ui] Fixed issue where saved launchpad config was not used for single-partition asset materializations.
- [ui] Fix console error noise during asset lineage navigation.
- [ui] Fixed an issue where the "Start X Automations" and "Stop X Automations" menu options on the Automations tab were sometimes incorrectly disabled.
- [dagster-dbt] The `DbtProject` constructor now correctly accepts strings for the `target_path` parameter.

## 1.12.14 (core) / 0.28.14 (libraries)

### New

- `@asset_check` and `AssetCheckSpec` now support a `partitions_def` parameter, allowing checks to execute against specific partitions of their upstream asset rather than the entire contents. If set, the partition definition must match the definition of the targeted asset.
- [ui] The "Select all" checkbox has been restored to the Automations list.

### Bugfixes

- Fixed performance issue where the partition selector would freeze for 30+ seconds when selecting "All" on assets with large (100k+) partition sets. (Thanks, [@ljodea](https://github.com/ljodea)!)
- Fixed an issue with cron schedules using step patterns (like `*/10` or `*/30`) in the day-of-month field where invalid days weren't properly skipped.
- [ui] Fixed an issue that could cause incorrect partition statuses to be displayed in the UI.
- [ui] Partition percentages now round in a more intuitive way.
- [ui] Row count metadata is now displayed even when set to zero.
- [dagster-databricks] Fixed an issue where op name generation would occasionally lead to collisions.
- [dagster-sigma] When building assets for Sigma workbooks that depend on tables unknown to Dagster, an error is logged instead of throwing an exception.
- [dagster-k8s] Fixed an issue where `PipesK8sClient` would sometimes fail when containers in the `ignored_containers` list failed.
- [dagster-github] Ensured compatibility with `pyjwt>=2.11.0`,which introduced breaking changes.

### Documentation

- Added an example of censoring PII in run logs.
- Updated branch deployment docs to include single-agent setup.

## 1.12.13 (core) / 0.28.13 (libraries)

### New

- [dagster-polytomic] `PolytomicComponent` has been added and can be used to represent your Polytomic bulk sync schemas as external assets in Dagster
- [dagster-fivetran] Added warning log when no Fivetran groups are found to help users troubleshoot permission issues.

## 1.12.12 (core) / 0.28.12 (libraries)

### New

- `dg plus deploy start` now validates deployment akin to `dagster-cloud ci check`.
- [dagster-aws] Added a suite of new components that map to all existing resources in the library.
- [dagster-k8s] Increased the maximum version of kubernetes to 35.x.x.
- [ui] You can now unpin asset groups that no longer contain any assets.

### Bugfixes

- Fixed type errors reported by Pyright's strict mode when using `@asset`, `@multi_asset`, and `@graph_asset` decorators.
- Running `dg launch --partition-range` for an asset without an explicitly defined single-run-backfill policy now provides a clean error message.
- Fixed issue where the celery_executor `config_source` values were ignored. (Thanks, [@danielbitzer](https://github.com/danielbitzer)!)
- Fixed issue with `dg plus deploy refresh-defs-state` URL construction for EU regions.
- Fixed helm chart validation error when enabling `concurrency` config with default `queuedRunCoordinator` values.
- `dg list defs` now correctly shows labels for automation conditions.
- [dagster-dbt] Fixed issue with the `dagster-dbt project prepare-and-package` command where user files named `dbt.py` could shadow the `dbt` module. (Thanks, [@alexaustin007](https://github.com/alexaustin007)!)
- [dagster-dbt] Fix errors raised when [dbt functions](https://docs.getdbt.com/docs/build/udfs) are present in dbt manifest. (Thanks, [@eso-xyme](https://github.com/eso-xyme)!)
- [ui] Fixes a bug where creating an alert policy from your Favorites would crash the app.

### Dagster Plus

- Fixed an issue while using the 'isolated_agents' configuration parameter in Dagster+ where runs that were terminated due to exceeding a maximum runtime would sometimes fail to terminate the run worker process after the run was marked as failed.

## 1.12.11 (core) / 0.28.11 (libraries)

### New

- The `dagster-cloud ci check` command is now marked as deprecated. Use `dg plus deploy start` instead, which now validates configuration during deployment initialization.
- [dagster-fivetran] `FivetranWorkspace` now supports a `request_backoff_factor` parameter for enabling exponential backoff on request failures.

### Bugfixes

- [dagster-dbt] Fixed an issue where the `exclude` parameter of `@dbt_assets` could be ignored if the selection was too large.
- [ui] The Asset Partitions page and the launch Materializations modal now correctly handle asset partitions that contain JSON or irregular characters.
- [ui] Fixed an issue where `dagster/row_count` metadata was sometimes not displayed on the Asset Overview page if it was being set by an asset observation rather than a materialization.

### Dagster Plus

- The ECS agent now waits for 10 minutes by default before timing out during a code location deploy instead of 5 minutes, to ensure that large images have enough time to be pulled by the agent. See https://docs.dagster.io/deployment/dagster-plus/hybrid/amazon-ecs/configuration-reference#user_code_launcher-properties for more information on changing this default.
- [ui] The Job Insights tab now shows a metric breakdown by job

## 1.12.10 (core) / 0.28.10 (libraries)

### Bugfixes

- [ui] Fixed an issue introduced in 1.12.9 where the "Catalog" tab in the Dagster UI sometimes failed to display any assets.

## 1.12.9 (core) / 0.28.9 (libraries)

### New

- The core `dagster` package (and most libraries) are now compatible with Python 3.14.
- Added support for using python version 3.13 when running `dg plus deploy`.
- `dg plus login` now supports a `region` flag for eu-based users: `dg plus login --region eu`.
- Updated the `bulk_actions` table `body` column from `Text` to `LongText` for Mysql storage. To take advantage of this migration run `dagster instance migrate`. (Thanks, [@jenkoian](https://github.com/jenkoian)!)
- Updated the `asset_keys` table `cached_status_data` column from `Text` to `LongText` for Mysql storage. To take advantage of this migration run `dagster instance migrate`. (Thanks, [@jenkoian](https://github.com/jenkoian)!)
- Runs now automatically include a `dagster/code_location` tag when created with a `remote_job_origin`, enabling filtering and concurrency control by code location. (Thanks, [@ssup2](https://github.com/ssup2)!)
- [ui] the Asset > Partitions page now shows historical "Failed to materialize" events for consistency with the Asset > Events page.
- [helm] Added a `concurrency` setting to the helm chart to configure concurrency pools.
- [dagster-azure] The `ADLS2PickleIOManager` now overwrites blob keys when the same asset is materialized twice, instead of deleting then writing the blob.
- [dagster-aws] An `ecs/container_overrides` tag can now be set on jobs (or on runs in the launchpad) to customize container-level overrides (like GPU resource requirements) for runs using the `EcsRunLauncher`.
- [dagster-dbt] `dagster-dbt` now supports dbt-core 1.11. (Thanks, [@nicoa](https://github.com/nicoa)!)
- [dagster-dlt] update url in README (Thanks, [@Miesjell](https://github.com/Miesjell)!)
- [dagster-databricks] Introduced `DatabricksWorkspaceComponent` to automatically discover Databricks jobs as Dagster assets.
- [dagster-looker] Added option PDT asset support to `LookerComponent`.

### Bugfixes

- Fixed an issue where a transient issue caused a step health check to fail when using the `k8s_job_executor`.
- Fixed an issue where a health check failure while using the `k8s_job_executor` could result in a step continuing to run after the run failed.
- Invalid `TimeWindowPartitionsDefinitions` that contain multiple time windows that map to the same partition key (for example, an hourly partitions definition with a daily format key) will now raise an `Exception` during `dagster definitions validate`, instead of being allowed but causing undefined behavior.
- [ui] Entering the asset launchpad by right-clicking on the asset graph no longer causes keyboard navigation issues.
- [ui] Fixed an issue where removing an asset prevented rendering status information for backfills involving that asset in the Dagster UI.
- [dagster-dbt] Fixed issue that could cause the `DbtCliEventMessage` iterator to error while parsing certain error messages produced by `dbt-core`.

## 1.12.8 (core) / 0.28.8 (libraries)

### New

- `dg plus deploy` commands now support Python 3.13 and Python 3.14.

### Bugfixes

- Fixed an issue where the Dagster Helm chart and Dagster+ agent helm chart could no longer deploy using Helm without adding the `--skip-schema-validation` flag to the Helm deploy command. Thanks [@kang8](https://github.com/kang8)!

## 1.12.7 (core) / 0.28.7 (libraries)

### New

- Optimized performance of calculating partition keys for time window partitions with exclusions.
- `timedelta` and `datetime` are now available via the `datetime` context when rendering components (Thanks, [@stevenayers](https://github.com/stevenayers)!)
- `FreshnessPolicy` is now available via the `dg` context when rendering components. (Thanks, [@stevenayers](https://github.com/stevenayers)!)
- Assets may now be annotated with up to 10 kinds (limit was previously 3).
- Arbitrary resource parameters may now be hidden in the UI by setting `json_schema_extra={"dagster__is_secret": True}` on the corresponding `Field` definition in the resource class.
- The `dg docs` cli group has been removed. The `integrations` subcommand has been moved to `dg utils integrations`.
- Bumped the `gql` dependency in `dagster-graphql` to be inclusive of v4 for broader transitive dependency compatibility
- [dagster-omni] Fix issue where retries would terminate while asynchronously gathering metadata.
- [dagster-tableau] The value of resource parameter `TableauWorkspace.connected_app_secret_value` is now hidden in the UI.
- [dagster-tableau] Updated extraction logic to handle hidden sheets. The materializable data sources connected to these sheets are now successfully detected and included as materializable data assets. (Thanks, [@miriamcastel](https://github.com/miriamcastel)!)

### Bugfixes

- Fix an AttributeError when calling `map_asset_specs` on assets defined using the `ins` parameter. (Thanks, [@Jongwan93](https://github.com/Jongwan93)!)
- Fix an issue where backfill runs that incorrectly created unpartitioned materializations of a partitioned asset, or partitioned materializations of an unpartitioned asset due to incorrect asset business logic would move the backfill into an invalid state. Now, the backfill will detect this case and fail the backfill.
- Fixed an issue with `dg plus deploy refresh-defs-state` which could cause errors when refreshing state for components that required CLIs that were only available in the project environment.
- [dagster-dbt] Fixed issue that could cause errors when emitting events for a dbt Cloud job run.

### Dagster Plus

- Dagster Plus Pro users can now create service users. Service users are accounts that can
  authenticate API requests but that are not tied to any particular human user.

## 1.12.6 (core) / 0.28.6 (libraries)

### New

- All CLI commands under `dagster project` have been removed. `create-dagster` should be used instead.
- [ui] Added a new Partitions facet to the Asset Lineage Graph.
- [ui] More details are now displayed for `SINCE` conditions in evaluation tables for automation conditions.
- [dagster-dbt] Added dbt cloud logs to stdout after the run completes in dbt cloud.
- [dagster-tableau] Improved resilience when fetching Tableau workspace data. The integration now skips individual workbooks that fail to return data and logs a warning, rather than failing the entire operation. (Thanks, [@miriamcastel](https://github.com/miriamcastel)!)

### Bugfixes

- Fixed an issue that would cause errors when attempting to create subclasses of `Resolved` that had fields using `default_factory` arguments.
- Fixed an issue with `dg plus deploy refresh-defs-state` which could cause errors when refreshing state for components that required CLIs that were only available in the project environment.
- [ui] Fixed Snowflake connection by changing the private key encoding from PEM to DER format. Snowflake requires unencrypted RSA private keys to be in DER format as bytes.
- [dagster-dbt] Updated `DbtCliResource` to use the `project_dir` attribute from the `DbtProject` instance rather than passing the entire `DbtProject` object.
- [dagster-tableau][dagster-sigma] Fixed bug that would cause templated env vars to not be resolved when specified in yaml.

## 1.12.5 (core) / 0.28.5 (libraries)

### New

- Increased the version of NextJS used by the Dagster webserver and the `dg docs serve` command to `15.5.7`. While these applications are unaffected by https://nextjs.org/blog/CVE-2025-66478 due to not using React 19, this upgrade ensures that dagster packages will not be flagged for that CVE by vulnerability scanners.

## 1.12.4 (core) / 0.28.4 (libraries)

### New

- CI workflows for Gitlab projects can now be scaffolded using `dg plus deploy configure`.
- "/" characters are now allowed in concurrency pool names.
- Pod wait timeout for K8sPipeClient can now be specified (Thanks, [@abhinavDhulipala](https://github.com/abhinavDhulipala)!)
- New `kind` tag icon for Zendesk (Thanks, [@kporter13](https://github.com/kporter13)!)
- [dagster-tableau] Added `enable_embedded_datasource_refresh` and `enable_published_datsource_refresh` options to the `TableauComponent`, which allow creating materializable assets for the associated datasource types.

### Bugfixes

- Fixed an issue where passing in JSON serializable enums to JsonMetadataValue would sometimes result in an error.
- Fixed an issue that would cause `SensorDefinition` subclasses (e.g. `AutomationConditionSensorDefinition`, `RunStatusSensorDefinition`) to be converted to having the wrong `sensor_type` property when produced from a `Component`.
- Fixed an issue where the `Flower` config map was included in the Helm chart even when `Flower` was disabled (Thanks, [@LoHertel](https://github.com/LoHertel)!)
- [dagster-dbt] Fixed a `FileExistsError` on Windows when reloading `dbt` project definitions by ensuring the local project directory creation handles pre-existing directories (Thanks, [@Jongwan93](https://github.com/Jongwan93)!)
- [dagster-tableau] Fixed a KeyError that occurred when using `workbook_selector_fn` to filter assets. Now dependencies are only accessed if they exist in the workspace data. (Thanks, [@miriamcastel](https://github.com/miriamcastel)!)
- [dagster-tableau] Fixed an issue where `workbook_selector_fn` was only applied to the first 100 workbooks.
- [dagster-tableau] The workbook is now part of the asset key prefix to avoid naming collisions.
- [dagster-tableau] Fixed an issue where workbook names with dots `.` were improperly handled.

### Documentation

- Updated `dagster-iceberg` docs to include recently-added features. (Thanks, [@zyd14](https://github.com/zyd14)!)

## 1.12.3 (core) / 0.28.3 (libraries)

### New

- Updated the cursoring logic of `AutomationCondition.since()`/`AutomationCondition.newly_true()` to make them retain access to their stored data in a wider range of scenarios where the underlying condition structure is changed.
- Added a `--use-active-venv` method to a variety of `dg` commands. (Thanks, [@cmpadden](https://github.com/cmpadden)!)
- The `build_defs_at_path` and `load_component_at_path` methods on the `ComponentLoadContext` class have been renamed to `build_defs` and `load_component` respectively. The previous names have been preserved for backcompat.
- The template variables available in the default resolution scope for Components have been reorganized / expanded:
  - `{{ automation_condition.on_cron(...) }} ` -> `{{ dg.AutomationCondition.on_cron(...) }}`
  - **new: ** All `AutomationCondition` static constructors may be accessed via the `dg` context, e.g.:
    - `{{ dg.AutomationCondition.on_missing() & dg.AutomationCondition.in_latest_time_window() }}`
  - **new: ** All `PartitionsDefinition` subclasses are now available via the `dg` context, e.g.:
  - `{{ dg.StaticPartitionsDefinition(['a', 'b', 'c']) }}`
  - `{{ dg.DailyPartitionsDefinition('2025-01-01') }}`
  - `{{ project_root }}` -> `{{ context.project_root }}`
  - `{{ build_definitions_at_path(...) }}` -> `{{ context.build_defs(...) }}`
  - `{{ load_component_at_path(...) }}` -> `{{ context.load_component(...) }}`
  - All previous template vars will continue to work as before for backcompat.
- [ui] Improve browser performance for large asset graphs.
- [dagster-snowflake] Added `create_snowpark_session()` which provides a convenient way to create a Snowpark session. (Thanks, [@stevenayers](https://github.com/stevenayers)!)
- [dagster-snowflake] Added `get_databases()`, `get_schemas()`, `get_tables()`, `get_views()`, `get_pipes()` & `get_stages()` which provide a pythonic interface for Snowflake introspection. (Thanks, [@stevenayers](https://github.com/stevenayers)!)
- [dagster-dbt] You can now override the `op_config_schema` property on the `DbtProjectComponent` to customize how your dbt execution can be configured at runtime.

### Bugfixes

- Added the ability to execute refreshes of embedded and published datasources when using the TableauComponent.
- Fixed a bug in asset partitions where the partition range selector would sometimes stop working.
- [dagster-dbt] Fixed a `FileExistsError` on Windows when reloading `dbt` project definitions by ensuring the local project directory creation handles pre-existing directories. (Thanks, [@Jongwan93](https://github.com/Jongwan93)!)
- [dagster-dbt] Fixed an issue introduced in version 1.12.2 that caused the `DbtProjectComponent` to not produce asset checks for tests on dbt sources. (Thanks, [@stevenayers](https://github.com/stevenayers)!)

### Documentation

- Added documentation for the community dagster-slurm integration. (Thanks, [@geoHeil](https://github.com/geoHeil)!)

## 1.12.2 (core) / 0.28.2 (libraries)

### New

- Dagster has dropped support for Python 3.9 (due to end of life). The minimum supported Python version is now 3.10. This is a breaking change originally intended for the 1.12.0 release.
- Added `dg api schedule {list,get}` command.
- Added new `dg plus deploy configure` CLI group that generates all the files necessary to get an existing project ready for deployment via Dagster+.
- [ui] A new sidebar in the Asset catalog (behind a feature flag) provides a hierarchical view of your asset keys.
- [ui] Improve a few parts of the "Recent updates" timeline section of the Asset overview page.
- [dagster-census] Added `CensusComponent` allowing Dagster assets to sync with census connections.
- [dagster-airbyte] New AirbyteWorkspace configurations: `poll_previous_running_sync`, `max_items_per_page`, `poll_interval`, `poll_timeout` & `cancel_on_termination`. (Thanks, [@stevenayers](https://github.com/stevenayers) and [@sonianuj287](https://github.com/sonianuj287)!)
- [dagster-dbt] You can now override the `op_config_schema` property on the `DbtProjectComponent` to customize how your dbt execution can be configured at runtime.

### Dagster Plus

- [ui] "Edit public catalog views" is now editable in the role permission list.

## 1.12.1 (core) / 0.28.1 (libraries)

### New

- Migrate SqlComponent to Pydantic v2 model_config pattern (Thanks, [@LPauzies](https://github.com/LPauzies)!)
- Make `dg api` commands visible in `dg --help` output.
- Make `dg plus` commands visible in the `dg --help` output.
- Add Dremio kind icon. (Thanks, [@maxfirman](https://github.com/maxfirman)!)
- The github actions scaffolded by `dg scaffold github-actions` now include commands to refresh state for `StateBackedComponents`.
- Run worker health check will now tag runs with their associated ENI ids.
- [ui] In asset sidebar, clearly indicate when a freshness policy is a legacy policy.
- [ui] Cost metrics are now shown on the asset catalog insights page.
- [dagster] New AutomationConditions for checking asset freshness - `dg.AutomationCondition.freshness_passed()`, `dg.AutomationCondition.freshness_warned()` and `dg.AutomationCondition.freshness_failed()`. (Thanks, [@stevenayers](https://github.com/stevenayers)!)

### Bugfixes

- [ui] Fix a sporadic race condition when loading jobs in the Dagster UI.
- [ui] Fixed an issue where deploying multiple serverless code locations simultaneously would sometimes fail with a "the dagster package dependency was expected but not found" error.
- [ui] Fixed a bug that would cause errors when attempting to supply config to a backfill that targeted assets with checks.
- [ui] Fixed an issue introduced in dagster 1.11.16 where repositories using custom RepositoryData subclasses would sometimes raise an error when viewing jobs in the Dagster UI.
- [ui] Fix sensor descriptions in the automation list.
- [dagster-dask] Fixed an issue where Dask parquet filters configured in YAML would fail with `ValueError: too many values to unpack (expected 3)` when using Dask version 2022.4.2. (Thanks, [@kudryk](https://github.com/kudryk)!)
- [dagster-dbt] Fixed an issue where dagster-dbt runs targeting large numbers of models could cause the underlying `dbt` CLI invocation to fail from too many arguments.

### Dagster Plus

- [ui] The insights view in the Observe UI now allows you to specify a custom date range.

## 1.12.0 (core) / 0.28.0 (libraries)

## Major changes since 1.11.0 (core) / 0.27.0 (libraries)

### **UI**

- **Refreshed UI:** The UI has been redesigned and streamlined to make it easier to find common utilities quickly. Navigation elements have been moved from a header to a collapsible sidebar to help highlight important workflows and provide more visual space throughout the product.

### Components

- **Components GA:** The Components framework and the `dg` CLI are now marked as GA (previously Release Candidate). The APIs are fully supported throughout all parts of the product and remain the recommended defaults for new Dagster projects.
- **Standardized Integrations:** Integration components have been updated to have `execute()` and `get_asset_spec()` methods that can be overridden by subclasses, making it easier and more consistent to customize your components.
- **New Components:**
  - [SigmaComponent](https://docs.dagster.io/integrations/libraries/sigma)
  - [LookerComponent](https://docs.dagster.io/integrations/libraries/looker)
  - [TableauComponent](https://docs.dagster.io/integrations/libraries/tableau)
  - [OmniComponent](https://docs.dagster.io/integrations/libraries/omni)
- **State-Backed Components:** Added a new `StateBackedComponent` abstract base class that enables components to persist and manage state separately from their YAML / Python configuration. This is particularly useful for integration components that need to fetch external data. State can be managed locally, in versioned storage, or via code server snapshots. Many integration components (`AirbyteWorkspaceComponent`, `FivetranAccountComponent`, `PowerBIWorkspaceComponent`, `AirflowInstanceComponent`, and `DbtProjectComponent`) now extend `StateBackedComponent` to provide better control over state management. You can check out the docs [here](https://docs.dagster.io/guides/build/components/state-backed-components)!

### Simplified Deployment

- `dg scaffold build-artifacts` scaffolds Docker and configuration files needed to build and deploy your Dagster project to Dagster Cloud, with support for multiple container registries (ECR, DockerHub, GHCR, ACR, GCR).
- `dg scaffold github-actions` generates a complete GitHub Actions CI/CD workflow for deploying to Dagster Cloud, with auto-detection of Serverless vs Hybrid agents and guided setup for required secrets.

### **Core Orchestration**

- **FreshnessPolicies GA:** The new [FreshnessPolicy](https://docs.dagster.io/guides/observe/asset-freshness-policies) API introduced in 1.10.0 has stabilized and is now marked as GA (previously Preview). These supersede the `LegacyFreshnessPolicy` API (formerly `FreshnessPolicy`, deprecated in 1.10.0), as well as freshness checks.
  - `FreshnessPolicy` and `apply_freshness_policy` are now exported from the top-level `dagster` module (instead of `dagster.preview.freshness` ).
  - The `build_.*_freshness_checks` methods have been marked as `superseded` . Their functionality will remain unchanged, but we recommend using `FreshnessPolicy` s for new use cases.
  - The `FreshnessDaemon` now runs by default, rather than needing to be explicitly enabled via `dagster.yaml` settings. To turn it off, set:
    ```yaml
    freshness:
      enabled: false
    ```
- **Configurable Backfills:** Run config can now be supplied when launching a backfill, allowing you to specify configuration that will be applied uniformly to all runs.
- **Time-based partition exclusions:** All subclasses of `TimeWindowPartitionsDefinition` now support an `exclusions` parameter, which allows you to exclude specific dates/times or recurring schedules from your partition set. This is useful for implementing custom calendars that exclude weekends, holidays, or maintenance windows. Exclusions can be specified as cron strings (e.g., `"0 0 * * 6"` for Saturdays) or datetime objects for specific dates.
- **Execution Dependency Options:** All `Executor`s have been updated to accept an optional `step_dependency_config` parameter with a `require_upstream_step_success` flag. When set to `False` via `{"step_dependency_config": {"require_upstream_step_success": False}}`, downstream steps can start as soon as their required upstream outputs are available, rather than waiting for the entire upstream step to complete successfully. This is particularly useful for large multi-assets where downstream assets only depend on a subset of upstream outputs.

### Support & Docs

- We launched a new [Support Center](https://support.dagster.io/) with help articles on Dagster+ Hybrid and Serverless troubleshooting, and answers to customer questions previously answered by our support team.
- In our [docs](https://docs.dagster.io/):
  - We reorganized the [Examples section](https://docs.dagster.io/examples) for easier navigation, and added new full pipeline examples on using Dagster with [DSpy](https://docs.dagster.io/examples/dspy) and [PyTorch](https://docs.dagster.io/examples/ml), as well as targeted mini examples that showcase best practices for:
    - [implementing dynamic fanout patterns](https://docs.dagster.io/examples/mini-examples/dynamic-fanout)
    - [using Dagster dynamic outputs for parallel processing](https://docs.dagster.io/examples/mini-examples/dynamic-vs-parallel)
    - [caching resources](https://docs.dagster.io/examples/mini-examples/resource-caching)
    - [sharing code across projects](https://docs.dagster.io/examples/mini-examples/shared-module)
  - We added new guides to help you:
    - [optimize and troubleshoot your Dagster+ Hybrid deployment](https://docs.dagster.io/deployment/troubleshooting/hybrid-optimizing-troubleshooting)
    - [understand where and why your Dagster code is hanging or running slow](https://docs.dagster.io/deployment/troubleshooting/py-spy-guide)
    - [resolve sensor timeout issues](https://docs.dagster.io/deployment/troubleshooting/sensor-timeouts)
  - We added links to Dagster University, our popular Python Primer blog post series, Dagster Deep Dives, customer case studies, Dagster Open Platform, and sales demo example pipelines so you can access all the resources you need to learn about Dagster in one place.

## Changes since 1.11.16 (core) / 0.27.16 (libraries)

### New

- In the Dagster helm chart, images can now be specified by digest (Thanks, [@pmartincalvo](https://github.com/pmartincalvo)!)
- The `MultiprocessExecutor`, `DockerExecutor`, and `K8sJobExecutor` now retry according to their configured retry policy when the step fails during resource initialization.
- [dagster-aws] Added an optional `key_prefix` parameter to `PipesS3ContextInjector` (Thanks, [@elipinska](https://github.com/elipinska)!)
- [dagster-azure] Added a new `PipesAzureMLClient`.
- [dagster-pipes] Added support for `AzureBlobStorage`.
- [dagster-tableau] Added a new `TableauComponent`
- [dagster-looker] Added a `LookerComponent`
- [dagster-sigma] Added a new `SigmaComponent`.
- [dagster-dbt] The `DagsterDbtTranslator` no longer has a `get_freshness_policy` method, nor does it automatically parse the legacy / deprecated `LegacyFreshnessPolicy` objects from dbt model configuration.
- [dagster-sling] The `DagsterSlingTranslator` no longer has a `get_freshness_policy` method, nor does it automatically parse the legacy / deprecated `LegacyFreshnessPolicy` objects from sling configuration.

### Bugfixes

- Asset jobs that are unable to resolve their asset selection (for example, due to targeting an empty set of asset keys) will now raise a clearer exception at definition load time explaining which job failed to resolve its asset selection.
- Fixed an issue where automatic run retries of runs that only targeted asset checks would sometimes fail with a `DagsterInvalidConfigError`.
- [ui] Fixed issue causing sensor descriptions to not be displayed in the automation list.
- [dagster-dbt] Fixed a bug causing `enable_code_references` to result in errors for dbt assets.

### Documentation

- Corrected several typos and inconsistencies in the helm chart documentation (Thanks, [@piggybox](https://github.com/piggybox)!)

## 1.11.16 (core) / 0.27.16 (libraries)

### New

- The proxy GRPC server heartbeat TTL can now be configured with the DAGSTER_GRPC_PROXY_HEARTBEAT_TTL_SECONDS env var (default remains 30 seconds).

### Bugfixes

- Fixed an issue introduced in dagster 1.11.15 where code locations that previously loaded would sometimes fail to load with a `gRPC Error code: RESOURCE_EXHAUSTED` error.
- Fixed an issue where defining a repository using a dictionary of job definitions with a key that did not match the name of the job would work when running dagster locally but not when using Dagster+.
- [components] Fixed a bug that caused errors when using the `DbtProjectComponent`, `FivetranAccountComponent`, and similar state-based components in k8s deployments due to a missing `StateStorage` object in context.
- [dagster-omni] Added a dependency on `python-dateutil` to `dagster-omni`. (Thanks, [@bollwyvl](https://github.com/bollwyvl)!)

## 1.11.15 (core) / 0.27.15 (libraries)

### New

- All sequences are now supported in `AssetKey.with_prefix`. (Thanks, [@aksestok](https://github.com/aksestok)!)
- [ui] Introduce new navigation, with main navigation items previously in top navigation now in a collapsible left nav.
- [ui] Improve loading performance of Runs page.
- [dagster-databricks] Add support for `notebook_task` in `PipesDatabricksClient`. (Thanks, [@SoerenStahlmann](https://github.com/SoerenStahlmann)!)

### Bugfixes

- Fixed an issue where `fetch_row_counts` and `fetch_column_metadata` do not execute in the same working directory as the underlying dbt command.
- Fixed a bug with `AutomationCondition.execution_failed` that would cause it to be evaluated as `True` for an unpartitioned asset in cases where the latest run failed, but the asset itself materialized successfully before that failure.
- Unrelated resource keys are now no longer included in the run config schema for subselections of assets.
- Ignored nodes are properly excluded when generating run config for an implicit asset job
- Invalid UTF-8 in stderr compute logs are now handled gracefully. (Thanks, [@2bxtech](https://github.com/2bxtech)!)
- [ui] Fix top nav rendering for Plus users.
- [dagster-celery] Fix Celery executor ignoring pools for ops. (Thanks, [@kkanter-asml](https://github.com/kkanter-asml)!)
- [dagster-dbt] Fixed issue that made custom template vars unavailable when specifying them for the `cli_args:` field of the `DbtProjectComponent`.
- [dagster-cloud-cli] Fixed an issue where deploying multiple serverless code locations or code locations with a custom project directory would sometimes fail with an "The dagster package dependency was expected but not found." error.

### Documentation

- Fixed broken social media link in docs. (Thanks, [@MandyMeindersma](https://github.com/MandyMeindersma)!)

### Dagster Plus

- [ui] Fix home page performance for users with large numbers of automations and jobs.
- [ui] Fix a sporadic JavaScript error that can crash the page when loading insights charts.

## 1.11.14 (core) / 0.27.14 (libraries)

### New

- `UnionTypes` (e.g. `Foo | Bar`) are now supported in `ConfigurableResources`. (Thanks, [@DominikHallab](https://github.com/DominikHallab)!)
- Added an `output_metadata` parameter to `build_output_context` (Thanks, [@zyd14](https://github.com/zyd14)!)
- `ResolvedAssetSpec` and related resolvers now support setting the `freshness_policy` field.
- `dagster-dbt project prepare-and-package --components .` will no longer attempt to load components outside of `DbtProjectComponent`, preventing errors when attempting to run this command in environments that do not have the necessary env vars set for other components.
- `click<8.2` upper bound has been removed
- [dagster-airbyte][dagster-fivetran][dagster-powerbi][dagster-sling][dagster-dlt] The `AirbyteWorkspaceComponent`, `FivetranAccountComponent`, `PowerBIWorkspaceComponent`, `SlingReplicationCollectionComponent`, and `DltLoadCollectionComponent` components have been updated to include a `get_asset_spec` method that can be overridden by subclasses to modify translation behavior.
- [dagster-airbyte][dagster-fivetran] The `AirbyteWorkspaceComponent` and `FivetranAccountComponent` have been updated to include an `execute()` method that can be overridden by subclasses to modify runtime execution behavior.
- [dagster-airbyte] The `AirbyteWorkspaceComponent` no longer binds an `"io_manager"` or `"airbyte"` resource, meaning it can be used in tandem with other definitions that use those keys without causing conflicts.
- [dagster-dbt] The `DbtProjectComponent` now supports overriding `get_asset_spec` and `get_asset_check_spec` methods when subclassing.
- [dagster-fivetran] The `FivetranAccountComponent` no longer binds an `"io_manager"` or `"fivetran"` resource, meaning it can be used in tandem with other definitions that use those keys without causing conflicts.

### Bugfixes

- Fixed a bug that would cause errors when instantiating a `TimeWindowPartitionsDefinition` with a monthly schedule and the default day offset.
- [ui] The `Materialize` button in the lineage view is now disabled while the view is updating to avoid inconsistencies when launching runs.
- [ui] Fixed an issue where the "View error" link in the popup that displayed when a backfill failed to launch was very difficult to see.
- [dagster-dbt] Fixed issue where the `select` and `exclude` parameters to `@dbt_assets` would be ignored when generating `AssetCheckSpecs` (Thanks, [@nathanskone](https://github.com/nathanskone)!)
- [dagster-powerbi] Previously, assets generated for semantic models would have a kind tag with an invalid space character (`"semantic model"`). Now, they have the kind tag `"semantic_model"`.
- [dagster-sling] Resolved issue that caused the substring "INF" to be stripped from all logs.

## 1.11.13 (core) / 0.27.13 (libraries)

### New

- [dagster-deltalake,dagster-deltalake-polars] BREAKING CHANGE - we now support `deltalake>=1.0.0` for `dagster-deltalake` and `dagster-deltalake-polars` and we will no longer support `deltalake<1.0.0` moving forward. End user APIs remain the same for both libraries.
- [dagster-databricks] Spark Python and Python Wheel tasks are now supported in `PipesDatabricksServerlessClient`.
- [dagster-dbt] `dagster-dbt project prepare-and-package --components .` will no longer attempt to load components outside of `DbtProjectComponent`, preventing errors when attempting to run this command in environments that do not have the necessary env vars set for other components.
- [dg] adds `dg api secret list` and `dg api secret get`

### Bugfixes

- Fixed a bug in the backfill daemon where an asset backfill with CANCELING​ or FAILING​ status could become permanently stuck in CANCELING​ or FAILING​ if the partitions definitions of the assets changed.
- Fixed an issue introduced in the 1.11.12 release where auto-complete in the Launchpad for nested fields stopped working.
- Fixed an issue where backfills would fail if a TimeWindowPartitionsDefinition's start date was changed in the middle of the backfill, even if it did not remove any of the targeted partitions.
- [ui] Fixed the link to "View asset lineage" on runs that don't specify an asset selection.

## 1.11.12 (core) / 0.27.12 (libraries)

### New

- [ui] Allow searching across code locations with `*` wildcard in selection inputs for jobs and automations.
- [ui] Added `AutomationCondition.all_new_executed_with_tags`, which allows automation conditions to be filtered to partitions that have been materialized since the last tick from runs with certain tags. This condition can be used to require or prevent certain run tags from triggering downstream declarative automation conditions.

### Bugfixes

- In `dagster==1.11.1`, `partitioned_config` was unintentionally removed from the public exports of the top-level `dagster` package. This has been fixed.
- Avoid adding trailing whitespace in env vars that use dot notation in components. Thanks [@edgarrmondragon](https://github.com/edgarrmondragon)!
- [dagster-airbyte] Fix the pagination url issue for the Airbyte API. Thanks [@stevenayers](https://github.com/stevenayers)!
- [dagster-dbt] Fixed an issue with the DbtCloudWorkspaceClient that would cause errors when calling `trigger_job_run` with no steps_override parameter.

### Dagster Plus

- [ui] Add Cost insights.
- [ui] For users who have inherited org roles from a team, show those roles when editing the user.
- [ui] Fix per-asset and per-job insights graphs.

## 1.11.11 (core) / 0.27.11 (libraries)

### New

- `anthropic`, `mcp`, and `claude-code-sdk` dependencies of `dagster-dg-cli` are now under a separate `ai` extra, allowing `dagster-dg-cli` to be installed without these dependencies.
- Added `AutomationCondition.all_new_updates_have_run_tags` and `AutomationCondition.any_new_update_has_run_tags`, which allows automation conditions to be filtered to partitions that have been materialized since the last tick from runs with certain tags. This condition can be used to require or prevent certain run tags from triggering downstream declarative automation conditions. These conditions are similar to `AutomationCondition.executed_with_tags`, but look at all new runs since the most recent tick instead of just looking at the latest run.

### Bugfixes

- Fixed a bug which would cause steps downstream of an asset with `skippable=True` and a blocking asset check to execute as long as the asset check output was produced, even if the asset output was skipped.
- When a backfill fails, it will now cancel all of its in-progress runs before terminating.
- Fixed an issue that would cause trailing whitespace to be added to env vars using dot notation (`{{ env.FOO }}`) when listing the env vars used by a component. (Thanks, [@edgarrmondragon](https://github.com/edgarrmondragon)!)
- Fixed issue that would cause errors when using multi to single partition mappings with `DbIOManager`s.
- [ui] Fixed issue with the "Report materialization" dialog for non-partitioned assets.
- [ui] Typing large YAML documents in the launchpad when default config is present is now more performant.
- [ui] Fixed an issue where setting a FloatMetadataValue to float('inf') or float('-inf') would cause an error when loading that metadata over graphql.
- [ui] The "Clear" button in the dimension partition text input for multi-partitioned assets now clears invalid selections as expected.
- [dagster-dbt] Fixed an issue with the `DbtCloudWorkspaceClient` that would cause errors when calling `trigger_job_run` with no `steps_override` parameter.

## 1.11.10 (core) / 0.27.10 (libraries)

### New

- Added `inline-component` command to the publicly available scaffold commands in the Dagster CLI.
- Added a new `require_upstream_step_success` config param to all executors. If `{"step_dependency_config": {"require_upstream_step_success": False}}` is set, this will allow downstream steps to execute immediately after all required upstream outputs have finished, even if the upstream step has not completed in its entirety yet. This can be useful particularly in cases where there are large multi-assets with downstream assets that depend on only a subset of the assets in the upstream step.
- The `logsForRun`​ resolvers and `eventConnection`​ resolvers in the Dagster GraphQL API will now apply a default limit of 1000 to the number of logs returned from a single graphql query. The `cursor`​ field in the response can be used to continue iterating through the logs for a given run.
- [dagster-airbyte] `@airbyte_assets` and `AirbyteWorkspaceComponent` (previously `AirbyteCloudWorkspaceComponent`) now support Airbyte OSS and Enterprise.

### Bugfixes

- Fixed an issue where the `dagster_dg_cli` package failed to import when using Python 3.9.
- Fixed an issue with `AutomationCondition.eager()` that could cause runs for materializable assets to be launched at the same time as an upstream observable source asset that had an automation condition, even if the upstream observation would not result in a new data version.
- Fixed an issue which could, in some circumstances, cause errors during Declarative Automation evaluation after a dynamic partition was deleted.
- Fixed an issue that could cause confusing errors when attempting to supply `attributes` configuration to `Component` subclasses that did not inherit from `Resolvable`.
- Added a Matillion kind tag, thanks [@RobBrownFreeAgent](https://github.com/RobBrownFreeAgent)!
- [ui] Fixed an issue where the "Report materialization events" dialog for partitioned assets only worked if the partition was failed or missing.
- [ui] Fixed a browser crash which could occur in the global asset graph.
- [ui] Fixed a bug with the sensor preview behavior that would cause run requests contianing `run_key`s that had already been submitted to show up in the preview result.
- [dagster-dbt] Fixed an issue that would cause the DbtCloudWorkspace to error before yielding asset events if the associated dbt Cloud run failed. Now, it will raise the error _after_ all relevant asset events have been produced.
- [dagster-dbt] Added the `dbt-core` dependency back to `dagster-dbt` as it is still required for the dbt Cloud integration. If both `dbt-core` and `dbt Fusion` are installed, `dagster-dbt` will still prefer using `dbt Fusion` by default.

### Documentation

- Introduced a new "Post-processing components" guide.
- Fixed incorrect YAML code snippets for alert policies docs page.
- Fixed incorrect chart keys in Helm documentation. Thanks, [@charlottevdscheun](https://github.com/charlottevdscheun)!
- Fixed incorrect owner tags in Components docs. Thanks, [@aaronprice00](https://github.com/aaronprice00)!

### Dagster Plus

- Improved the Dagster+ agent's retry behavior during when it experiences outbound connection timeouts while a code location is being deployed.

## 1.11.9 (core) / 0.27.9 (libraries)

### New

- Subclasses of `Resolved` now support fields of type `dict[str, T]`.
- [ui] Added a new 'arrow' icon to the set of supported kind tags (thanks [@aleewen](https://github.com/aleewen)!)

### Bugfixes

- Launching a backfill of a non-subsettable multi-asset without including every asset will now raise a clear error at backfill submission time, instead of failing with a confusing error after the backfill has started.
- Fixed an issue where passing in an empty list to the `assetKeys` argument of the `assetsOrError` field in the GraphQL API would return every asset instead of an empty list of assets.
- [dagster-dbt] Fixed an issue that would cause the DbtCloudWorkspace to error before yielding asset events if the associated DBT Cloud run failed. Now, it will raise the error _after_ all relevant asset events have been produced.

### Dagster Plus

- Serverless pex builds now support pyproject.toml-based packages.

## 1.11.8 (core) / 0.27.8 (libraries)

### New

- A param `exclusions` was added to time window partition definitions to support custom calendars.
- The `dagster` library now supports `protobuf==6.x`
- [dg] `dg scaffold defs --help` now shows descriptions for subcommands.
- [dg] A new `dg check toml` command has been added to validate your TOML configuration files.
- [dagster-databricks] The `DatabricksAssetBundleComponent` has been added in preview. Databricks tasks can now be represented as assets and submitted via Dagster.
- [dagster-dbt] The DbtProjectComponent now takes an optional `cli_args` configuration to allow customizing the command that is run when your assets are executed.
- [dagster-dbt] The polling interval and timeout used for runs triggered with the `DbtCloudWorkspace` resource can now be customized with the `DAGSTER_DBT_CLOUD_POLL_INTERVAL` and `DAGSTER_DBT_CLOUD_POLL_TIMEOUT` environment variables.
- [ui] Added the ability to filter to failed/missing partitions in the asset report events dialog.
- [ui] A tree view has been added in the Global Asset Lineage.
- [telemetry] Telemetry disclaimer now prints to stderr.

### Bugfixes

- Fixed an issue that would require config provided to backfills to contain config for all assets in the code location rather than just the selected ones.

## 1.11.7 (core) / 0.27.7 (libraries)

### New

- `dg` will now report multiple detected errors in a configuration file instead of failing on the first detected error.
- It is now possible to supply run config when launching an asset backfill.
- Updated the root URL to display the Overview/Timeline view for locations with schedules/automations, but no jobs (thanks [@dschafer](https://github.com/dschafer)!)
- Added `tzdata` as a dependency to `dagster`, to ensure that declaring timezones like `US/Central` work in all environments.
- [dagster-dg-cli] Updated scaffolded file names to handle consecutive upper case letters (ACMEDatabricksJobComponent → acme_databricks_job_component.py not a_c_m_e_databricks_job_component.py)
- [dagster-dg-cli] Validating `requirements.env` is now opt-in for `dg check yaml`.
- [dagster-dbt] `DAGSTER_DBT_CLOUD_POLL_INTERVAL` and `DAGSTER_DBT_CLOUD_POLL_TIMEOUT` environment variables can now be used to configure the polling interval and timeout for fetching data from dbt Cloud.

### Deprecations

- [components] Removed deprecated and non-functional `asset_post_processors` fields from `SlingReplicationCollectionComponent` and `AirflowInstanceComponent`.

## 1.11.6 (core) / 0.27.6 (libraries)

### New

- Allow explicit git `platform` selection in `link_code_references_to_git`, thanks [@chazmo03](https://github.com/chazmo03)!

### Bugfixes

- Fixed issue causing `AutomationCondition.replace` to not update built-in sub-conditions that did not have an explicit label, thanks [@dschafer](https://github.com/dschafer)!
- Fixed an issue where assets were considered stubs if they were a stub in any code location.
- Projects using components no longer cause "job definitions changed while uploading" errors on older agent versions.
- [dagster-dbt] Fixed a bug that could cause execution to fail if `enable_code_references` was set to `True` on the `DagsterDbtTranslatorSettings`.

### Documentation

- Updated documentation of `dagster.yaml` to include the `nux` option, thanks [@dwisdom0](https://github.com/dwisdom0)!

### Dagster Plus

- Fix "Create a support ticket" dialog submissions.

## 1.11.5 (core) / 0.27.5 (libraries)

### New

- Static functions on classes decorated with `@template_var` can now optionally accept a `ComponentLoadContext` argument.
- [dg] A MCP server is available to expose `dg` CLI capabilities to MCP clients. See the `dg mcp` CLI group for details.
- [dagster-dbt] The `dagster-dbt` package no longer has a dependency on `dbt-core`.
- [dagster-dbt][preview] Users of the dbt Fusion CLI can now use the `dagster-dbt` package to run dbt commands with no changes to their existing dagster code. This support is still in preview as the format of the log messages produced by the dbt Fusion CLI is still subject to change. Let us know if you notice any incompatibilities.
- [dagster-databricks] Added a `PipesDatabricksServerlessClient` to support Databricks Serverless jobs with Dagster pipes.
- [dagster-databricks] Added additional options for cluster configuration (thanks [@jmccartin](https://github.com/jmccartin)!)

### Bugfixes

- Various bugfixes for backfills that target assets which change their partitions definition mid-backfill.
- [ui] Fixed issue that could cause errors related to the `ObjectMetadataValue` class.

### Documentation

- Added docs for using Spark Connect and Databricks Connect with Dagster.

## 1.11.4 (core) / 0.27.4 (libraries)

### New

- Schedules now support specifying a subset of asset checks to execute in a `RunRequest`.
- [dg] A new `docs integrations` cli is available for viewing an index of available integrations.
- [ui] Jobs can now be filtered with a selection syntax.
- [dagster-tableau] Dashboards containing hidden sheets are now correctly linked to upstream data sources.
- [dagster-tableau] Tableau sheets and dashboards now produce observation events instead of materialization events when using `refresh_and_poll` inside the `@tableau_assets` asset decorator.

### Bugfixes

- Fixed a set of issues with the asset backfill system that could, in rare cases, cause runs to be kicked off out of order or never be kicked off.
- Fixed issue where additional args passed into a PermissiveConfig object could not be accessed via dot notation (thanks [@CarlyAThomas](https://github.com/CarlyAThomas) and [@BoLiuV5](https://github.com/BoLiuV5)!)
- Duplicate definitions are no longer incorrectly created when including jobs for schedules & sensors when loading from a `defs` folder.
- [components] Fixed an incorrect import being generated when scaffolding a component in Python. (thanks, [@ajohnson5](https://github.com/ajohnson5)!)
- [dg] when assets are selected via `--assets`, other definitions types will no longer be displayed.

### Documentation

- Fixed typo in the `polars.md` example doc (thanks [@j1wilmot](https://github.com/j1wilmot)!)
- Fixed a typo in the ETL tutorial docs (thanks [@yumazak](https://github.com/yumazak)!)

## 1.11.3 (core) / 0.27.3 (libraries)

### New

- Introduced `AssetExecutionContext.load_asset_value`, which enables loading asset values from the IO manager dynamically rather than requiring asset values be loaded as parameters to the asset function. For example:
  ```python
  @dg.asset(deps=[the_asset])
  def the_downstream_asset(context: dg.AssetExecutionContext):
    return context.load_asset_value(dg.AssetKey("the_asset"))
  ```
- Expose asset_selection parameter for `submit_job_execution` function in DagsterGraphQLClient, thanks [@brunobbaraujo](https://github.com/brunobbaraujo)!
- Large error stack traces from Dagster events will be automatically truncated if the message or stack trace exceeds 500kb. The exact value of the truncation can be overridden by setting the `DAGSTER_EVENT_ERROR_FIELD_SIZE_LIMIT` environment variable.
- Added `databento`, `ax`, and `botorch` kind tags, thanks [@aleewen](https://github.com/aleewen) and [@CompRhys](https://github.com/CompRhys)!
- [dagster-k8s] Added the option to include `ownerReferences`s to k8s executor step jobs, ensuring that the step job and step pod are properly garbage collected if the run pod is deleted. These can be enabled by setting the `enable_owner_references` flag on the executor config.
- [components] Added `dg list component-tree` command which can be used to visualize the component tree of a project.
- [components] Added the ability to reference, load, and build defs for other components in the same project. In YAML, you may use the `load_component_at_path` and `build_defs_at_path` functions:

  ```yaml
  type: dagster.PythonScriptComponent

  attributes:
    execution:
      path: my_script.py
    assets:
      - key: customers_export
        deps:
          - "{{ load_component_at_path('dbt_ingest').asset_key_for_model('customers') }}"
  ```

### Bugfixes

- [components] Python component instances are now properly loaded from ordinary Python files.
- Fixed an issue that could cause asset backfills to request downstream partitions at the same time as their parent partitions in rare cases.
- Fixed a bug that could cause `@graph_asset`s to not properly apply the `AllPartitionMapping` or `LastPartitionMapping` to dependencies, thanks [@BoLiuV5](https://github.com/BoLiuV5)!
- Fixed a bug that could cause code locations to fail to load when a custom python AutomationCondition was used as the operand of `AutomationCondition.any_deps_match()` or `AutomationCondition.all_deps_match()`.
- The `create-dagster` standalone executable now works on all Linux versions using glibc 2.17 or later.
- [ui] Partition tags are now properly shown on the runs page, thanks [@HynekBlaha](https://github.com/HynekBlaha)!
- [ui] Using the "Retry from Asset Failure" option when retrying a run that failed after materializing all of its assets will now correctly indicate that there is no work that needs to be retried.
- [ui] The timeline tab on the Overview page now shows runs by sensor when they were launched by an automation condition sensor, instead of showing every row in the same "Automation condition" row.
- [ui] Fixed an issue where filtering to an asset group on the lineage page did not apply the correct repository filter in code locations with multiple repositories.
- [ui] Fixed an issue where asset checks referencing asset keys that did not exist in the asset graph did not appear in the Dagster UI.
- [ui] Fixed occasional crashes of the asset graph on the asset lineage tab.
- [dagster-dbt] The `@dbt_assets` decorator and associated APIs no longer error when parsing dbt projects that contain an owner with multiple emails.

### Documentation

- Fixed typos in the ELT pipeline tutorial, thanks [@aaronprice00](https://github.com/aaronprice00) and [@kevJ711](https://github.com/kevJ711)!
- Fixed typos in components docs, thanks [@tintamarre](https://github.com/tintamarre)!
- Fixed error in Sling docs, thanks [@nhuray](https://github.com/nhuray)!
- Updated the `AutomationCondition.replace` type signature to provide callers more information about the returned `AutomationCondition`, thanks [@dschafer](https://github.com/dschafer)!

### Dagster Plus

- Catalog search now uses a similar syntax to the selection syntax for filtering by attribute (eg: `Code location: location` -> `code_location: location`.

## 1.11.2 (core) / 0.27.2 (libraries)

### New

- The `dagster` package now supports Python 3.13.
- [dagster-tableau] Tableau assets can now be subsetted and materialized individually. [#31078](https://github.com/dagster-io/dagster/pull/31078)
- [dagster-snowflake-polars] The new `dagster-snowflake-polars` package adds a `SnowflakePolarsIOManager` that can be used to read and write Snowflake tables using Polars.

### Bugfixes

- [ui] Fixed some cases where strings would be incorrectly middle-truncated.

### Documentation

- [dbt] Fixed incorrect reference to `dbt_profiles.yml` in the `dagster-dbt` tutorial (thanks [@EFox2413](https://github.com/EFox2413)!).
- [dbt] Added documentation for the new dbt Cloud integration.

### Dagster Plus

- [ui][observe] You can now bulk add/remove assets to/from your favorites.

## 1.11.1 (core) / 0.27.1 (libraries)

### New

- `dagster definitions validate` will now raise an exception if there are invalid partition mappings between any assets in your asset graph (for example, an upstream and downstream asset with time-based partitions definitions using different timezones).
- Performance improvements for run dequeuing when there are many queued runs using pools.
- [ui] For times in the last two days, Dagster UI now shows e.g. "47 hours ago" instead of "2 days ago."
- [ui] Asset checks now show whether they are `blocking`.
- [dagster-tableau] Tableau workbooks fetched in Dagster can now be filtered and selected using the WorkbookSelectorFn.

### Bugfixes

- `@graph` now correctly allows omitting inputs when the destinations of an input mapping have a default value.
- `@record` classes no longer create problematic namespace conflicts with the symbol "check."
- [ui] Filtering by partition on the Asset Events view now works as expected.
- [ui] Assets without definitions can now be properly wiped in the Asset Catalog.

### Documentation

- Added clearer setup instructions for Windows and Linux users to the Contributing documentation, thanks [@oohwooh](https://github.com/oohwooh)!
- Fixed broken links in the Contributing documentation, thanks [@emmanuel-ferdman](https://github.com/emmanuel-ferdman)!

### Dagster Plus

- [ui] Fixed an issue that prevented status filtering from working within the selection syntax.

### dg & Components

- Fixed an issue where `dg scaffold github-actions` would invoke the `dg` CLI with outdated parameters for serverless orgs.
- [dagster-dlt] Fixed an issue where the default scaffolded dlt load led to an invalid asset key.

## 1.11.0 (core) / 0.27.0 (libraries)

## Major changes since 1.10.0 (core) / 0.26.0 (libraries)

### Components — Configurable, reusable building blocks for data pipelines (now stable)

Components, first released as Preview in 1.10.6, have reached Release Candidate status. APIs are stable, fully documented, and are the recommended, production-ready defaults for new Dagster projects.

- **Simplified interface:** A short YAML block in `defs.yaml`, or a lightweight `Component` subclass in Python, lets you spin up arbitrary Dagster definitions (such as assets, resources, schedules, checks, and more), removing boilerplate while keeping every definition type-checked.
- **Custom components:** Subclassing `Component` lets you wrap any internal script or third-party tool behind a strongly-typed interface; get the same autocompletion and docs as first-party integrations.
- **Pythonic templating:** Register variables or helpers with `@template_var` so pipeline authors edit parameters directly in YAML without touching Python. Optional inline components keep small bits of Python co-located.
- **Powerful tooling:** High quality errors, strongly-typed schemas, rich CLI support, and auto-generated docs directly in the UI.
- **Read the docs:** https://docs.dagster.io/guides/build/components/

### `dg` — **the everything-CLI for developer experience (now stable)**

The `dg` CLI provides a single surface for scaffolding, local iteration, execution, and static analysis; introduced as Preview in 1.10.6, it has also reached Release Candidate status.

- **Scaffolding:** Namespaced scaffold commands such as `dg scaffold defs dagster.asset assets.py`, `dg scaffold component …` to quickly generate definitions without boilerplate.
- **Local development & ad-hoc execution:** `dg dev` spins up local instance with UI; `dg launch` runs jobs and assets from the CLI.
- **Introspection & checks:** `dg list` enumerates definitions; `dg check` validates YAML and Python code.
- **Utility bundle:** `dg utils` provides support for Cursor/VSCode schema setup, JSON-schema export, and deep component inspection.
- **CLI reference:** https://docs.dagster.io/api/dg/dg-cli

### `create-dagster` — one-shot project scaffold

**`create-dagster`** scaffolds a ready-to-run Dagster project or workspace in one command (pipx, uvx, brew, curl friendly).

- **`create-dagster project`** supersedes the **`dagster project scaffold`** flow with the modern `src/` + `defs/` layout and a pre-wired local **`dg`** CLI, with no active Python environment required.
- **Docs:** https://docs.dagster.io/guides/build/projects/creating-a-new-project

### Core Orchestration

- **Retry from asset failure with multi‑assets** – a new re‑execution option allows rerunning only failed assets in multi-asset steps, rather than all assets within a failed step.
- **Checks emitted from ops**  – **`AssetCheckEvaluation`** objects can now be yielded from within ops.
- **Per‑asset hooks** – **`@asset`** now accepts a **`hooks`** argument for success/failure callbacks.
- **Backfill improvements**
  - **`BackfillPolicy`** is now GA
  - Backfills can now use a threadpool for more efficient run submission. By default, the daemon will now use 4 workers.
- **Concurrency enhancements** – run blocking is now on by default for concurrency pools, preventing oversubscription when scheduling runs.
- **FreshnessPolicy** — A new **`FreshnessPolicy`** API is introduced, replacing the deprecated `FreshnessPolicy` API (which has been renamed to `LegacyFreshnessPolicy`). The API is under active development, and will eventually also supersede freshness checks as the primary way of specifying and evaluating asset freshness. For more details, check out the [GitHub announcement](https://github.com/dagster-io/dagster/discussions/30934) and the [docs](https://docs.dagster.io/guides/labs/freshness).

### UI

- **Unified asset selection syntax** lets you combine lineage traversal, attribute filters, and boolean logic in a single expression; the same syntax powers Alerts, Insights, Saved Selections, the Asset Catalog, and Components YAML. An analogous op-selection syntax is available in the Gantt view of a single run. [[docs](https://docs.dagster.io/guides/build/assets/asset-selection-syntax/reference)]
- **Redesigned, customizable asset-graph nodes** with health overlays and deeper zoom.
- **Runs › Backfills** consolidates all backfill activity under the Runs page for faster navigation.

### Integrations

- **Fivetran integration GA:** the **`FivetranWorkspace`** resource is now GA [[docs](http://docs.dagster.io/integrations/libraries/fivetran)].
- **Airflow (Beta):** Airflow Component lets you surface Airflow DAGs inside Dagster for mixed-orchestrator observability [[docs](http://docs.dagster.io/migration/airflow-to-dagster/airflow-component-tutorial)].
- **dbt Cloud (Beta):** first-class job launches and lineage capture [[docs](http://docs.dagster.io/integrations/libraries/dbt/dbt-cloud)].
- **Apache Iceberg (Preview):** Iceberg IOManager writes/reads lake-house tables [[docs](http://docs.dagster.io/integrations/libraries/iceberg/)].
- **Integrations Marketplace (Preview):** “Integrations” tab to browse first- and third-party integrations natively in Dagster UI (enable via User Settings → “Display integrations marketplace”).

## Changes since 1.10.21 (core) / 0.25.21 (libraries)

### New

- `MaterializeResult` now optionally supports a `value` parameter. If set, the asset's IOManager will be invoked. You may also optionally annotate your return types with `-> MaterializeResult[T]` to indicate the specific value type you expect.
- Allow importing `FreshnessPolicy` from `dagster.deprecated`.
- Adds a custom error message when importing `FreshnessPolicy` from the `dagster` module.
- `freshness_policy` parameter now used to pass the new freshness policies (`InternalFreshnessPolicy`) to asset specs, asset decorator, etc.
- Removed `@preview` from `@definitions`.
- [components] Introduce `build_defs_for_component`, which can be used to build defs from a component instance outside of a `defs` folder.
- [components] Removed `@preview` from `DefsFolderComponent`.
- [components] Removed `@preview` decorator from `load_from_defs_folder` and enhanced its documentation with detailed usage instructions and examples.
- [components] The `asset_post_processors` field on `SlingReplicationCollectionComponent` and `AirflowInstanceComponent` is no longer supported, and has been replaced with the top-level `post_processors` field.
- [dagster-tableau] Tableau workbooks fetched in Dagster can now be filtered and selected using the WorkbookSelectorFn.
- [dagster-dbt] `dagster-dbt` now supports dbt-core 1.10.
- [dagster-dbt] dbt tests with error severity are now modeled as blocking asset checks, ensuring that if a run fails due to a dbt test failure, the connected model is included in a retried run if it is retried using the experimental "Enable retries from asset failure" feature. This change should not result in any behavior changes during execution since the dbt cli already fails the step and any downstream models if dbt tests fail with error severity, but could change the behavior that depends on blocking tests.
- [dagster-sigma] When fetching data from the sigma API, the `SigmaOrganization` resource will now use an exponential backoff strategy in response to getting rate limited instead of immediately failing.
- [dagster-sling] Removed `asset_post_processors` on `SlingReplicationCollectionComponent` and uses generic `post_processing` key at top-level instead.
- [dagster-pandera] Adds support for version 0.24.0 of the `pandera` library to `dagster-pandera`, dropping support for pandera 0.23.1 and below.
- [ui] Show whether an asset check is `blocking`.

### Bugfixes

- [dagster-dlt] Fixed an issue where the default scaffolded dlt load led to an invalid asset key.
- Fixed a bug with `DAGSTER_GRPC_SENSOR_TIMEOUT_SECONDS` not being propagated through from daemon to code servers, resulting in the sensor still timing out at 60 seconds if the `dagster code-server start` entrypoint was used.
- [dagster-sling] Fixed an issue with the `SlingResource` that could cause values specified with `EnvVar`s to provide the env var name instead of the env var value to the sling replication configuration.
- [ui] Fix timestamps on the "Recent events" view on some assets.
- [ui] Fix "View" link color on code location status toasts.

### Breaking Changes

- `Definitions` and `AssetsDefinition` will now error if they get different `AssetSpec`s with the same key.
- Renamed `FreshnessPolicy` to `LegacyFreshnessPolicy`.

### Deprecations

- [dagster-sling] The `SlingReplicationCollectionComponent` is now configured by passing `connections` directly. This means that the `sling` yaml field and the `resource` python argument are both deprecated, and will be removed in a future release. The `connections` field in yaml now shares a format with Sling's `env.yaml`.
- [components] The `load_defs` entrypoint has been deprecated in favor of `load_from_defs_folder`, which takes a single path for a folder to load definitions from rather than a module object.
- [components] The no longer recommended `inline-component` subcommand of `dg scaffold defs` is now hidden from --help.
- [components] `load_defs` is no longer public.

### Dagster Plus

- The billing page has been updated to show available plans front-and-center and recommend a plan based on trial usage.
- The trial "days remaining" banner and "choose a plan" CTAs have been re-designed.

## 1.10.21 (core) / 0.26.21 (libraries)

### New

- [dagster-tableau] The `tableau_assets` decorator is now available to create the asset definitions of all materializable assets in a given Tableau workspace. These assets can be subsetted and materialized using the `TableauCloudWorkspace.refresh_and_poll` method.
- [dagster-tableau] The deprecated `get_*_asset_key` methods on the `DagsterTableauTranslator` class have been removed.
- [ui] Show tags for a Job on the sidebar of the Job page. [#30728](https://github.com/dagster-io/dagster/pull/30728)

### Bugfixes

- Fixed a bug where "falsey" defualt config values were not showing up in the launchpad. This has been fixed for all cases except the empty dictionary.
- Fixed an issue with the new "re-execute from asset failure" functionality that could cause additional steps to be included if the job was previously re-executed from step failure.
- Fixed an issue where the `staleStatusByPartition`, `staleCausesByPartition`, and `dataVersionByPartition` fields on the graphql `AssetNode` would fail when called on an asset with dynamic partitions.
- [dagster-dbt] Fixed an issue where creating a DagsterDbtTranslator that didn't call the parent class's constructor in its `__init__` method would raise an Exception during execution.
- [dagster-sling] Removed upper-bound pin on the `sling` dependency.
- [dagster-sling] Fixed an issue with the `SlingResource` that could cause values specified with `EnvVar`s to provide the env var name instead of the env var value to the sling replication configuration.
- [dagster-fivetran] Introduced a `dagster-fivetran snapshot` command, allowing Fivetran workspaces to be captured to a file for faster subsequent loading.

### Dagster Plus

- [ui] The integrations marketplace (currently behind a feature flag) now allows you to create, edit, and delete private packages.

### dg & Components

- Added `FunctionComponent`, `PythonScriptComponent`, and `UvRunComponent` to make it easier to define arbitrary computations that execute assets or asset checks when invoked.
- Weekly and arbitrary time-window partitions can now be provided to the `partitions_def` asset customization in YAML.
- A clean and informative error message is now printed when an invalid set of parameters is passed to `dg scaffold defs ...`.
- Component asset specs now allow specifying partition definitions through the `partitions_def` key.
- The `dg` cache is no longer operative, since `dg` now operates in the same python environment as the projects it manipulates. Config options for the cache have been removed.
- The `load_defs` entrypoint has been deprecated in favor of `load_from_defs_folder`, which takes a single path for a folder to load definitions from rather than a module object.
- The `asset_post_processors` field on `SlingReplicationCollectionComponent` and `AirflowInstanceComponent` is no longer supported, and has been replaced with the top-level `post_processors` field.
- Fixed an issue where dg projects using `autoload_defs=true` could not be deployed to Dagster+.
- Removed `@preview` from `Component`.
- `ComponentLoadContext` is now frozen and no longer in preview.
- `Resolved` subclasses now support `Enum` fields.

## 1.10.20 (core) / 0.26.20 (libraries)

### New

- The `@asset` decorator now supports a `hooks` argument to allow for functions to be executed on asset success / failure (thanks @brunobbaraujo)!
- The log message produced when an asset check is evaluated now includes its pass / fail state.
- The `@multi_asset_check` decorator now supports the `pool` argument.
- [dagster-dbt] The `DagsterDbtTranslator` class now has a `get_asset_check_spec` method which can be overridden to customize the `AssetCheckSpecs` that are produced for each individual dbt test.

### Bugfixes

- Fixed an issue where setting the non-public `blocking` attribute on an `AssetCheckSpec` would halt execution of the step as soon as any asset check failure was emitted, even if the step still had asset materializations or check evaluations to emit that were not downstream of the failed asset check. Now that this issue has been fixed, the `blocking` attribute on `AssetCheckSpec` has been made a public attribute. If you were making use of the `blocking` attribute on AssetCheckSpec before it was public and relying on the previous behavior, you should exit from your asset evaluation function after emitting an AssetCheckFailure from within your multi-asset in order to halt further execution of the step.
- Fixed a bug where `GraphDefinition.to_job()` would not work if an op had a custom IO manager key.
- Fixed an issue that would cause `.allow()` and `.ignore()` applications to not propagate through `.since()` automation conditions.
- Fixed a bug where assets with cross-location dependencies could sometimes be incorrectly reported as "Unsynced".
- Fixed an issue where `dagster dev` was sometimes failing to load code locations with a "Deadline Exceeded" error unless the `--use-legacy-code-server-behavior` flag was set.
- The backfill daemon can now be configured to use a threadpool executor via helm (thanks @hynekblaha)!
- [dagster-gcp] Added a `google-cloud-bigquery>=1.28.3` pin to correctly reflect the lowest compatible version.

### Breaking Changes

- [ui] Moved legacy Auto-materialize (global AMP) tab from Overview to Automations.

### Dagster Plus

- Fixed an issue where certain rare network conditions could cause steps to hang while uploading compute logs after a step finished.
- [ui] For users with the new Observe UIs enabled, the Asset Health and Resources tabs are no longer shown on the Timeline page.

### dg & Components (Preview)

- Fix a bug with `dg check yaml` where valid component type names were rejected if they were not registered (i.e. visible from `dg check components`).
- `dg create-dagster` now warns when scaffolding a project or workspace if it is not the latest version.
- The `project.registry_modules` configuration can now accept wildcards (e.g. `foo_bar.components.*`). This will register any module matching the pattern with `dg`.
- The `env` YAML function now errors if the specified env var is unset. Default values can be provided as an additional argument: `{{ env('MY_ENV_VAR', 'default') }}`
- defs.yaml files can now specify a component in the module where it is defined, as opposed to just the module where it is exposed in the `dg` registry.
- The `PipesSubprocessScriptCollectionComponent` has been removed.
- Running dg commands such as `dg check defs` and `dg dev` in a project folder that is part of the workspace will now only apply to that project, instead of every project in the workspace.
- Scaffolded projects no longer contain a "components" directory or a Python `dagster_dg_cli.plugin` entry point.
- Scaffolded components can now be placed anywhere within a project module hierarchy.
- The entry point group used by shared libraries exposing custom components to `dg` has been renamed from `dagster_dg_cli.plugin` to `dagster_dg_cli.registry_modules` (projects no longer need to define an entry point group at all).
- `dg list plugin-modules` has been renamed to `dg list registry-modules`.
- `dg list defs` now supports configuring output columns with the `--columns/-c` option.
- [dagster-airbyte] Introduced a `AirbyteCloudWorkspaceComponent` which can be used to pull in Airbyte Cloud connections into Dagster

## 1.10.19 (core) / 0.26.19 (libraries)

### New

- The database table used by the `DbIOManager` is now configurable via `"table"` output (asset) metadata key [#30310](https://github.com/dagster-io/oss/pull/30310)
- Changed default settings for backfill daemon to `use_threads=True`, `num_workers=4`. Thanks [@HynekBlaha](https://github.com/HynekBlaha)!
- A new function `build_asset_check_context` can be used to build asset check contexts for direct invocation.
- Changed `Definitions.get_all_asset_specs` to only return assets directly passed in as AssetSpecs or AssetsDefinitions.
- Removed `selection` argument from `Definitions.map_asset_specs`. If selection is needed use the new `Definitions.map_resolved_asset_specs`.
- `Definitions.get_job_def` now warns when it finds an unresolved job or no job.
- Changed `Definitions.get_assets_def` to return an AssetsDefinition without resolving if it was passed in directly.
- [dagster-dbt] `build_schedule_from_dbt_selection` now supports a `selector` argument, allowing you to use yaml-based selectors.
- [dagster-k8s] Pods created by the Kubernetes run launcher and executor from Dagster Plus now include the `dagster/deployment-name` label.
- [dagster-pipes] Pipes execution errors are no longer treated as framework errors, meaning they properly invoke RetryPolicies.
- [helm] Backfill daemon configuration now supported. Thanks [@HynekBlaha](https://github.com/HynekBlaha)!
- [ui] Show relative start time on runs in run timeline hover lists. [#30327](https://github.com/dagster-io/oss/pull/30327)

### Bugfixes

- [ui] Fixed live updating of asset materialization statuses in asset graph.

### dg & Components (Preview)

- Running dg commands like `dg check defs` and `dg dev` in a project folder that is part of the workspace will now only apply to that project, instead of every project in the workspace.
- `dg list defs` now supports the `--assets/-a` option, to show only assets matching the provided selection.
- `dg list defs` now supports a `--path` argument to subset the defs files shown.
- The `create-dagster workspace` command now accepts the same required path argument as the `create-dagster project` command, instead of defaulting to a `dagster-workspace` subfolder of the current working directory.
- The entry point group used by shared libraries exposing custom components to dg has been renamed from `dagster_dg_cli.plugin` to `dagster_dg_cli.registry_modules` (projects no longer need to define an entry point group at all).
- `dg list plugin-modules` has been renamed to `dg list registry-modules`.
- Newly scaffolded projects no longer contain a "components" directory or a Python `dagster_dg_cli.plugin` entry point.
- Newly scaffolded components can now be placed anywhere within a project module hierarchy.
- `Resolvable` subclasses can now use bare `dict` and `list` as field types.
- Resolving a `Resolvable` subclass will no longer change empty strings to `None`.
- Users can define multiple `@definitions`-decorated functions in a single module in the `defs` hierarchy and they are automatically merged and incorporated into the project.
- Added `@component_instance` to replace `@component`. This allows multiple component instances in a python file.
- Fixed an issue where `dg` commands would sometimes output extra `dagster_telemetry_logger` lines to stdout at the end of commands.
- Added `@template_var` as an alternative approach for defining variables in a templating context.

## 1.10.18 (core) / 0.26.18 (libraries)

### New

- `BackfillPolicy` is now marked as generally available (GA).
- Optimized the order of the `@asset` decorator overloads to make custom wrappers around the asset decorator easier. Thanks [@jonathanunderwood](https://github.com/jonathanunderwood)!
- [dagster-slack] Added `get_client()` to SlackResource.

### Bugfixes

- `Definitions` and `AssetDefinition` will now warn if they get different `AssetSpec`s with the same key. This will become an exception in 1.11.
- Functions that load all definitions from modules like `load_definitions_from_modules` now handle duplicate `AssetSpec`s.
- Fixed typo in logging. Thanks [@eli-b](https://github.com/eli-b)!
- [dagster-dbt] An issue occurring when using dbt selection arguments with a dbt project using saved queries and semantic models has been fixed.
- [dagster-fivetran] Fixed an issue with `load_assets_from_fivetran_instance` where assets whose asset keys have been customized using a Fivetran translator would lead to an exception.

### Documentation

- Fixed grammar issues in GCP docs. Thanks [@D1n0](https://github.com/D1n0)!
- Fixed missing docs for `required_resource_keys` in `@sensor`. Thanks [@seyf97](https://github.com/seyf97)!

### Breaking Changes

- `Definitions` and `AssetDefinition` will now warn if they get different `AssetSpec`s with the same key. This will become an exception in 1.11.

### Dagster Plus

- [dagster-cloud-cli] Added a `--wait` to the `dagster-cloud job launch` command that makes it wait until the launched run copmletes. Thanks [@stevenayers](https://github.com/stevenayers)!
- [fix][dagster-cloud-cli] Fixed an issue where the `dagster-cloud` cli failed to deploy PEX projects on python 3.12 in certain environments without setuptools already installed.

### dg & Components (Preview)

- The `dg` CLI is now installed in each project's Python environment instead of as a global tool. If you previously had `dg` installed globally and are upgrading, first uninstall the global dg tool (`uv tool uninstall dagster-dg` or `pip uninstall dagster-dg`) and add `dagster-dg-cli` as a dependency to each of your projects. Newly scaffolded projects will automatically include the `dg` CLI going forward.
- A new `create-dagster` CLI has been added for scaffolding projects instead of workspaces. `uvx create-dagster project` has replaced `dg scaffold project`, and `uvx create-dagster workspace` has replaced `dg scaffold workspace`. The commands take identical arguments.
- Definitions and component instances are now scaffolded with `dg scaffold defs <scaffolder>` instead of `dg scaffold <scaffolder>`.
- The `component.yaml` file to specify a component instance is now called "defs.yaml". "component.yaml" will remain supported for several weeks, but is deprecated.
- The `lib` folder in newly scaffolded projects has been renamed to "components".
- `dg scaffold component-type` has been renamed to `dg scaffold component`.
- `dg list plugins` has been renamed to `dg list plugin-modules` and now outputs only plugin module names, not plugin objects.
- `dg list component` now lists component types instead of instances.
- Exports from `dagster.components` are now available in the top-level `dagster` module.
- Added `@component_instance` to replace `@component`, which allows multiple component instances in a python file.
- If you type a partial component name for `dg scaffold defs <component>`, you will now be prompted with possible matches.
- When component classnames are unique, you can now use just the classname as an alias for the fully qualified name when running `dg scaffold defs <component>`.
- `dg launch` now supports passing config files through `--config/-c`.
- Added `Component.from_attributes_dict` and `Component.from_yaml_path` to help with testing.
- Added `dagster.components.testing.component_defs` utility to help with testing components.
- Scaffolded schedules and sensors in `dg` are now loadable by default.
- `dg scaffold defs inline-component` can now be used to create inline components and corresponding instances.
- `dg list defs` now outputs resources.
- [fix] The `dagster-dbt` cli flag `--components` flag now correctly finds `DbtProjectComponent` again.
- [dagster-fivetran] Added a `FivetranAccountComponent` which can be used to pull in Fivetran connections into Dagster.
- [dagster-dlt] The DltLoadCollectionComponent scaffolder no longer attempts to automatically construct loads for the given source and destination type.
- Fixed an issue where components failed to load when using `load_assets_from_airbyte_instance` or other APIs that return a `CacheableAssetsDefinition`.

## 1.10.17 (core) / 0.26.17 (libraries)

### Bugfixes

- Fixed an issue where an error was displayed in the UI while viewing run logs
- [dagster-dbt] Fixed an issue occurring when using dbt selection arguments with a dbt project using semantic models.

## 1.10.16 (core) / 0.26.16 (libraries)

### New

- `typing_extensions` is now pinned to `>=4.11.0` instead of `>=4.10.0`.
- [ui] Viewing an automation condition evaluation now automatically expands the set of applicable sub-conditions.
- [ui] Added the ability to navigate from an automation condition evaluation to upstream automation condition evaluations.
- [ui] Added an asset graph node facet for viewing automation conditions and the most recent evaluation. This can be enabled in the user settings via a feature flag (`Enable faceted asset nodes`).
- [ui] A new experimental integrations marketplace tab is now available and can be enabled in your user settings via a feature flag (`Display integrations marketplace`). It provides easy access to the gallery of dagster-supported plugins.

### Bugfixes

- Fixed an issue with the `ExternalNotebookDataRequest` GRPC call that would allow it to access files outside of the current directory.
- Fixed an issue that would cause `op_tags` set on `@observable_source_asset`s to be dropped from the underlying step context object when executed.
- Fixed an issue where `dagster dev` would sometimes raise a gRPC error when loading several code locations at once.
- Fixed an issue where setting an environment variable to the string "false", "0" or "None" for a dagster config field using a `BoolSource` would evaluate to True.
- Fixed an issue where specifying `executable_path` in a workspace.yaml file to run code locations in a different virtual environment would not correctly inherit the PATH of that virtual environment in the code location.
- [dagster-dbt] Fixed an issue causing dbt CLI invocation to fail when materializing assets when `OpExecutionContext` was used as the type hint for the context.
- [dagster-deltalake] Corrected the `timeout` property data type in `ClientConfig` to be str instead of int (thanks, [@edsoncezar16](https://github.com/edsoncezar16)!)

### Documentation

- Added additional config fields to the `K8sRunLauncher` example (thanks, [@nishan-soni](https://github.com/nishan-soni)!)
- Corrected broken links on the automation landing page (thanks, [@briandailey](https://github.com/briandailey)!)

### Dagster Plus

- [ui] Alert policy event tags no longer appear red and yellow outside of the policy notification history.

### dg & Components (Preview)

- Added suggestions to component model error messages when using built-in models for common classes such as `AssetKey` and `AssetSpec`.
- `dg list env` now displays whether env vars are configured in each Dagster Plus scope.
- Introduced `Resolver.passthrough()` to avoid processing fields on a component model.
- `ResolvedAssetKey` is now exported from `dagster.components`.
- `dg init` has been removed. `dg scaffold project` and `dg scaffold workspace` should be used instead.
- Fixed an issue where `dg dev` failed with a temporarily file permissions error when running on Windows. Thanks [@polivbr](https://github.com/polivbr)!

## 1.10.15 (core) / 0.26.15 (libraries)

### New

- Added a config section to `dagster.yaml` to enable submitting backfill runs in a threadpool.
- Expanded definition time validation for partition mappings to avoid runtime errors querying asset status.
- [ui][beta] You can now re-execute a run that targeted a multi-asset from the point of asset failure instead of step failure, meaning only assets that failed or were skipped will be re-executed. To enable this option, turn on the `Enable retries from asset failure` feature flag in your user settings.
- [ui] Made it easier to select and copy image names for code locations.
- [ui] Added asset lineage navigation within the automation condition evaluation tree.
- [ui] Viewing an evaluation tick now auto-expands the set of applicable automation conditions.
- [ui] Added an asset graph node facet for viewing automation conditions and the most recent evaluation in the global asset graph.
- [dagster-fivetran] The `FivetranWorkspace` resource is now marked as generally available (GA).

### Bugfixes

- Changed asset wipes to also wipe associated asset check evaluations.
- [dagster-fivetran] Fixed an issue causing the Fivetran integration to fail when the schema config does not exist for a connector.

### Documentation

- Fixed a broken link in the airflow migration docs. Thanks [@jjyeo](https://github.com/jjyeo)!
- Updated example snippet to include a missing type hint. Thanks [@agrueneberg](https://github.com/agrueneberg)!

### Deprecations

- [dagster-fivetran] The `FivetranResource` resource is now deprecated. Use the new `FivetranWorkspace` resource instead.

### dg & Components (Preview)

- Changed `Scaffolder.scaffold` to have the params object as an attribute of the `ScaffoldRequest` object instead of a dictionary. This is a breaking change for those who have implemented a custom scaffolder.
- Added support for scaffolding resources via `dg scaffold dagster.resources path/to/resources.py`.
- Added support for the usage of `@definitions` in the `defs` hierarchy.
- Dagster components now include code references by default. When viewing an asset emitted by a component in the asset catalog, this will allow you to jump to the backing `component.yaml` file in your editor.
- [dagster-dbt] `DbtProjectComponent` fields now properly evaluate templates.
- [dagster-sling] Updated the SlingReplicationCollectionComponent from using the `asset_attributes` parameter to `translation`, in order to match our other integration components.
- Fixed an issue where `dg dev` failed with a temporary file permissions error when running on Windows. Thanks [@polivbr](https://github.com/polivbr)!

## 1.10.14 (core) / 0.26.14 (libraries)

### New

- [dagster-tableau] Refined Tableau integration for API 3.25 or greater.
- [dagster-tableau] Data sources with extracts can now be materialized in Tableau assets created with `build_tableau_materializable_assets_definition`.
- [ui] Added kinds tag for treasuredata.
- [ui] Add Supabase kind icon.

### Bugfixes

- Fixed a bug which could cause an error when calling `MultiPartitionsDefinition.has_partition_key()` on invalid keys.
- Fixed a bug where the default multiprocess executor would fail runs where the child process for a step crashed, even if a retry policy resulted in a successful retry of that crashed step.
- Fixed a bug with `AutomationCondition.initial_evaluation` which could cause it to return `False` for an asset that went from having a condition, to having no condition at all, back to having the original condition again.
- [ui] Fixed an issue which could cause the "Target" field of AutomationConditionSensorDefinitions to render incorrectly when exactly one asset check was defined in a code location.
- [dagster-dbt] Fix `DagsterDbtTranslatorSettings.enable_source_tests_as_checks` returning duplicate asset checks.

### Documentation

- Added a sample Dagster+ ECS CloudFormation template which incorporates private subnets.
- Fixed incorrect storage values in the Fargate task section of the AWS deployment guide, thanks [@alexpotv](https://github.com/alexpotv)!
- Updated log stream docs, thanks [@jjyeo](https://github.com/jjyeo)!
- Fixed broken code in the configurable resources guide, thanks [@nightscape](https://github.com/nightscape)!

### Deprecations

- `dagster.InitResourceContext.dagster_run` has been deprecated in favor of `InitResourceContext.run`.

### dg & Components (Preview)

- [dagster-k8s] PipesK8sComponent has been added.
- Dagster components no longer change the working directory while they are being loaded. This allows components to store relative paths and ensure that they will still work when accessed outside of the component loading codepath. This change may affect user-defined components that depend on `Path.cwd()` or `os.getcwd()`. Instead, you should use a path relative to the current source file when loading paths in a component, using the `context.resolve_source_relative_path` method (see `resolve_dbt_project` in `DbtProjectComponent` for an example).
- Added `dagster.job` scaffolder.
- [dagster-dbt] The `DbtProjectComponent` now has a `translation_settings` argument for adjusting `DagsterDbtTranslatorSettings`.
- [dagster-dbt][fix] `DbtProjectComponent` fields now properly evaluate templates.
- Fixed docstring for `load_defs` entrypoint, thanks [@mattgiles](https://github.com/mattgiles)!

## 1.10.13 (core) / 0.26.13 (libraries)

### New

- If an unselected asset check is executed during a run, the system will now warn instead of throwing a hard error.
- When evaluating `AutomationCondition.any_deps_match` or `AutomationCondition.all_dep_match` with an allow / ignore specified, an error will no longer be produced if the provided asset selection references an asset key that does not exist.
- Added the ability to restrict the list of ports that `dagster dev` is allowed to use to open subprocesses when running on Windows, by setting the `DAGSTER_PORT_RANGE` env var to a string of the form `<start>=<end>` - for example "20000-30000".
- [dagster-aws] The S3 sensor's `get_objects` now returns an empty list if no new files can be found since the `since_last_modified` parameter. Thanks [@bartcode](https://github.com/bartcode)!
- [dagster-dbt] `@dbt_assets` and `build_dbt_manifest_asset_selection` now support a `selector` argument, allowing you to use yaml-based selectors.
- [dagster-k8s] improved run monitoring when running with increased backoff limits. Thanks [@adam-bloom](https://github.com/adam-bloom)!

### Bugfixes

- Fixed a bug with `AutomationCondition.initial_evaluation` which could cause it to return `False` for an asset that went from having a condition, to having no condition at all, back to having the original condition again.
- Fixed a bug that would cause the `AutomationCondition.any_deps_updated()` condition to evaluate to `False` when evaluated on a self-dependency.
- Fixed a bug in the `quickstart_aws` example. Thanks [@Thenkei](https://github.com/Thenkei)!
- [ui] Fixed navigation between asset tabs by no longer preserving query parameters from one tab to the next.
- [ui] Fixed an issue where the asset graph looked like it was still loading when it wasn't.

### Documentation

- Added Scala Spark / Dagster Pipes guide.

### dg & Components (Preview)

- [dg] Error message when an invalid configuration file is detected is now shorter and more clear.
- [components] Descriptions and examples have been restored for core models such as `ResolvedAssetSpec`. `description` and `examples` arguments have been added to `Resolver` for documenting fields on non-pydantic model based `Resolvable` classes.

## 1.10.12 (core) / 0.26.12 (libraries)

### New

- [ui] Removed the `By partition` grouping view for recent events for assets that do not have a definition in the workspace.
- [ui] The asset graph now displays asset health information when the new Observe UI feature flag is enabled.
- [ui] A new feature flag allows you to customize the appearance of assets on the asset graph by enabling and disabling individual facets.
- [ui] Fixed a bug that prevented filtering asset events by type.
- [dagster-k8s] K8sPipeClient failures will now include the last 100 lines of the logs of the pod that failed, instead of the full log output.

### Bugfixes

- Fixed an issue which caused multi assets that were automatically broken apart in some contexts to remain separated even in cases where this was not necessary to maintain execution dependencies.
- Fixed a bug that would cause multi-assets defined with `can_subset=True` to error when using `dagster-pipes` if not all outputs were emitted.
- [ui] Fixed an issue where the asset graph looked like it was still loading when it wasn't.

### Documentation

- [docs] New integration pages for [Polars](https://docs.dagster.io/integrations/libraries/polars) and [Patito](https://docs.dagster.io/integrations/libraries/patito).

### dg & Components (Preview)

- `dg` will now fail with an error message if it's version is below the minimum supported version for the version of `dagster` in your environment.
- `dg` now checks for new versions and prompts the user to update. The check runs automatically at `dg` startup once per day.
- `dg` will now emit a warning prompting the user to reinstall the package if it detects an entry point in project metadata that does not show up when running in `dg list plugins`.
- `dg list defs` now collapses long system stacktraces [#29507](https://github.com/dagster-io/oss/pull/29507)
- Added `dagster.multi_asset` scaffolder
- Added `dagster.asset_check` scaffolder
- Fixed a bug where `dg list defs` would crash if anything was written to stdout while loading a project's definitions.
- The default location for the `dg` user config file on Unix has been moved from `~/.dg.toml` to `~/.config/dg.toml`. `~/.config` can be overridden by setting `$XDG_CONFIG_HOME`.
- Cache deserialization errors are now ignored. Previously, when the `dg` contents of the cache were in an outdated format, `dg` could crash. Now it will just rebuild the cache.
- The [Components ETL Pipeline Tutorial](https://docs.dagster.io/guides/labs/components/components-etl-pipeline-tutorial) now supports users of both `pip` and `uv`.
- The `dg` CLI will now emit a warning if you are using "active" mode for your project python environment, there is a virtual environment at `<project_root>/.venv`, and the activated venv is not `<project_root>/.venv`
- A new `dg` setting `cli.suppress_warnings` is available. This takes a list of warning types to suppress.
- Added a warning message to inform users they need to install their project package when skipping automatic environment setup.
- Changed configuration of project Python environments. The `tool.dg.project.python_environment` previously accepted a string, `"active"` or `"persistent_uv"`. Now it accepts a table with one of two keys:
  - `{active = true}`: equivalent of previous `"active"`
  - `{uv_managed = true}`: equivalent of previous `"persistent_uv"`
- Changed the default python environment for newly scaffolded projects to `tool.dg.project.python_environment` to `{active = true}`. This means by default, no virtual environment or `uv.lock` will be created when scaffolding a new project (via `dg init` or `dg scaffold project`). You can pass `--python-environment uv_managed` for the old behavior.
- Removed the `--skip-venv` flag on `dg scaffold project` and `dg init`.
- The `dagster_components` package has been merged into `dagster` and use of the `dagster-components` package has been deprecated. `dagster-components` will remain as a stub package for the next few weeks, but code should be updated to import from `dagster.components` instead of `dagster_components`.
- [dagster-dbt] the `dagster-dbt project prepare-and-package` cli now supports `--components` for handling `DbtProjectComponent`
- [dagster-dbt] `DbtProjectComponent` has been reworked, changing both the python api and the yaml schema. `dbt` has been replaced with `project` with a slightly different schema, and `asset_attributes` with `translation` .

## 1.10.11 (core) / 0.26.11 (libraries)

### New

- [ui] Runs launched from the Dagster UI get a `dagster/from_ui = true` tag, making it easy to filter for them.
- [ui] The run page now shows the number of log levels selected as well as the number of log levels available.
- Added `AirflowFilter` API for use with `dagster-airlift`, allows you to filter down the set of dags retrieved up front for perf improvements.

### Bugfixes

- [ui] Fixed a bug that prevented filtering asset events by type.
- Fixed a bug that would cause multi-assets defined with `can_subset=True` to error when using `dagster-pipes` if not all outputs were emitted.
- [dagster-dbt] the `state_path` argument to `DbtCliResource` now resolves relative to the project directory as documented.
- [dagster-k8s] Made reliability improvements to PipesK8sClient log streaming when transient networking errors occur. The default behavior of the PipesK8sClient is now to reconnect to the stream of logs every hour (this value can be overridden by setting the `DAGSTER_PIPES_K8S_CONSUME_POD_LOGS_REQUEST_TIMEOUT` environment variable) and to retry up to 5 times if an error occurs while streaming logs from the launched Kubernetes pod (this value can be overridden by setting the `DAGSTER_PIPES_K8S_CONSUME_POD_LOGS_RETRIES` environment variable.)
- [dagster-dbt] Fixed a bug where dbt jobs would fail due to unparseable logs causing errors in `DbtCliInvocation.stream_raw_events`. (Thanks [@ross-whatnot](https://github.com/ross-whatnot)!)

### Dagster Plus

- [ui] It is now possible to roll back a code location to a version that had previously been in an errored state.

### dg & Components (Preview)

- The `dg` CLI will now emit a warning if you are using "active" mode for your project python environment, there is a virtual environment at `<project_root>/.venv`, and the activated venv is not `<project_root>/.venv`
- A new `dg` setting `cli.suppress_warnings` is now available. This takes a list of warning types to suppress.
- Changed configuration of project Python environments. The `tool.dg.project.python_environment` previously accepted a string, `"active"` or `"persistent_uv"`. Now it accepts a table with one of three keys: - `{active = true}`: equivalent of previous `"active"` - `{uv_managed = true}`: equivalent of previous `"persistent_uv"`
- Changed the default python environment for newly scaffolded projects to `tool.dg.project.python_environment` to `{active = true}`. This means by default, no virtual environment or `uv.lock` will be created when scaffolding a new project (via `dg init` or `dg scaffold project`). You can pass `--python-environment uv_managed` for the old behavior.
- Removed the `--skip-venv` flag on `dg scaffold project` and `dg init`.
- Fixed a bug where new projects scaffolded with `dg scaffold project` were lacking `dagster` as a dependency.
- The "Creating a library of components" guide has been replaced by a new and more general "Creating a `dg` plugin" guide.
- The arguments/options of the `dg init` command have changed. You may pass `.` as an argument to initialize a project/workspace in the CWD. See `dg init --help` for more details.
- The `dagster-components` package (which was converted to a stub package in the last release) is no longer being published. All `dagster-components` functionality is now part of `dagster`.
- Projects should now expose custom component types under the `dagster_dg.plugin` entry point group instead of `dagster_dg.library`. `dagster_dg.library` support is being kept for now for backcompatibility, but will be dropped in a few weeks.
- Fixed formatting of line added to `project/lib/__init__.py` when scaffolding a component type.
- The `dg env list` command is now `dg list env`
- The `dg plus env pull` command is now `dg plus pull env`.
- The `dg list component-type` command has been removed. There is a new `dg list plugins` with output that is a superset of `dg list component-type`.
- The `dg` user config file on Unix is now looked for at `~/.dg.toml` instead of `~/dg.toml`.
- [dagster-dbt] `DbtProjectComponent` has been reworked, changing both the python api and the yaml schema. `dbt` has been replaced with `project` with a slightly different schema, and `asset_attributes` with `translation`.

## 1.10.10 (core) / 0.26.10 (libraries)

### New

- A new `blocking` parameter has been added to `build_last_update_freshness_checks` and `build_time_partition_freshness_checks`.
- The default byte size limit for gRPC requests and responses is now 100MB instead of 50MB. This value can be adjusted by setting the `DAGSTER_GRPC_MAX_RX_BYTES` and `DAGSTER_GRPC_MAX_SEND_BYTES` environment variables on the gRPC client and server processes.
- Added a new `Definitions.map_asset_specs` method, which allows for the transformation of properties on any AssetSpec or AssetsDefinition objects in the `Definitions` object which match a given asset selection.
- `Definitions.validate_loadable` and `dagster definitions validate` will now raise an error on assets with invalid partition mappings, like a `TimeWindowPartitionMapping` between two time-based partitions definitions with different timezones. Previously, these invalid partition mappings would not raise an error until they were used to launch a run.
- [dagster-k8s] Reliability improvements to `PipesK8sClient` log streaming when transient networking errors occur. The default behavior of the `PipesK8sClient` is now to reconnect to the stream of logs every 3600 seconds (this value can be overridden by setting the `DAGSTER_PIPES_K8S_CONSUME_POD_LOGS_REQUEST_TIMEOUT` environment variable) and to retry up to 5 times if an error occurs while streaming logs from the launched Kubernetes pod (this value can be overridden by setting the `DAGSTER_PIPES_K8S_CONSUME_POD_LOGS_RETRIES` environment variable.)

### Bugfixes

- Fixed an issue where run monitoring sometimes didn't fail runs that were stuck in a `NOT_STARTED` status instead of a `STARTING` status.
- Fixed an issue where Dagster run metrics produced large amounts of error lines when running in containers without a CPU limit set on the container.
- Fixed an issue where using partial resources in Pydantic >= 2.5.0 could result in an unexpected keyword argument TypeError. (Thanks [@HynekBlaha](https://github.com/HynekBlaha)!)
- Fixed an issue with new `AutomationCondition.executed_with_tags()` that would cause the `tag_keys` argument to not be respected. Updated the display name of `AutomationCondition.executed_with_tags()` to contain the relevant tag_keys and tag_values.
- [ui] Fixed a bug preventing filtering on the asset events page.
- [ui] Fix custom time datepicker filter selection for users with custom Dagster timezone settings.
- [dagster-fivetran] Fixed a bug causing the Fivetran integration to fetch only 100 connectors per destination.
- [dagster-fivetran] Paused connectors no longer raise an exception in `FivetranWorkspace.sync_and_poll(...)`. Instead, they skip and a warning message is logged.
- [dagster-fivetran] Fixed an issue where new runs of code locations using Fivetran assets would sometimes raise a "Failure condition: No metadata found for CacheableAssetsDefinition" error if the run was started immediately after a new version of the code location was deployed.
- [dagster-cloud] Reliability improvements to the `dagster-cloud job launch` command when launching runs targeting large numbers of assets or asset checks.

### Dagster Plus

Fixed an issue with the identification of the base repository URL the `DAGSTER_CLOUD_GIT_URL`. The raw URL is now exposed as `DAGSTER_CLOUD_RAW_GIT_URL`.

### dg & Components (Preview)

- The `dagster_components` package has been merged into `dagster`. All symbols exported from `dagster_components` are now exported by `dagster`.
- Projects should now expose custom component types under the `dagster_dg.plugin` entry point group instead of `dagster_dg.library`. `dagster_dg.library` support is being kept for now for backcompatibility, but will be dropped in a few weeks.
- `Component.get_schema` has been renamed to `Component.get_model_cls`. Override that instead to customize the frontend of your component. `Component.get_schema` will continue to work for the time being but will be removed at some point in the future.
- Add support for `dg.toml` files. `dg` settings in `pyproject.toml` are set under `tool.dg`, but in `dg.toml` they are set at the top level. A `dg.toml` may be used in place of `pyproject.toml` at either the project or workspace level.
- `dg`-scaffolded workspaces now include a `dg.toml` instead of `pyproject.toml` file.
- Projects scaffolded using `dg init` or `dg scaffold project` now follow modern Python packaging conventions, placing the root module in a top-level `src` directory and use `hatchling` as build backend rather than `setuptools`.
- Scaffolding a component type defaults to inheriting from `dagster.components.Model` instead of getting decorated with `@dataclasses.dataclass`.
- Assets scaffolded using `dg scaffold dagster.asset` will no longer be commented out.
- The `dg list component-type` command has been removed. There is a new `dg list plugins` with output that is a superset of `dg list component-type`.
- `dg list defs` now includes infomation about asset checks.
- Fix formatting of line added to `project/lib/__init__.py` when scaffolding a component type.
- Fixed bug where schedules were displayed in the sensors section of `dg list defs`.
- Fixed a bug where `dg` would crash when working with Python packages with an src-based layout.

## 1.10.9 (core) / 0.26.9 (libraries)

### Bugfixes

- [ui] Fix custom time datepicker filter selection for users with custom Dagster timezone settings.

### dg & Components (Preview)

- Add support for `dg.toml` files. `dg` settings in `pyproject.toml` are set under `tool.dg`, but in `dg.toml` they are set at the top level. A `dg.toml` may be used in place of `pyproject.toml` at either the project or workspace level.
- `dg`-scaffolded workspaces now include a `dg.toml` instead of `pyproject.toml` file.
- `dg`-scaffolded projects now place the root package in an `src/` directory and use `hatchling` as the build backend rather than `setuptools`.
- Fixed a bug where `dg` would crash when working with Python packages with an src-based layout.
- `dg check yaml` now properly validates component files in nested subdirectories of the `defs/` folder.

## 1.10.8 (core) / 0.26.8 (libraries)

### New

- [ui] The Dagster UI now allows you to specify extra tags when re-executing runs from failure from the runs feed re-execute dialog, or by holding shift when clicking Re-execute menu items throughout the app.
- [ui] Performance improvements for loading the partitions page for multi-partitioned assets.
- [ui] Fix link in toast messages that appear when launching backfills.
- [ui] Dagster's UI now allows you to copy run tags as a YAML block from the Tags and Configuration modals.
- [ui] The Dagster Run UI now allows you to view the execution plan of a queued run.

### Bugfixes

- The `AutomationCondition.initial_evaluation` condition has been updated to become true for all partitions of an asset whenever the PartitionsDefinition of that asset changes, rather than whenever the structure of the condition changes.
- [dagster-fivetran] Fixed an issue where new runs of code locations using fivetran assets would sometimes raise a "Failure condition: No metadata found for CacheableAssetsDefinition" error if the run was started immediately after a new version of the code location was deployed.
- [dagster-fivetran] Fixed an issue where including multiple sets of assets from `build_fivetran_assets_definitions` in a single `Definitions` object would result in "duplicate node" errors when launching a run.
- [ui] Fixed line charts for colorblind themes.
- [ui] Fixed an issue with querystring parsing that can arise when selecting a large number of items in the selection syntax input.
- [ui] Fixed tag filtering on automations list.
- [ui] Fixed hover state on focused inputs.
- [ui] Fixed an issue with the Run step selection input autocomplete where it would suggest `key:"*substring*"` instead of `name:"*substring*"`.
- [ui] Fixed the "View run" link shown when launching runs

### Documentation

- Fix a bug in example code for pyspark.

### dg & Components (Preview)

- Added the ability to scaffold Python components.
- The `DefsModuleComponent` has been renamed to `DefsFolderComponent`.
- When scaffolding a component, the command is now `dg scaffold my_project.ComponentType` instead of `dg scaffold component my_project.ComponentType`.
- [dagster-dg] `dagster list defs` will now read environment variables from a local .env file if present when constructing the definitions.
- `dagster-components` has been merged into `dagster` and use of the `dagster-components` package has been deprecated.
  `dagster-components` will remain as a stub package for the next few weeks, but code should be updated to import from `dagster.components` instead of `dagster_components`.
- The `DbtProjectComponent` has been relocated to the `dagster-dbt` package,
  importable as `dagster_dbt.DbtProjectComponent`.
- The `SlingReplicationCollectionComponent` has been relocated to the `dagster-sling` package,
  importable as `dagster_sling.SlingReplicationCollectionComponent`.

## 1.10.7 (core) / 0.26.7 (libraries)

### New

- Applying changes from sensor test results now also applies changes from dynamic partition requests.
- When merging assets from multiple code locations, autogenerated specs are now prioritized lower than customized external asset specs.
- [ui] Allowed using command-click to view a run from the toast message that appears when starting a materialization of an asset.
- [ui] Asset graph can now zoom out a lot more.
- [ui] Added a kind tag for dbt Cloud.
- [dagster-dlt] Added backfill policy to dlt_assets, defaulting to single-run. (Thanks [@neuromantik33](https://github.com/neuromantik33)!)

### Bugfixes

- Updated `AutomationCondition.initial_evaluation` condition to become true for all partitions of an asset whenever the PartitionsDefinition of that asset changes, rather than whenever the structure of the condition changes.
- Fixed a bug with several integrations that caused data fetched from external APIs not to be properly cached during code server initialization, leading to unnecessary API calls in run and step worker processes. This affected `dagster-airbyte`, `dagster-dlift`, `dagster-dbt`, `dagster-fivetran`, `dagster-looker`, `dagster-powerbi`, `dagster-sigma`, and `dagster-tableau`.
- [ui] Fixed an issue with the Run step selection input autocomplete where it would suggest `key:"*substring*"` instead of `name:"*substring*"`.
- [ui] Fixed the "View run" link shown when launching runs.
- [ui] Fixed an issue where updating a catalog view caused an infinite loading state.
- Fixed an issue which could cause asset check evaluations emitted from the body of the op to not impact the check status of an asset in the UI.
- Fixed an issue that could cause an asset backfill created by re-executing another backfill from the point of failure to error on the first tick in rare cases.
- Fixed an issue that could cause automation condition evaluations to fail to render in the UI in rare cases.
- [ui] Fixed a regression in the "Cancel Backfill" option for job backfills that have finished queuing runs.
- [ui] Fixed overflow of long runs feed table on backfill page.
- [dagster-dbt] Replaced `@validator` with `@field_validator` in dagster_dbt/core/resource.py to prevent Pydantic deprecation warnings. (Thanks [@tintamarre](https://github.com/tintamarre)!)

### Documentation

- Updated the "Asset versioning and caching" guide to reflect the current Dagster UI and "Unsynced" labels.
- Removed a few repeated lines in documentation on customizing automation conditions. (Thanks [@zero-stroke](https://github.com/zero-stroke)!)
- Fixed example in TableRecord documentation to use the new input format.

### Configuration

- [dagster-gcp] Updated Dataproc configuration to the latest version. If necessary, consider pinning your `dagster-gcp` version while you migrate config. Please see the full list of changed fields: https://gist.github.com/deepyaman/b4d562e04fe571e40037a344b7a9937d
- [dagster-aws][dagster-spark] Updated Spark configuration to the latest version (3.5.5). If necessary, consider pinning your `dagster-aws` and/or `dagster-spark` version while you migrate config. Please see the full list of changed fields: https://gist.github.com/deepyaman/f358f5a70fea28d5f164aca8da3dee04

### Dagster Plus

- [ui] Fixed filtering for multiple tags on list view pages, including Automations.
- [ui] Fixed an issue where the urls generated by catalog filtering would remove all filters if loaded directly.
- [ui] Added a warning on the sign-in page indicating that the sign-in and signup flows will be changing soon.
- [ui] Require confirmation when rolling back a code location to a previous version.

### dg & Components (Preview)

- Virtual environment detection settings for projects have changed. Previously, the global settings `use_dg_managed_environment` and `require_local_venv` controlled the environment used when launching project subprocesses. This is now configured at the project level. The `tool.dg.project.python_environment` setting takes a value of either `persistent_uv` or `active`. `persistent_uv` will be used by default in new scaffolded projects and uses a uv-managed `.venv` in the project root. `active` is the default if no `tool.dg.project.python_environment` is set, and just uses the active python environment and opts out of `dg` management of the environment.
- A new base class, `Resolvable`, has been added. This can be used to simplify the process of defining a yaml schema for your components. Instead of manually defining a manual `ResolvedFrom[...]` and `ResolvableModel`, the framework will automatically derive the model schema for you based off of the annotations of your class.
- Python files with Pythonic Components (i.e. defined with `@component`) can now contain relative imports.
- The `dg init` command now accepts optional `--workspace-name` and `--project-name` options to allow scaffolding an initial workspace and project via CLI options instead of prompts.
- Added a new `dagster_components.dagster.DefsFolderComponent` that can be used at any level of your `defs/` folder to apply asset attributes to the definitions at or below that level. This was previously named `dagster_components.dagster.DefsModuleComponent`.

## 1.10.6 (core) / 0.26.6 (libraries)

### New

- Added a new `AutomationCondition.executed_with_tags()` condition that makes it possible to filter for updates from runs with particular tags.
- `AssetCheckEvaluation` can now be yielded from Dagster ops to log an evaluation of an asset check outside of an asset context.
- Added the `kinds` argument to `dagster.AssetOut`, allowing kinds to be specified in `@multi_asset`.
- [dagster-dbt] `AssetCheckEvaluations` are now yielded from `ops` leveraging `DbtCliResource.cli(...)` when asset checks are included in the dbt asset lineage.
- [dagster-sling] The `SlingResource.replicate()` method now takes an option `stream` parameter, which allows events to be streamed as the command executes, instead of waiting until it completes (thanks, @natpatchara-w!).
- [dagster-graphql] The `DagsterGraphQLClient` now supports an `auth` keyword argument, which is passed to the underlying `RequestsHTTPTransport` constructor.
- [ui] The asset selection syntax input now allows slashes "/" in the freeform search.
- [ui] The backfill pages now show summary information on all tabs for easier backfill monitoring.

### Bugfixes

- Fixed issue with `AutomationCondition.newly_requested()` which could cause it to fail when nested within `AutomationCondition.any_deps_match()` or `AutomationCondition.all_deps_match()`.
- Fixed a bug with `AutomationCondition.replace()` that would cause it to not effect `AutomationCondition.since()` conditions.
- Fixed a bug with several integrations that caused data fetched from external APIs not to be properly cached during code server initialization, leading to unnecessary API calls in run and step worker processes. This affected: `dagster-airbyte`, `dagster-dlift`, `dagster-dbt`, `dagster-fivetran`, `dagster-looker`, `dagster-powerbi`, `dagster-sigma`, and `dagster-tableau`.
- Fixed a bug that could cause invalid circular dependency errors when using asset checks with additional dependencies.
- [dagster-fivetran] Loading assets for a Fivetran workspace containing incomplete and broken connectors now no longer raises an exception.
- [ui] Fixed the colorblind (no red/green) theme behavior when in dark mode.
- [ui] The Asset > Partitions page no longer displays an error in some cases when creating dynamic partitions.
- [ui] The Launch and Report Events buttons no longer error if you click it immediately after creating a new dynamic partition.

### dg & Components (Preview)

- `__pycache__` files are no longer included in the output of `dg list component`. (Thanks [@stevenayers](https://github.com/stevenayers)!)
- When resolving the `deps` of an `AssetSpec` from yaml, multi-part asset keys are now correctly parsed. (Thanks [@stevenayers](https://github.com/stevenayers)!)
- The entrypoint group for dg projects has been renamed from `dagster.components` to `dagster_dg.library`.
- `dg check yaml` is now run by default before `dg dev` and `dg check defs`.

## 1.10.5 (core) / 0.26.5 (libraries)

### New

- `async def yield_for_execution` is now supported on `ConfigurableResource`. An `event_loop` argument has been added to context builders to support direct execution.
- `dagster dev` deduplicates stacktraces when code locations fail to load, and will by default truncate them to highlight only user code frames.
- Improved error message experience for resources expecting an env var which was not provided.
- [ui] An updated asset selection syntax is now available in the asset graph, insights, and alerts. The new syntax allows combining logical operators, lineage operators, and attribute filters.
- [dagster-polars] The minimal compatible `deltalake` version has been bumped to `0.25.0`; the `PolarsDeltaIOManager` is now using the `rust` engine for writing DeltaLake tables by default.

### Bugfixes

- Fixed a bug with AutomationCondition.replace() that would cause it to not effect `AutomationCondition.since()` conditions.
- Fixed a bug that could cause invalid circular dependency errors when using asset checks with additional dependencies.
- Fixed an issue in Dagster OSS where failed runs of multiple partitions didn't update those partitions as failed in the Dagster UI or trigger failure automation conditions.
- Fixed an issue where `dagster dev` would fail to load code that took more than 45 seconds to import unless the `--use-legacy-code-server-behavior` flag was used.
- [dagster-airbyte] Fixed an issue that caused the group name of assets created using `build_airbyte_assets_definitions` function to error when attempting to modify the default group name.
- [dagster-fivetran] Fixed an issue that caused the group name of assets created using `build_fivetran_assets_definitions` function to error when attempting to modify the default group name.

## 1.10.4 (core) / 0.26.4 (libraries)

### New

- [ui] The asset overview tab for a partitioned asset now shows metadata and schema of the most recent materialization, not today's partition.
- [ui] In run logs, asset materialization and observation events now show the output partition as well as the asset key.
- [ui] The backfills view has moved to Runs > Backfills and is no longer available on the Overview tab.
- [ui] Pool event information from a run now links to the pool configuration page.
- Added support for passing `tags` to the created `RunRequest` when using `build_sensor_for_freshness_checks()`.
- [dagster-gcp] The `PickledObjectGCSIOManager` now replaces the underlying blob when the same asset is materialized multiple times, instead of deleting and then re-uploading the blob.
- [docs] Added docs covering run-scoped op concurrency.
- [dagster-fivetran] Fivetran connectors fetched in Dagster can now be filtered and selected using the ConnectorSelectorFn.

### Bugfixes

- Fixed a bug where if a run was deleted while the re-execution system was determining whether the run should be retried an error was raised. Now, if a run is deleted while the re-execution system is determining whether the run should be retried, the run will not be retried.
- [ui] Fixed an issue where assets with automation conditions wouldn't show the jobs/sensors/schedules targeting them.
- [ui] Steps properly transition to failed in the Run gantt chart when resource initialization fails.

## 1.10.3 (core) / 0.26.3 (libraries)

### New

- Added links from pool info in run event logs to the respective pool configuration pages.
- Added queued run information on the pool info page, even if the pool granularity is set to `run`.
- [ui] Added information about asset partitions that fail to materialize due to run cancellations to the asset partition detail page.
- [ui] Added two new themes for users with reduced sensitivity to red and green light.
- [ui] Added Not Diamond icon for asset `kinds` tag. (Thanks [@dragos-pop](https://github.com/dragos-pop)!)
- [ui] Added Weaviate icon for asset `kinds` tag. (Thanks [@jjyeo](https://github.com/jjyeo)!)
- [ui] Made Alerts page visible to users with Viewer roles.
- [dagster-postgres] Removed the cap on `PostgresEventLogStorage` `QueuePool` by setting [`max_overflow`](https://docs.sqlalchemy.org/en/20/core/engines.html#sqlalchemy.create_engine.params.max_overflow) to `-1`. (Thanks [@axelwas](https://github.com/axelwas)!)

### Bugfixes

- Fixed a bug where a sensor emitting multiple `RunRequests` with the same run key within a single tick would cause two runs with the same key to be executed. Now, only the first run will be executed. (Thanks [@Gw1p](https://github.com/Gw1p)!)
- Fixed a bug where run step selections were not affecting which pools limit a given run.
- Fixed an issue where seeding the random number generator during code import or when initializing a resource could cause every step to write to the same stdout or stderr key.
- [ui] Fixed an issue where certain jobs weren't showing the assets they targeted.
- Asset backfills will now move into a `CANCELED` state instead of a `FAILURE` state when not every requested partition has been marked as materialized or failed by the backfill.
- [dagster-dbt] Fixed a bug breaking `packaged_project_dir` since supporting `profiles_dir` in `DbtProject`.
- Fixed an issue with `DbIOManagers` being unable to process subclasses of handled types.
- [ui] Preserved asset selection filters when navigating folders in the asset catalog.
- [ui] Corrected PostgreSQL SVG icon for asset `kinds` tag. (Thanks [@dragos-pop](https://github.com/dragos-pop)!)
- [ui] Fixed an issue that caused Markdown with code blocks in languages not supported for syntax highlighting to crash the page.
- Fixed an issue where asset backfills included failed partitions in the in-progress list in logging output.

### Documentation

- Fixed broken image links in quickstart examples. (Thanks [@stevenayers](https://github.com/stevenayers)!)
- [dagster-dbt] Made several fixes to the "Using dbt with Dagster" page. (Thanks [@jjyeo](https://github.com/jjyeo)!)
- Fixed broken link in defining-assets.md. (Thanks [@Exlll](https://github.com/Exlll)!)
- Fixed link in CONTRIBUTING.md leading to a 404. (Thanks [@Exlll](https://github.com/Exlll)!)
- Fixed typo in managing-code-locations-with-definitions.md. (Thanks [@kgeis](https://github.com/kgeis)!)
- Fixed typo in asset-versioning-and-caching.md. (Thanks [@petrusek](https://github.com/petrusek)!)

### Dagster Plus

- [ui] Enabled setting long-running job alerts in minutes instead of hours.
- [dagster-insights] Fix links to branch deployments in the deployment list UI.
- [dagster-insights] Adjusted the way batching runs from the `create_snowflake_insights_asset_and_schedule` sensor using the `schedule_batch_size_hrs` parameter works to yield a single partition range run instead of individual runs per partition.

## 1.10.2 (core) / 0.26.2 (libraries)

### New

- Turned on run-blocking for concurrency keys / pools by default. For op granularity, runs are dequeued if there exists at least one op that can execute once the run has started. For run granularity, runs are dequeued if all pools have available slots.
- Performance improvements for backfills of large partition sets.
- The prefix of temporary directories created when running a temporary Dagster instance (as with `dagster dev`) has been changed from `tmp` to `.tmp_dagster_home_`. (Thanks [@chazmo03](https://github.com/chazmo03)!)
- Added sanitation checks on valid pool names.
- [dagster-aws] Added sample Terraform modules for Dagster deployment on AWS ECS.
- [dagster-dbt] Added pool support for dbt integrations.
- [dagster-dlt] Added pool support for dlt integrations.
- [dagster-sling] Added pool support for sling integrations.
- [dagster-aws] Added AWS RDSResource. (Thanks [@shimon-cherrypick](https://github.com/shimon-cherrypick)!)
- [dagster-mysql] Added MySQLResource. (Thanks [@shimon-cherrypick](https://github.com/shimon-cherrypick)!)
- [dagster-azure] Added Azure Blob Storage Resource. (Thanks [@shimon-cherrypick](https://github.com/shimon-cherrypick)!)
- [ui] Expanding/collapsing groups in the Asset Graph will no longer reset your zoom.
- [ui] Changed the queue criteria dialog to reference pools instead of concurrency keys.
- [ui] The Instance Backfills page is being removed in the upcoming March 6 release in favor of the new Runs > Backfills view.
- [ui] When re-executing a run that is part of a backfill that has completed, Dagster UI notifies you that the re-execution will not update the backfill stats.
- [ui] The backfill actions menu now includes "Re-execute" and "Re-execute from failure", which create new backfills targeting the same partitions, and the partitions which failed to materialize, respectively.
- [ui] The latest asset check evaluation is shown in the Evaluation History tab, and `AssetCheckResult` descriptions are rendered in the table making it easier to publish a summary of check evaluation.
- [ui] The Materialize button appears more quickly on asset pages in the Dagster UI.
- [ui] The queue details modal for a run no longer closes as new runs arrive and links to the correct concurrency page.

### Bugfixes

- Fixed an issue where if two separate code locations defined the same asset key with an automation condition, duplicate runs could be created by Declarative Automation.
- Fixed the `psycopg2.errors.UndefinedColumn` database error when trying to set a concurrency key without first having run `dagster instance migrate`.
- Fixed an issue where Declarative Automation sensors in code locations that included source assets referencing assets with automation conditions in other code locations would sometimes cause duplicate runs to be created.
- Fixed a bug in the enforcement of global op concurrency limits.
- Fixed an issue where when using `dagster dev`, some changes were not reflected in the UI after pressing the "Reload Definitions" button.
- Fixed the issue where a resource initialization error within a sensor definition test incorrectly recommended using `build_schedule_context` instead of `build_sensor_context`.
- Fixed migration issue where `dagster instance migrate` was failing for instances with non-empty concurrency limits tables.
- [ui] Fixed an issue where a "Message: Cannot return null for non-nullable field PartitionKeys.partitionKeys." error was raised in the launchpad for jobs with unpartitioned assets.
- [ui] Fixed concurrency link escaping in the `View queue criteria` dialog.
- [ui] Fixed an issue where the deployment switcher can become permanently "unset" when navigating from Org Settings back to a deployment.
- [ui] Fixed an issue with the traversal operators on the asset graph (`asset++`) not including assets connected to the target asset by paths of varying distance.

### Dagster Plus

- A setting is available in agent configuration `direct_snapshot_uploads` (`directSnapshotUploads` in helm) which opts in to a new more efficient scheme for how definitions are handled during code location updates.
- Introduced new test utilities `event_log` and `dagster_event` in `dagster-cloud-test-infra` to facilitate the creation of test data with sensible defaults for EventLogEntry and DagsterEvent objects.
- [bigquery-insights][bugfix] Support querying for insights from the configured `execution_project` if defined.
- [bigquery-insights][bugfix] When `execution_project` is defined in the dbt profile, fall back to fetching the dataset from the dbt profile's `project` if the dataset cannot be found in the `execution_project`.

## 1.10.1 (core) / 0.26.1 (libraries)

### Bugfixes

- Fixed an issue where runs containing pool-assigned ops without limits set got stuck in the run queue.
- Fixed an issue where a "Message: Cannot return null for non-nullable field PartitionKeys.partitionKeys." error was raised in the launchpad for jobs with unpartitioned assets.
- [ui] Updated "Queue criteria" modal to reference and link to pool concurrency settings pages.
- [ui] The "Queue criteria" modal for a run no longer closes as new runs arrive.

## 1.10.0 (core) / 0.26.0 (libraries)

### New

- Added a new `AutomationCondition.data_version_changed()` condition.
- [dagster-msteams] Added support for sending messages to PowerAutomate flows using AdaptiveCard formatting.
- `dagster definitions validate` is now less verbose, primarily highlighting load errors.
- [ui] Made defunct code locations removable when editing environment variables.
- [ui] Added a warning icon to the Agents item in Deployment settings, indicating when there are no active agents.
- [dagster-tableau] Changed logic to show embedded data sources in case published data sources are not present. Also, pulled more metadata from Tableau. (Thanks [@VenkyRules](https://github.com/VenkyRules)!)
- Added new decorators to reflect our [new API lifecycle](https://docs.dagster.io/api/api-lifecycle): `@preview`, `@beta` and `@superseded`. Also added new annotations and warnings to match these new decorators.

### Bugfixes

- [ui] Fixed persistence of the group-by setting in the run timeline view.
- [ui] Fixed timestamped links to asset pages from asset check evaluations in run logs.
- [ui] Fixed excessive rendering and querying on the Concurrency configuration page.
- Fixed the step stats calculations for steps that fail and request a retry before the step starts. This happened if a failure occurred in the step worker before the compute function began execution. This should help with sporadic hanging of step retries.
- Fixed an issue where the Concurrency UI was broken for keys with slashes.
- Fixed an issue with emitting `AssetResult` with ops or multi-assets that are triggered multiple times in the same run.
- [dagster-dbt] Fixed a bug introduced in dagster-dbt 0.25.7 that would cause execution to fail when using the `@dbt_assets` decorator with an `io_manager_key` specified.
- [dagster-dbt] Refactored `UnitTestDefinition` instantiation to address failure to initialize dbt models with unit tests. (Thanks [@kang8](https://github.com/kang8)!)
- Fixed issue where `dagster instance migrate` was failing for instances with tables having non-empty concurrency limits.
- Fixed an issue where Declarative Automation sensors in code locations that included source assets referencing assets with automation conditions in other code locations would sometimes cause duplicate runs to be created.
- Turned on run blocking for concurrency keys/pools by default. For op granularity, runs are dequeued if there exists at least one op that can execute once the run has started. For run granularity, runs are dequeued if all pools have available slots.
- [dagster-dbt] Added pool support.
- [dagster-dlt] Added pool support.
- [dagster-sling] Added pool support.

### Documentation

- Corrected docs on managing concurrency.
- Fixed a Markdown link to "assets metadata." (Thanks [@rchrand](https://github.com/rchrand)!)
- Fixed a `pip install` command for Zsh. (Thanks [@aimeecodes](https://github.com/aimeecodes)!)

### Breaking Changes

- The `include_sources` param on all `AssetSelection` APIs has been renamed to `include_external_assets`.
- Disallowed invalid characters (i.e. anything other than letters, numbers, dashes, and underscores) in pool names.
- Changed the default run coordinator to be the queued run coordinator. This requires the Dagster daemon to be running for runs to be launched. To restore the previous behavior, you can add the following configuration block to your `dagster.yaml`:

  ```
  run_coordinator:
    module: dagster.core.run_coordinator.sync_in_memory_run_coordinator
    class: SyncInMemoryRunCoordinator
  ```

### Deprecations

- [dagster-sdf] Moved the `dagster-sdf` library to the community-supported repo.
- [dagster-blueprints] Removed the `dagster-blueprints` package. We are actively developing a project, currently named Components, that has similar goals to Blueprints of increasing the accessibility of Dagster.
- Removed the `@experimental` decorator in favor of the `@preview` and `@beta` decorators. Also removed annotations and warnings related to the `@experimental` decorator.

### Dagster Plus

- Shipped a range of improvements to alerts in Dagster+, including more granular targeting, streamlined UIs, and more helpful content. Stay tuned for some final changes and a full announcement in the coming weeks!

## 1.9.13 (core) / 0.25.13 (libraries)

### Dagster Plus

- Fixed a bug where runs using global op concurrency would raise an exception when claiming a concurrency slot.

## 1.9.12 (core) / 0.25.12 (libraries)

### New

- Adds a top-level argument `pool` to asset/op definitions to replace the use of op tags to specify concurrency conditions.
- The `dagster definitions validate` command now loads locations in-process by default, which speeds up runtime.
- All published dagster libraries now include a `py.typed` file, which means their type annotations will be used by static analyzers. Previously a few libraries were missing this file.
- Adds concurrency pool information in the UI for asset / op definitions that use concurrency pools.
- Optional data migration to improve performance of the Runs page. Run `dagster instance migrate` to run the data migration. The migration will update serialized backfill objects in the database with an end timestamp attribute computed by querying the runs launched by that backfill to determine when the last run completed.
- Added the ability to distinguish between explicitly set concurrency pool limits and default-set pool limits. Requires a schema migration using `dagster instance migrate`.
- Moves run queue configuration from its standalone deployment setting into the `concurrency` deployment setting, along with new settings for concurrency pools.
- Enabled run granularity concurrency enforcement of concurrency pool limits.
- [dagster-dbt] Specifying a dbt profiles directory and profile is now supported in `DbtProject`.
- [dagster-dlt] `DagsterDltTranslator.get_*` methods have been superseded in favor of `DagsterDltTranslator.get_asset_spec`.
- [dagster-gcp] Added `PipesDataprocJobClient`, a Pipes client for running workloads on GCP Dataproc in Job mode.
- [dagster-looker] `DagsterLookerLkmlTranslator.get_*` methods have been superseded in favor of `DagsterLookerLkmlTranslator.get_asset_spec`.
- [dagster-pipes] Dagster Pipes now support passing messages and Dagster context via Google Cloud Storage.
- [ui] Created a standalone view for concurrency pools under the Deployment tab.
- [ui] When launching partitioned assets in the launchpad from the global graph, Dagster will now warn you if you have not made a partition selection.
- [ui] When viewing Runs, allow freeform search for filtering to view runs launched by schedules and sensors.
- [ui] Remove misleading run status dot from the asset events list.
- [ui] Introduce a stepped workflow for creating new Alerts.

### Bugfixes

- Fixed an issue where querying for Asset Materialization events from multi-partition runs would assign incorrect partition keys to the events.
- Fixed an issue where partition keys could be dropped when converting a list of partition keys for a `MultiPartitionsDefinition` to a `PartitionSubset`.
- Fixed an issue where the "Reload definitions" button didn't work when using `dagster dev` on Windows, starting in the 1.9.10 release.
- Fixed an issue where dagster could not be imported alongside some other libraries using gRPC with an 'api.proto' file.
- [ui] Fixed an issue where non-`None` default config fields weren't being displayed in the Launchpad view.
- [ui] Fixed an issue with the search bar on the Asset partitions page incorrectly filtering partitions when combined with a status filter.
- [ui] Fixed Asset page header display of long key values.
- [ui] Fixed Slack tag in alert creation review step for orgs that have Slack workspaces connected.
- [dagster-dbt] Fixed a bug introduced in `dagster-dbt` 0.25.7 which would cause execution to fail when using the `@dbt_assets` decorator with an `io_manager_key` specified.
- [dagster-databricks] Fixed an issue with Dagster Pipes log capturing when running on Databricks.

### Documentation

- Fixed a mistake in the docs concerning configuring asset concurrency tags in Dagster+.
- Added a tutorial for using GCP Dataproc with Dagster Pipes.

### Dagster Plus

- Relaxed pins on the 'opentelemetry-api' dependency in the 'dagster-cloud' package to `>=1.27.0` to allow using `dagster-cloud` with `protobuf` versions 3 and 4.

## 1.9.11 (core) / 0.25.11 (libraries)

### Bugfixes

- Fixed an issue where running `dagster dev` would fail on Windows machines.
- Fixed an issue where partially resolved config with default values were not able to be overridden at runtime.
- Fixed an issue where default config values at the top level were not propagated to nested config values.

## 1.9.10 (core) / 0.25.10 (libraries)

### New

- Added a new `.replace()` method to `AutomationCondition`, which allows sub-conditions to be modified in-place.
- Added new `.allow()` and `.ignore()` methods to the boolean `AutomationCondition` operators, which allow asset selections to be propagated to sub-conditions such as `AutomationCondition.any_deps_match()` and `AutomationCondition.all_deps_match()`.
- When using the `DAGSTER_REDACT_USER_CODE_ERRORS` environment variable to mask user code errors, the unmasked log lines are now written using a `dagster.masked` Python logger instead of being written to stderr, allowing the format of those log lines to be customized.
- Added a `get_partition_key()` helper method that can be used on hourly/daily/weekly/monthly partitioned assets to get the partition key for any given partition definition. (Thanks [@Gw1p](https://github.com/Gw1p)!)
- [dagster-aws] Added a `task_definition_prefix` argument to `EcsRunLauncher`, allowing the name of the task definition families for launched runs to be customized. Previously, the task definition families always started with `run`.
- [dagster-aws] Added the `PipesEMRContainersClient` Dagster Pipes client for running and monitoring workloads on [AWS EMR on EKS](https://docs.aws.amazon.com/emr/latest/EMR-on-EKS-DevelopmentGuide/emr-eks.html) with Dagster.
- [dagster-pipes] Added support for setting timestamp metadata (e.g. `{"my_key": {"raw_value": 111, "type": "timestamp"}}`).
- [dagster-databricks, dagster-pipes] Databricks Pipes now support log forwarding when running on existing clusters. It can be enabled by setting `PipesDbfsMessageReader(include_stdio_in_messages=True)`.
- [dagster-polars] Added `rust` engine support when writing a Delta Lake table using native partitioning. (Thanks [@Milias](https://github.com/Milias)!)

### Bugfixes

- Fixed a bug where setting an `AutomationCondition` on an observable source asset could sometimes result in invalid backfills being launched.
- Using `AndAutomationCondition.without()` no longer removes the condition's label.
- [ui] Sensors targeting asset checks now list the asset checks when you click to view their targets.
- [dagster-aws] Fixed the execution of EMR Serverless jobs using `PipesEMRServerlessClient` failing if a job is in the `QUEUED` state.
- [dagster-pipes] Fixed Dagster Pipes log capturing when running on Databricks.
- [dagster-snowflake] Fixed a bug where passing a non-base64-encoded private key to a `SnowflakeResource` resulted in an error.
- [dagster-openai] Updated `openai` kinds tag to be "OpenAI" instead of "Open AI" in line with the OpenAI branding.

### Documentation

- [dagster-pipes] Added a [tutorial](https://docs.dagster.io/concepts/dagster-pipes/pyspark) for using Dagster Pipes with PySpark.

## 1.9.9 (core) / 0.25.9 (libraries)

### New

- Added a new function `load_definitions_from_module`, which can load all the assets, checks, schedules, sensors, and job objects within a module scope into a single Definitions object. Check out [the documentation to learn more](https://docs.dagster.io/_apidocs/definitions#dagster.load_definitions_from_module).
- When using the `DAGSTER_REDACT_USER_CODE_ERRORS` environment variable to mask user code errors, the unmasked log lines are now written using a `dagster.redacted_errors` Python logger instead of being written to stderr, allowing the format of those log lines to be customized.
- The `croniter` package is now vendored in dagster.
- [ui] Corrected the `minstral` typo and updated the Mistral logo for asset `kinds` tag.
- [ui] The relevant runs are now shown within the same dialog when viewing details of an automation evaluation.
- [ui] Clicking to view runs with a specific status from the backfill overview now switches to the new backfill runs tab with your filters applied, instead of the global runs page.
- [ui] In the run timeline, all run ids and timings are now shown in the hover popover.
- [ui] Added a new tab on the Runs page that shows a filterable list of recent backfills.
- [dagster-airlift] Added support for Python 3.7.
- [dagster-aws] Added a `task_definition_prefix` argument to `EcsRunLauncher`, allowing the name of the task definition families for launched runs to be customized. Previously, the task definition families always started with `run`.
- [dagster-azure] Moved azure fake implementations to its own submodule, paving the way for fake implementations to not be imported by default. (Thanks [@futurewasfree](https://github.com/futurewasfree)!)
- [dagster-dlt] The `dagster-dlt` library is added. It replaces the dlt module of `dagster-embedded-elt`.
- [dagster-sling] The `dagster-sling` library is added. It replaces the Sling module of `dagster-embedded-elt`.
- [helm] Added support for sidecar containers for all Dagster pods, for versions of K8s after 1.29 ([Native Sidecars](https://kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/)). (Thanks [@hom3r](https://github.com/hom3r)!)

### Bugfixes

- Fixed an issue where the tick timeline wouldn't load for an automation condition sensor that emitted a backfill.
- Fixed a bug with asset checks where additional_deps/additional_ins were not being threaded through properly in certain cases, and would result in errors at job creation.
- Fixed a bug where the UI will hit an unexpected error when loading details for a run containing a step retry before the step has started.
- Fixed a bug with load_assets_from_x functions where we began erroring when a spec and AssetsDefinition had the same key in a given module. We now only error in this case if include_specs=True.
- Fixed a bug with `load_assets_from_modules` where AssetSpec objects were being given the key_prefix instead of the source_key_prefix. Going forward, when load_specs is set to True, only the source_key_prefix will affect AssetSpec objects.
- Fixed a bug with the run queue criteria UI for branch deployments in Dagster Plus.
- [ui] Fixed the "View evaluation" links from the "Automation condition" tag popover on Runs.
- [dagster-aws] Fixed an issue with the EcsRunLauncher where it would sometimes create a new task definition revision for each run if the "task_role_arn" or "execution_role_arn" parameters were specified without the `arn:aws:iam:` prefix.
- [dagster-aws] Fixed a bug with `PipesEMRServerlessClient` trying to get the dashboard URL for a run before it transitions to RUNNING state.
- [dagster-dbt] Fixed an issue where group names set on partitioned dbt assets created using the `@dbt_assets` decorator would be ignored.
- [dagster-azure] Fixed the default configuration for the `show_url_only` parameter on the `AzureBlobComputeLogManager`. (Thanks [@ion-elgreco](https://github.com/ion-elgreco)!)
- [dagster-aws] Fixed an issue handling null `networkConfiguration` parameters for the ECS run launcher. (Thanks [@markgrin](https://github.com/markgrin)!)

### Documentation

- Added example potential use cases for sensors. (Thanks [@gianfrancodemarco](https://github.com/gianfrancodemarco)!)
- Updated the tutorial to match the outlined structure. (Thanks [@vincent0426](https://github.com/vincent0426)!)

### Deprecations

- [dagster-embedded-elt] the `dagster-embedded-elt` library is deprecated in favor of `dagster-dlt` and `dagster-sling`.

### Dagster Plus

- The Alert Policies page will now show a warning if a slack channel for a policy no longer exists.

## 1.9.8 (core) / 0.25.8 (libraries)

### Bugfixes

- Fixed a bug with `load_assets_from_x` functions where we began erroring when a spec and AssetsDefinition had the same key in a given module. We now only error in this case if `include_specs=True`.
- [dagster-azure] Fixed a bug in 1.9.6 and 1.9.7 where the default behavior of the compute log manager switched from showing logs in the UI to showing a URL. You can toggle the `show_url_only` option to `True` to enable the URL showing behavior.
- [dagster-dbt] Fixed an issue where group names set on partitioned dbt assets created using the `@dbt_assets` decorator would be ignored

## 1.9.7 (core) / 0.25.7 (libraries)

### New

- Added new function `load_definitions_from_module`, which can load all the assets, checks, schedules, sensors, and job objects within a module scope into a single Definitions object. Check out the documentation to learn more: https://docs.dagster.io/_apidocs/definitions#dagster.load_definitions_from_module.
- Previously, asset backfills could only target selections of assets in which all assets had a `BackfillPolicy`, or none of them did. Mixed selections are now supported.
- `AssetSpecs` may now contain a `partitions_def`. Different `AssetSpecs` passed to the same invocation of `@multi_asset` can now have different `PartitionsDefinitions`, as long as `can_subset=True`.
- Added the option to use a thread pool to process backfills in parallel.
- Exceptions that are raised when a schedule or sensor is writing to logs will now write an error message to stdout instead of failing the tick.
- Added validation of `title` for asset backfills (not just for job backfills).
- [ui] Design tweaks to the asset Automations tab.
- [ui] Asset selection filtering is now case insensitive.
- [ui] Add Teradata icon for kind tags.
- [ui] When creating and editing alerts, when the form is in an invalid state, display the reason on the disabled buttons.
- [ui] Add Automation history to asset checks.
- [ui] Improve performance of Run page for very long-running runs.
- [dagster-airbyte] The `airbyte_assets` decorator has been added. It can be used with the `AirbyteCloudWorkspace` resource and `DagsterAirbyteTranslator` translator to load Airbyte tables for a given connection as assets in Dagster. The `build_airbyte_assets_definitions` factory can be used to create assets for all the connections in your Airbyte workspace.
- [dagster-airbyte] Airbyte Cloud assets can now be materialized using the `AirbyteCloudWorkspace.sync_and_poll(…)` method in the definition of a `@airbyte_assets` decorator.
- [dagster-airlift] Airflow imports are now compatible with Airflow 1.
- [dagster-aws] new `ecs_executor` which executes Dagster steps via AWS ECS tasks. This can be used in conjunction with `ECSRunLauncher`.
- [dagster-dbt] `dbt-core>=1.9` is now supported.
- [dagster-dbt] Adds SQL syntax highlighting to raw sql code in dbt asset descriptions.
- [dagster-looker] `load_looker_asset_specs` and `build_looker_pdt_assets_definitions` are updated to accept an instance of `DagsterLookerApiTranslator` or custom subclass.
- [dagster-looker] Type hints in the signature of `DagsterLookerApiTranslator.get_asset_spec` have been updated - the parameter `looker_structure` is now of type `LookerApiTranslatorStructureData` instead of `LookerStructureData`. Custom Looker API translators should be updated.
- [dagster-powerbi] `load_powerbi_asset_specs` has been updated to accept an instance of `DagsterPowerBITranslator` or custom subclass.
- [dagster-powerbi] Type hints in the signature of `DagsterPowerBITranslator.get_asset_spec` have been updated - the parameter `data` is now of type `PowerBITranslatorData` instead of `PowerBIContentData`. Custom Power BI translators should be updated.
- [dagster-sigma] `load_sigma_asset_specs` has been updated to accept an instance of `DagsterSigmaTranslator` or a custom subclass.
- [dagster-sigma] Type hints in the signature of `DagsterLookerApiTranslator.get_asset_spec` have been updated - the parameter `data` is now of type `Union[SigmaDatasetTranslatorData, SigmaWorkbookTranslatorData]` instead of `Union[SigmaDataset, SigmaWorkbook]`. Custom Looker API translators should be updated.
- [dagster-sigma] Added the option to filter to specific workbooks in addition to folders.
- [dagster-sigma] Added the option to skip fetching lineage for workbooks in cases where users want to build this information themselves.
- [dagster-tableau] `load_tableau_asset_specs` has been updated to accept an instance of `DagsterTableauTranslator` or custom subclass.
- [dagster-tableau] Type hints in the signature of `DagsterTableauTranslator.get_asset_spec` have been updated - the parameter `data` is now of type `TableauTranslatorData` instead of `TableauContentData`. Custom Tableau translators should be updated.

### Bugfixes

- Fixed an issue where sensor and schedule tick logs would accumulate disk over time on Dagster code servers.
- [ui] Fixed an issue where the app sometimes loads with styles missing.
- [ui] Fix search string highlighting in global search results.
- Fixed a race condition where immediately after adding a new asset to the graph, a freshness check sensor targeting that asset might raise an InvalidSubsetError in its first one.
- [ui] Fixed a bug where backfills launched by Declarative Automation were not being shown in the table of launched runs.
- The `dagster-airlift` package erroneously introduced a dependency on `dagster`. This has been rectified - `dagster` is only required for the `dagster-airlift[core]` submodule.

### Deprecations

- Deprecation of `@multi_asset_sensor` has been rolled back.

### Dagster Plus

- Introduce the Catalog Viewer role for Users and Teams.
- Slack, MS Teams, and email alerts for run failures will list the steps that were successful or not executed.
- [experimental] The option `blobStorageSnapshotUploads` has been added which enables a new process for how definition snapshots are uploaded to Dagster Cloud.
- Fixed a catalog search issue where exact prefix matches are not prioritized in the search results.
- Fixed a bug with Insights metric customization.

## 1.9.6 (core) / 0.25.6 (libraries)

### New

- Updated `cronitor` pin to allow versions `>= 5.0.1` to enable use of `DayOfWeek` as 7. Cronitor `4.0.0` is still disallowed. (Thanks, [@joshuataylor](https://github.com/joshuataylor)!)
- Added flag `checkDbReadyInitContainer` to optionally disable db check initContainer.
- Added job name filtering to increase the throughput for run status sensors that target jobs.
- [ui] Added Google Drive icon for `kind` tags. (Thanks, [@dragos-pop](https://github.com/dragos-pop)!)
- [ui] Renamed the run lineage sidebar on the Run details page to `Re-executions`.
- [ui] Sensors and schedules that appear in the Runs page are now clickable.
- [ui] Runs targeting assets now show more of the assets in the Runs page.
- [dagster-airbyte] The destination type for an Airbyte asset is now added as a `kind` tag for display in the UI.
- [dagster-gcp] `DataprocResource` now receives an optional parameter `labels` to be attached to Dataproc clusters. (Thanks, [@thiagoazcampos](https://github.com/thiagoazcampos)!)
- [dagster-k8s] Added a `checkDbReadyInitContainer` flag to the Dagster Helm chart to allow disabling the default init container behavior. (Thanks, [@easontm](https://github.com/easontm)!)
- [dagster-k8s] K8s pod logs are now logged when a pod fails. (Thanks, [@apetryla](https://github.com/apetryla)!)
- [dagster-sigma] Introduced `build_materialize_workbook_assets_definition` which can be used to build assets that run materialize schedules for a Sigma workbook.
- [dagster-snowflake] `SnowflakeResource` and `SnowflakeIOManager` both accept `additional_snowflake_connection_args` config. This dictionary of arguments will be passed to the `snowflake.connector.connect` method. This config will be ignored if you are using the `sqlalchemy` connector.
- [helm] Added the ability to set user-deployments labels on k8s deployments as well as pods.

### Bugfixes

- Assets with self dependencies and `BackfillPolicy` are now evaluated correctly during backfills. Self dependent assets no longer result in serial partition submissions or disregarded upstream dependencies.
- Previously, the freshness check sensor would not re-evaluate freshness checks if an in-flight run was planning on evaluating that check. Now, the freshness check sensor will kick off an independent run of the check, even if there's already an in flight run, as long as the freshness check can potentially fail.
- Previously, if the freshness check was in a failing state, the sensor would wait for a run to update the freshness check before re-evaluating. Now, if there's a materialization later than the last evaluation of the freshness check and no planned evaluation, we will re-evaluate the freshness check automatically.
- [ui] Fixed run log streaming for runs with a large volume of logs.
- [ui] Fixed a bug in the Backfill Preview where a loading spinner would spin forever if an asset had no valid partitions targeted by the backfill.
- [dagster-aws] `PipesCloudWatchMessageReader` correctly identifies streams which are not ready yet and doesn't fail on `ThrottlingException`. (Thanks, [@jenkoian](https://github.com/jenkoian)!)
- [dagster-fivetran] Column metadata can now be fetched for Fivetran assets using `FivetranWorkspace.sync_and_poll(...).fetch_column_metadata()`.
- [dagster-k8s] The k8s client now waits for the main container to be ready instead of only waiting for sidecar init containers. (Thanks, [@OrenLederman](https://github.com/OrenLederman)!)

### Documentation

- Fixed a typo in the `dlt_assets` API docs. (Thanks, [@zilto](https://github.com/zilto)!)

## 1.9.5 (core) / 0.25.5 (libraries)

### New

- The automatic run retry daemon has been updated so that there is a single source of truth for if a run will be retried and if the retry has been launched. Tags are now added to run at failure time indicating if the run will be retried by the automatic retry system. Once the automatic retry has been launched, the run ID of the retry is added to the original run.
- When canceling a backfill of a job, the backfill daemon will now cancel all runs launched by that backfill before marking the backfill as canceled.
- Dagster execution info (tags such as `dagster/run-id`, `dagster/code-location`, `dagster/user` and Dagster Cloud environment variables) typically attached to external resources are now available under `DagsterRun.dagster_execution_info`.
- `SensorReturnTypesUnion` is now exported for typing the output of sensor functions.
- [dagster-dbt] dbt seeds now get a valid code version (Thanks [@marijncv](https://github.com/marijncv)!).
- Manual and automatic retries of runs launched by backfills that occur while the backfill is still in progress are now incorporated into the backfill's status.
- Manual retries of runs launched by backfills are no longer considered part of the backfill if the backfill is complete when the retry is launched.
- [dagster-fivetran] Fivetran assets can now be materialized using the FivetranWorkspace.sync_and_poll(…) method in the definition of a `@fivetran_assets` decorator.
- [dagster-fivetran] `load_fivetran_asset_specs` has been updated to accept an instance of `DagsterFivetranTranslator` or custom subclass.
- [dagster-fivetran] The `fivetran_assets` decorator was added. It can be used with the `FivetranWorkspace` resource and `DagsterFivetranTranslator` translator to load Fivetran tables for a given connector as assets in Dagster. The `build_fivetran_assets_definitions` factory can be used to create assets for all the connectors in your Fivetran workspace.
- [dagster-aws] `ECSPipesClient.run` now waits up to 70 days for tasks completion (waiter parameters are configurable) (Thanks [@jenkoian](https://github.com/jenkoian)!)
- [dagster-dbt] Update dagster-dbt scaffold template to be compatible with uv (Thanks [@wingyplus](https://github.com/wingyplus)!).
- [dagster-airbyte] A `load_airbyte_cloud_asset_specs` function has
  been added. It can be used with the `AirbyteCloudWorkspace` resource and `DagsterAirbyteTranslator` translator to load your Airbyte Cloud connection streams as external assets in Dagster.
- [ui] Add an icon for the `icechunk` kind.
- [ui] Improved ui for manual sensor/schedule evaluation.

### Bugfixes

- Fixed database locking bug for the `ConsolidatedSqliteEventLogStorage`, which is mostly used for tests.
- [dagster-aws] Fixed a bug in the ECSRunLauncher that prevented it from accepting a user-provided task definition when DAGSTER_CURRENT_IMAGE was not set in the code location.
- [ui] Fixed an issue that would sometimes cause the asset graph to fail to render on initial load.
- [ui] Fix global auto-materialize tick timeline when paginating.

## 1.9.4 (core) / 0.25.4 (libraries)

### New

- Global op concurrency is now enabled on the default SQLite storage. Deployments that have not been migrated since `1.6.0` may need to run `dagster instance migrate` to enable.
- Introduced `map_asset_specs` to enable modifying `AssetSpec`s and `AssetsDefinition`s in bulk.
- Introduced `AssetSpec.replace_attributes` and `AssetSpec.merge_attributes` to easily alter properties of an asset spec.
- [ui] Add a "View logs" button to open tick logs in the sensor tick history table.
- [ui] Add Spanner kind icon.
- [ui] The asset catalog now supports filtering using the asset selection syntax.
- [dagster-pipes, dagster-aws] `PipesS3MessageReader` now has a new parameter `include_stdio_in_messages` which enables log forwarding to Dagster via Pipes messages.
- [dagster-pipes] Experimental: A new Dagster Pipes message type `log_external_stream` has been added. It can be used to forward external logs to Dagster via Pipes messages.
- [dagster-powerbi] Opts in to using admin scan APIs to pull data from a Power BI instance. This can be disabled by passing `load_powerbi_asset_specs(..., use_workspace_scan=False)`.
- [dagster-sigma] Introduced an experimental `dagster-sigma snapshot` command, allowing Sigma workspaces to be captured to a file for faster subsequent loading.

### Bugfixes

- Fixed a bug that caused `DagsterExecutionStepNotFoundError` errors when trying to execute an asset check step of a run launched by a backfill.
- Fixed an issue where invalid cron strings like "0 0 30 2 \*" that represented invalid dates in February were still allowed as Dagster cron strings, but then failed during schedule execution. Now, these invalid cronstrings will raise an exception when they are first loaded.
- Fixed a bug where `owners` added to `AssetOut`s when defining a `@graph_multi_asset` were not added to the underlying `AssetsDefinition`.
- Fixed a bug where using the `&` or `|` operators on `AutomationCondition`s with labels would cause that label to be erased.
- [ui] Launching partitioned asset jobs from the launchpad now warns if no partition is selected.
- [ui] Fixed unnecessary middle truncation occurring in dialogs.
- [ui] Fixed timestamp labels and "Now" line rendering bugs on the sensor tick timeline.
- [ui] Opening Dagster's UI with a single job defined takes you to the Overview page rather than the Job page.
- [ui] Fix stretched tags in backfill table view for non-partitioned assets.
- [ui] Open automation sensor evaluation details in a dialog instead of navigating away.
- [ui] Fix scrollbars in dark mode.
- [dagster-sigma] Workbooks filtered using a `SigmaFilter` no longer fetch lineage information.
- [dagster-powerbi] Fixed an issue where reports without an upstream dataset dependency would fail to translate to an asset spec.

### Deprecations

- [dagster-powerbi] `DagsterPowerBITranslator.get_asset_key` is deprecated in favor of `DagsterPowerBITranslator.get_asset_spec().key`
- [dagster-looker] `DagsterLookerApiTranslator.get_asset_key` is deprecated in favor of `DagsterLookerApiTranslator.get_asset_spec().key`
- [dagster-sigma] `DagsterSigmaTranslator.get_asset_key` is deprecated in favor of `DagsterSigmaTranslator.get_asset_spec().key`
- [dagster-tableau] `DagsterTableauTranslator.get_asset_key` is deprecated in favor of `DagsterTableauTranslator.get_asset_spec().key`

## 1.9.3 (core) / 0.25.3 (libraries)

### New

- Added `run_id` to the `run_tags` index to improve database performance. Run `dagster instance migrate` to update the index. (Thanks, [@HynekBlaha](https://github.com/HynekBlaha)!)
- Added icons for `kind` tags: Cassandra, ClickHouse, CockroachDB, Doris, Druid, Elasticsearch, Flink, Hadoop, Impala, Kafka, MariaDB, MinIO, Pinot, Presto, Pulsar, RabbitMQ, Redis, Redpanda, ScyllaDB, Starrocks, and Superset. (Thanks, [@swrookie](https://github.com/swrookie)!)
- Added a new icon for the Denodo kind tag. (Thanks, [@tintamarre](https://github.com/tintamarre)!)
- Errors raised from defining more than one `Definitions` object at module scope now include the object names so that the source of the error is easier to determine.
- [ui] Asset metadata entries like `dagster/row_count` now appear on the events page and are properly hidden on the overview page when they appear in the sidebar.
- [dagster-aws] `PipesGlueClient` now attaches AWS Glue metadata to Dagster results produced during Pipes invocation.
- [dagster-aws] `PipesEMRServerlessClient` now attaches AWS EMR Serverless metadata to Dagster results produced during Pipes invocation and adds Dagster tags to the job run.
- [dagster-aws] `PipesECSClient` now attaches AWS ECS metadata to Dagster results produced during Pipes invocation and adds Dagster tags to the ECS task.
- [dagster-aws] `PipesEMRClient` now attaches AWS EMR metadata to Dagster results produced during Pipes invocation.
- [dagster-databricks] `PipesDatabricksClient` now attaches Databricks metadata to Dagster results produced during Pipes invocation and adds Dagster tags to the Databricks job.
- [dagster-fivetran] Added `load_fivetran_asset_specs` function. It can be used with the `FivetranWorkspace` resource and `DagsterFivetranTranslator` translator to load your Fivetran connector tables as external assets in Dagster.
- [dagster-looker] Errors are now handled more gracefully when parsing derived tables.
- [dagster-sigma] Sigma assets now contain extra metadata and kind tags.
- [dagster-sigma] Added support for direct workbook to warehouse table dependencies.
- [dagster-sigma] Added `include_unused_datasets` field to `SigmaFilter` to disable pulling datasets that aren't used by a downstream workbook.
- [dagster-sigma] Added `skip_fetch_column_data` option to skip loading Sigma column lineage. This can speed up loading large instances.
- [dagster-sigma] Introduced an experimental `dagster-sigma snapshot` command, allowing Sigma workspaces to be captured to a file for faster subsequent loading.

  ### Introducing: `dagster-airlift` (experimental)

  `dagster-airlift` is coming out of stealth. See the initial Airlift RFC [here](https://github.com/dagster-io/dagster/discussions/25279), and the following documentation to learn more:
  - A full [Airflow migration tutorial](https://docs.dagster.io/integrations/airlift/tutorial/overview).
  - A tutorial on [federating between Airflow instances](https://docs.dagster.io/integrations/airlift/federation-tutorial/overview).

  More Airflow-related content is coming soon! We'd love for you to check it out, and post any comments / questions in the `#airflow-migration` channel in the Dagster slack.

### Bugfixes

- Fixed a bug in run status sensors where setting incompatible arguments `monitor_all_code_locations` and `monitored_jobs` did not raise the expected error. (Thanks, [@apetryla](https://github.com/apetryla)!)
- Fixed an issue that would cause the label for `AutomationCondition.any_deps_match()` and `AutomationCondition.all_deps_match()` to render incorrectly when `allow_selection` or `ignore_selection` were set.
- Fixed a bug which could cause code location load errors when using `CacheableAssetsDefinitions` in code locations that contained `AutomationConditions`
- Fixed an issue where the default multiprocess executor kept holding onto subprocesses after their step completed, potentially causing `Too many open files` errors for jobs with many steps.
- [ui] Fixed an issue introduced in 1.9.2 where the backfill overview page would sometimes display extra assets that were targeted by the backfill.
- [ui] Fixed "Open in Launchpad" button when testing a schedule or sensor by ensuring that it opens to the correct deployment.
- [ui] Fixed an issue where switching a user setting was immediately saved, rather than waiting for the change to be confirmed.
- [dagster-looker] Unions without unique/distinct criteria are now properly handled.
- [dagster-powerbi] Fixed an issue where reports without an upstream dataset dependency would fail to translate to an asset spec.
- [dagster-sigma] Fixed an issue where API fetches did not paginate properly.

### Documentation

- Added an [Airflow Federation Tutorial](https://docs.dagster.io/integrations/airlift/federation-tutorial/overview).
- Added `dagster-dingtalk` to the list of [community supported libraries](https://docs.dagster.io/integrations#community-supported-libraries).
- Fixed typos in the `dagster-wandb` (Weights and Biases) documentation. (Thanks, [@matt-weingarten](https://github.com/matt-weingarten)!)
- Updated the [Role-based Access Control (RBAC)](https://docs.dagster.io/dagster-plus/account/managing-users/managing-user-roles-permissions) documentation.
- Added additional information about filtering to the [`dagster-sigma`](https://docs.dagster.io/integrations/sigma) documentation.

### Dagster Plus

- [ui] Fixed an issue with filtering and catalog search in branch deployments.
- [ui] Fixed an issue where the asset graph would reload unexpectedly.

## 1.9.2 (core) / 0.25.2 (libraries)

### New

- Introduced a new constructor, `AssetOut.from_spec`, that will construct an `AssetOut` from an `AssetSpec`.
- [ui] Column tags are now displayed in the `Column name` section of the asset overview page.
- [ui] Introduced an icon for the `gcs` (Google Cloud Storage) kind tag.
- [ui] Introduced icons for `report` and `semanticmodel` kind tags.
- [ui] The tooltip for a tag containing a cron expression now shows a human-readable, timezone-aware cron string.
- [ui] Asset check descriptions are now sourced from docstrings and rendered in the UI. (Thanks, [@marijncv](https://github.com/marijncv)!)
- [dagster-aws] Added option to propagate tags to ECS tasks when using the `EcsRunLauncher`. (Thanks, [@zyd14](https://github.com/zyd14)!)
- [dagster-dbt] You can now implement `DagsterDbtTranslator.get_code_version` to customize the code version for your dbt assets. (Thanks, [@Grzyblon](https://github.com/Grzyblon)!)
- [dagster-pipes] Added the ability to pass arbitrary metadata to `PipesClientCompletedInvocation`. This metadata will be attached to all materializations and asset checks stored during the pipes invocation.
- [dagster-powerbi] During a full workspace scan, owner and column metadata is now automatically attached to assets.

### Bugfixes

- Fixed an issue with `AutomationCondition.execution_in_progress` which would cause it to evaluate to `True` for unpartitioned assets that were part of a run that was in progress, even if the asset itself had already been materialized.
- Fixed an issue with `AutomationCondition.run_in_progress` that would cause it to ignore queued runs.
- Fixed an issue that would cause a `default_automation_condition_sensor` to be constructed for user code servers running on dagster version `< 1.9.0` even if the legacy `auto_materialize: use_sensors` configuration setting was set to `False`.
- [ui] Fixed an issue when executing asset checks where the wrong job name was used in some situations. The correct job name is now used.
- [ui] Selecting assets with 100k+ partitions no longer causes the asset graph to temporarily freeze.
- [ui] Fixed an issue that could cause a GraphQL error on certain pages after removing an asset.
- [ui] The asset events page no longer truncates event history in cases where both materialization and observation events are present.
- [ui] The backfill coordinator logs tab no longer sits in a loading state when no logs are available to display.
- [ui] Fixed issue which would cause the "Partitions evaluated" label on an asset's automation history page to incorrectly display `0` in cases where all partitions were evaluated.
- [ui] Fix "Open in Playground" link when testing a schedule or sensor by ensuring that it opens to the correct deployment.
- [ui] Fixed an issue where the asset graph would reload unexpectedly.
- [dagster-dbt] Fixed an issue where the SQL filepath for a dbt model was incorrectly resolved when the dbt manifest file was built on a Windows machine, but executed on a Unix machine.
- [dagster-pipes] Asset keys containing embedded `/` characters now work correctly with Dagster Pipes.

### Documentation

- Community-hosted integrations are now listed on the [Integrations](https://docs.dagster.io/integrations) page.
- Added a [tutorial](https://docs.dagster.io/integrations/airlift/tutorial/overview), [reference page](https://docs.dagster.io/integrations/airlift/reference) and [API docs](https://docs.dagster.io/_apidocs/libraries/dagster-airlift) for `dagster-airlift`.
- Fixed a typo in the label for superseded APIs. (Thanks, [@matt-weingarten](https://github.com/matt-weingarten)!)

### Deprecations

- The `types-sqlalchemy` package is no longer included in the `dagster[pyright]` extra package.

### Dagster Plus

- [ui] The Environment Variables table can now be sorted by name and update time.
- [ui] The code location configuration dialog now contains more metadata about the code location.
- [ui] Fixed an issue where the incorrect user icons were shown in the Users table when a search filter had been applied.

## 1.9.1 (core) / 0.25.1 (libraries)

### New

- `dagster project scaffold` now has an option to create dagster projects from templates with excluded files/filepaths.
- [ui] Filters in the asset catalog now persist when navigating subdirectories.
- [ui] The Run page now displays the partition(s) a run was for.
- [ui] Filtering on owners/groups/tags is now case-insensitive.
- [dagster-tableau] the helper function `parse_tableau_external_and_materializable_asset_specs` is now available to parse a list of Tableau asset specs into a list of external asset specs and materializable asset specs.
- [dagster-looker] Looker assets now by default have owner and URL metadata.
- [dagster-k8s] Added a per_step_k8s_config configuration option to the k8s_job_executor, allowing the k8s configuration of individual steps to be configured at run launch time (thanks @Kuhlwein!)
- [dagster-fivetran] Introduced `DagsterFivetranTranslator` to customize assets loaded from Fivetran.
- [dagster-snowflake] `dagster_snowflake.fetch_last_updated_timestamps` now supports ignoring tables not found in Snowflake instead of raising an error.

### Bugfixes

- Fixed issue which would cause a `default_automation_condition_sensor` to be constructed for user code servers running on dagster version < 1.9.0 even if the legacy `auto_materialize: use_sensors` configuration setting was set to `False`.
- Fixed an issue where running `dagster instance migrate` on Dagster version 1.9.0 constructed a SQL query that exceeded the maximum allowed depth.
- Fixed an issue where wiping a dynamically partitioned asset causes an error.
- [dagster-polars] `ImportError`s are no longer raised when bigquery libraries are not installed [#25708]

### Documentation

- [dagster-dbt] A guide on how to use dbt defer with Dagster branch deployments has been added to the dbt reference.

## 1.9.0 (core) / 0.25.0 (libraries)

## Major changes since 1.8.0 (core) / 0.24.0 (libraries)

### Automation

- Declarative Automation, the system which enables setting per-asset `AutomationConditions`, is no longer experimental. We now recommend using this system in all cases where asset-centric orchestration is desired. A suite of built-in static constructors have been added for common usecases, such as `AutomationCondition.on_missing()` (which can fill in missing partitions of assets as soon as upstream data is available), and `AutomationCondition.all_deps_blocking_checks_passed()` (which can prevent materialization of assets until all upstream blocking checks have passed).
- You can now assign `AutomationConditions` to asset checks, via the `automation_condition` parameter on `@asset_check` or `AssetCheckSpec`.
- You can now assign `AutomationConditions` to observable source assets, via the `automation_condition` parameter on `@observable_source_asset`.
- [experimental] You can now define custom subclasses of `AutomationCondition` to execute arbitrary Python code in the context of a broader expression. This allows you to compose built-in conditions with custom business logic.
- The `target` arguments on schedules and sensors are now marked stable, allowing a stable way for schedules and sensors to target asset selections without needing to define a job.

### Integrations

- Introduced a slate of integrations with business intelligence (BI) tools, enabling dashboards, views, and reports to be represented in the Dagster asset graph.
  - [Looker](https://docs.dagster.io/integrations/looker)
  - [Power BI](https://docs.dagster.io/integrations/powerbi)
  - [Sigma](https://docs.dagster.io/integrations/sigma)
  - [Tableau](https://docs.dagster.io/integrations/tableau)
- A rich set of metadata is now automatically collected by our suite of ELT integrations.
  - The `dagster/table_name` metadata tag, containing the fully-qualified name of the destination model, has been added for Airbyte, dlt, Fivetran and Sling assets.
  - The `dagster/row_count` metadata tag, containing the number of records loaded in the corresponding run, has been added for dlt and Sling assets.
  - The `dagster/column_schema` metadata tag, containing column schema information of the destination tables, has been added for Fivetran assets.
  - Column lineage information is now collected for Sling assets.
- [dagster-pipes](https://docs.dagster.io/concepts/dagster-pipes) are replacing the now deprecated Step Launchers as the new recommended approach for executing remote Spark jobs. Three new [Pipes clients](https://docs.dagster.io/_apidocs/libraries/dagster-aws#clients) for running Spark applications on Amazon Web Services have been added:
  - `dagster_aws.pipes.PipesGlueClient`
  - `dagster_aws.pipes.PipesEMRServerlessClient`
  - `dagster_aws.pipes.PipesEMRClient`

### UI

- Several changes have been made to the information architecture to make it easier to find what you’re looking for:
  - Backfills have been moved from their own tab underneath the Overview page to entries within the table on the Runs page. This reflects the fact that backfills and runs are similar entities that share most properties. You can continue to use the legacy Runs page with the “Revert to legacy Runs page” user setting. ([GitHub Discussion](https://github.com/dagster-io/dagster/discussions/24898))
  - “Jobs” is now a page reachable from the top-level navigation pane. It replaces the Jobs tab within the Overview page.
  - “Automations” is now a page reachable from the top-level navigation pane. It replaces the schedule and sensor tabs within the Overview page.
- `@asset` and `AssetSpec` now have a `kinds` attribute that enables specifying labels that show up on asset nodes in the asset graph in the UI. This supersedes the `compute_kind` attribute.

## Changes since 1.8.13 (core) / 0.24.13 (libraries)

### New

- The `tags` parameter to `@asset` and `AssetSpec` is no longer marked as experimental.
- The `@observable_source_asset` decorator now supports an `automation_condition` argument.
- `AutomationCondition` and associated APIs are no longer marked as experimental.
- Added a new `use_user_code_server` parameter to `AutomationConditionSensorDefinition`. If set, the sensor will be evaluated in the user code server (as traditional sensors are), allowing custom `AutomationCondition` subclasses to be evaluated.
- Added a new column to the BulkActions table, a new column to the Runs table, and a new BackfillTags table to improve the performance of the Runs page. To take advantage of these performance improvements, run `dagster instance migrate`. This migration involves a schema migration to add the new columns and table, and a data migration to populate the new columns for historical backfills and runs.
- Performance improvements when loading definitions with multi-assets with many asset keys.
- [ui] The previously-experimental changes to the top nav are now enabled for all users.
- [ui] Added new code location pages which provide information regarding library versions, metadata, and definitions.
- [ui] The new version of the Runs page is now enabled by default. To use the legacy version of the Runs page, toggle the "Revert to legacy Runs page" user setting.
- [ui] Clicking an asset with failed partitions on the asset health overview now takes you to a list of the failed partitions.
- [ui] The Materialize button runs pre-flight checks more efficiently, resulting in faster run launch times.
- [dagster-pipes] Added support for multi-container log streaming (thanks, [@MattyKuzyk](https://github.com/MattyKuzyk)!)
- [dagster-docker] `container_kwargs.stop_timeout` can now be set when using the `DockerRunLauncher` or `docker_executor` to configure the amount of time that Docker will wait when terminating a run for it to clean up before forcibly stopping it with a SIGKILL signal.
- [dagster-dbt] Performance improvements when loading definitions using `build_dbt_asset_selection`.

### Bugfixes

- [ui] Fixed redirect behavior on full pageloads of the legacy auto-materialize overview page.
- [ui] Plots for assets that emit materialization and observation events at different rates no longer display a time period missing the more frequent event type.
- [ui] Fixed issue causing scrolling to misbehave on the concurrency settings page.
- [helm] The blockOpConcurrencyLimitedRuns section of queuedRunCoordinator now correctly templates the appropriate config.
- [dagster-pipes] Fixed issue where k8s ops would fail after 4 hours (thanks, [@MattyKuzyk](https://github.com/MattyKuzyk)!)

### Documentation

- [dagster-dbt] Added guide for using dbt defer with Dagster branch deployments.
- [docs] Step Launchers documentation has been removed and replaced with references to Dagster Pipes.
- [docs] Fixed code example in Dagster Essentials (thanks, [@aleexharris](https://github.com/aleexharris)!)

### Breaking Changes

- `dagster` no longer supports Python 3.8, which hit EOL on 2024-10-07.
- `dagster` now requires `pydantic>=2`.
- By default, `AutomationConditionSensorDefinitions` will now emit backfills to handle cases where more than one partition of an asset is requested on a given tick. This allows that asset's `BackfillPolicy` to be respected. This feature can be disabled by setting `allow_backfills` to `False`.
- Passing a custom `PartitionsDefinition` subclass into a `Definitions` object now issues an error instead of a deprecation warning.
- `AssetExecutionContext` is no longer a subclass of `OpExecutionContext`. At this release, `AssetExecutionContext` and `OpExecutionContext` implement the same methods, but in the future, the methods implemented by each class may diverge. If you have written helper functions with `OpExecutionContext` type annotations, they may need to be updated to include `AssetExecutionContext` depending on your usage. Explicit calls to `isinstance(context, OpExecutionContext)` will now fail if `context` is an `AssetExecutionContext`.
- The `asset_selection` parameter on `AutomationConditionSensorDefinition` has been renamed to `target`, to align with existing sensor APIs.
- The experimental `freshness_policy_sensor` has been removed, as it relies on the long-deprecated `FreshnessPolicy` API.
- The deprecated `external_assets_from_specs` and `external_asset_from_spec` methods have been removed. Users should use `AssetsDefinition(specs=[...])`, or pass specs directly into the `Definitions` object instead.
- `AssetKey` objects can no longer be iterated over or indexed in to. This behavior was never an intended access pattern and in all observed cases was a mistake.
- The `dagster/relation_identifier` metadata key has been renamed to `dagster/table_name`.
- [dagster-ge] `dagster-ge` now only supports `great_expectations>=0.17.15`. The `ge_validation_op_factory` API has been replaced with the API previously called `ge_validation_op_factory_v3`.
- [dagster-aws] Removed deprecated parameters from `dagster_aws.pipes.PipesGlueClient.run`.
- [dagster-embedded-elt] Removed deprecated parameter `dlt_dagster_translator` from `@dlt_assets`. The `dagster_dlt_translator` parameter should be used instead.
- [dagster-polars] Dropped support for saving storage-level arbitrary metadata via IOManagers.

### Deprecations

- The `DataBricksPysparkStepLauncher`, `EmrPySparkStepLauncher`, and any custom subclass of `StepLauncher` have been marked as deprecated, but will not be removed from the codebase until Dagster 2.0 is released, meaning they will continue to function as they currently do for the foreseeable future. Their functionality has been superseded by the interfaces provided by `dagster-pipes`, and so future development work will be focused there.
- The experimental `multi_asset_sensor` has been marked as deprecated, as its main use cases have been superseded by the `AutomationCondition` APIs. However, it will not be removed until version 2.0.0.

## 1.8.13 (core) / 0.24.13 (libraries)

### New

- Performance improvements when loading code locations using multi-assets with many asset keys.
- `AutomationCondition.in_progress()` now will be true if an asset partition is part of an in-progress backfill that has not yet executed it. The prior behavior, which only considered runs, is encapsulated in `AutomationCondition.execution_in_progress()`.
- [ui] Added tag filter to the jobs page.
- [ui] Preserve user login state for a longer period of time.
- [dagster-dbt] Performance improvements when loading definitions using `build_dbt_asset_selection`.
- [dagster-docker] `container_kwargs.stop_timeout` can now be set when using the `DockerRunLauncher` or `docker_executor` to configure the amount of time that Docker will wait when terminating a run for it to clean up before forcibly stopping it with a SIGKILL signal.
- [dagster-sigma] The Sigma integration now fetches initial API responses in parallel, speeding up initial load.
- [dagster-looker] Attempt to naively render liquid templates for derived table sql.
- [dagster-looker] Added support for views and explores that rely on refinements or extends.
- [dagster-looker] When fetching explores and dashboards from the Looker API, retrieve in parallel.

### Bugfixes

- Fixed an issue with `AutomationCondition.eager()` that could cause it to attempt to launch a second attempt of an asset in cases where it was skipped or failed during a run where one of its parents successfully materialized.
- Fixed an issue which would cause `AutomationConditionSensorDefinitions` to not be evaluated if the `use_user_code_server` value was toggled after the initial evaluation.
- Fixed an issue where configuration values for aliased pydantic fields would be dropped.
- [ui] Fix an issue in the code locations page where invalid query parameters could crash the page.
- [ui] Fix navigation between deployments when query parameters are present in the URL.
- [helm] the blockOpConcurrencyLimitedRuns section of queuedRunCoordinator now correctly templates the appropriate config.
- [dagster-sigma] Fixed pulling incomplete data for very large workspaces.

## 1.8.12 (core) / 0.24.12 (libraries)

### New

- The `AutomationCondition.eager()`, `AutomationCondition.missing()`, and `AutomationCondition.on_cron` conditions are now compatible with asset checks.
- Added `AssetSelection.materializable()`, which returns only assets that are materializable in an existing selection.
- Added a new `AutomationCondition.all_deps_blocking_checks_passed` condition, which can be used to prevent materialization when any upstream blocking checks have failed.
- Added a `code_version` parameter to the `@graph_asset` decorator.
- If a `LaunchPartitionBackfill` mutation is submitted to GQL with invalid partition keys, it will now return an early `PartitionKeysNotFoundError`.
- `AssetSelection.checks_for_assets` now accepts `AssetKey`s and string asset keys, in addition to `AssetsDefinition`s.
- [ui] Added a search bar to partitions tab on the asset details page.
- [ui] Restored docked left nav behavior for wide viewports.
- [dagster-aws] `get_objects` now has a `since_last_modified` that enables only fetching objects modified after a given timestamp.
- [dagster-aws] New AWS EMR Dagster Pipes client (`dagster_aws.pipes.PipesEMRCLient` ) for running and monitoring AWS EMR jobs from Dagster.
- [dagster-looker] Pinned the looker-sdk dependency below 24.18.0 to avoid this issue: https://github.com/looker-open-source/sdk-codegen/issues/1518.

### Bugfixes

- Fixed an issue which could cause incorrect evaluation results when using self-dependent partition mappings with `AutomationConditions` that operate over dependencies.
- [ui] Fixed an issue where the breadcumb on asset pages would flicker nonstop.
- [dagster-embedded-elt] Fixed extraction of metadata for dlt assets whose source and destination identifiers differ.
- [dagster-databricks] Fixed a permissioning gap that existed with the `DatabricksPySparkStepLauncher`, so that permissions are now set correctly for non-admin users.
- [dagster-dbt] Fixed an issue where column metadata generated with `fetch_column_metadata` did not work properly for models imported through dbt dependencies.

### Documentation

- [dagster-k8s] `DagsterK8sPipesClient.run` now shows up in API docs.

### Dagster Plus

- [ui] Fixed a bug in the catalog UI where owners filters were not applied correctly.
- [ui] Fixed width of the column lineage dropdown selector on the asset page.
- [ui] Column lineage now correctly renders when set on asset definition metadata
- [ui] Fixed Settings link on the list of deployments, for users in the legacy navigation flag.

## 1.8.11 (core) / 0.24.11 (libraries)

### New

- [experimental] AutomationCondition.eager() will now only launch runs for missing partitions which become missing _after_ the condition has been added to the asset. This avoids situations in which the eager policy kicks off a large amount of work when added to an asset with many missing historical static/dynamic partitions.
- [experimental] Added a new AutomationCondition.asset_matches() condition, which can apply a condition against an arbitrary asset in the graph.
- [experimental] Added the ability to specify multiple kinds for an asset with the kinds parameter.
- [dagster-github] Added `create_pull_request` method on `GithubClient` that enables creating a pull request.
- [dagster-github] Added `create_ref` method on `GithubClient` that enables creating a new branch.
- [dagster-embedded-elt] dlt assets now generate column metadata for child tables.
- [dagster-embedded-elt] dlt assets can now fetch row count metadata with `dlt.run(...).fetch_row_count()` for both partitioned and non-partitioned assets. Thanks [@kristianandre](https://github.com/kristianandre)!
- [dagster-airbyte] relation identifier metadata is now attached to Airbyte assets.
- [dagster-embedded-elt] relation identifier metadata is now attached to sling assets.
- [dagster-embedded-elt] relation identifier metadata is now attached to dlt assets.

### Bugfixes

- `PartitionedConfig` objects can now return a `RunConfig` without causing a crash.
- Corrected the `AssetIn.__new__` typing for the dagster_type argument.
- [dagster-embedded-elt] dlt assets now generate correct column metadata after the first materialization.
- [dagster-embedded-elt] Sling's `fetch_row_count()` method now works for databases returning uppercase column names. Thanks [@kristianandre](https://github.com/kristianandre)!
- [dagster-gcp] Ensure blob download is flushed to temporary file for `GCSFileManager.read` operations. Thanks [@ollie-bell](https://github.com/ollie-bell)!

### Dagster Plus

- Fixed a bug in the catalog UI where owners filters were not applied correctly.

## 1.8.10 (core) / 0.24.10 (libraries)

### New

- `JobDefinition`, `@job`, and `define_asset_job` now take a `run_tags` parameter. If `run_tags` are defined, they will be attached to all runs of the job, and `tags` will not be. If `run_tags` is not set, then `tags` are attached to all runs of the job (status quo behavior). This change enables the separation of definition-level and run-level tags on jobs.
- Then env var `DAGSTER_COMPUTE_LOG_TAIL_WAIT_AFTER_FINISH` can now be used to pause before capturing logs (thanks @HynekBlaha!)
- The `kinds` parameter is now available on `AssetSpec`.
- `OutputContext` now exposes the `AssetSpec` of the asset that is being stored as an output (thanks, @marijncv!)
- [experimental] Backfills are incorporated into the Runs page to improve observability and provide a more simplified UI. See the [GitHub discussion](https://github.com/dagster-io/dagster/discussions/24898) for more details.
- [ui] The updated navigation is now enabled for all users. You can revert to the legacy navigation via a feature flag. See [GitHub discussion](https://github.com/dagster-io/dagster/discussions/21370) for more.
- [ui] Improved performance for loading partition statuses of an asset job.
- [dagster-docker] Run containers launched by the DockerRunLauncher now include dagster/job_name and dagster/run_id labels.
- [dagster-aws] The ECS launcher now automatically retries transient ECS RunTask failures (like capacity placement failures).

### Bugfixes

- Changed the log volume for global concurrency blocked runs in the run coordinator to be less spammy.
- [ui] Asset checks are now visible in the run page header when launched from a schedule.
- [ui] Fixed asset group outlines not rendering properly in Safari.
- [ui] Reporting a materialization event now removes the asset from the asset health "Execution failures" list and returns the asset to a green / success state.
- [ui] When setting an `AutomationCondition` on an asset, the label of this condition will now be shown in the sidebar on the Asset Details page.
- [ui] Previously, filtering runs by Created date would include runs that had been updated after the lower bound of the requested time range. This has been updated so that only runs created after the lower bound will be included.
- [ui] When using the new experimental navigation flag, added a fix for the automations page for code locations that have schedules but no sensors.
- [ui] Fixed tag wrapping on asset column schema table.
- [ui] Restored object counts on the code location list view.
- [ui] Padding when displaying warnings on unsupported run coordinators has been corrected (thanks @hainenber!)
- [dagster-k8s] Fixed an issue where run termination sometimes did not terminate all step processes when using the k8s_job_executor, if the termination was initiated while it was in the middle of launching a step pod.

### Documentation

- Corrections on the Dagster instance concept page (thanks @mheguy!)
- Corrections on the code locations concept page (thanks @tiberiuana!)
- Repeated words removed (thanks @tianzedavid!)
- [dagster-deltalake] Corrections and improvements (thanks @avriiil!)
- [dagster-aws] Added docs for PipesEMRServerlessClient.
- [dagster-cli] A guide on how to validate Dagster definitions using `dagster definitions validate` have been added.
- [dagster-databricks] Added docs for using Databricks Pipes with existing clusters.
- [dagster-dbt] Corrected sample sql code (thanks @b-per!)

## 1.8.9 (core) / 0.24.9 (libraries)

### New

- `AssetSpec` now has a `with_io_manager_key` method that returns an `AssetSpec` with the appropriate metadata entry to dictate the key for the IO manager used to load it. The deprecation warning for `SourceAsset` now references this method.
- Added a `max_runtime_seconds` configuration option to run monitoring, allowing you to specify that any run in your Dagster deployment should terminate if it exceeds a certain runtime. Prevoiusly, jobs had to be individually tagged with a `dagster/max_runtime` tag in order to take advantage of this feature. Jobs and runs can still be tagged in order to override this value for an individual run.
- It is now possible to set both `tags` and a custom `execution_fn` on a `ScheduleDefinition`. Schedule `tags` are intended to annotate the definition and can be used to search and filter in the UI. They will not be attached to run requests emitted from the schedule if a custom `execution_fn` is provided. If no custom `execution_fn` is provided, then for back-compatibility the tags will also be automatically attached to run requests emitted from the schedule.
- `SensorDefinition` and all of its variants/decorators now accept a `tags` parameter. The tags annotate the definition and can be used to search and filter in the UI.
- Added the `dagster definitions validate` command to Dagster CLI. This command validates if Dagster definitions are loadable.
- [dagster-databricks] Databricks Pipes now allow running tasks in existing clusters.

### Bugfixes

- Fixed an issue where calling `build_op_context` in a unit test would sometimes raise a `TypeError: signal handler must be signal.SIG_IGN, signal.SIG_DFL, or a callable object` Exception on process shutdown.
- [dagster-webserver] Fix an issue where the incorrect sensor/schedule state would appear when using `DefaultScheduleStatus.STOPPED` / `DefaultSensorStatus.STOPPED` after performing a reset.

### Documentation

- [dagster-pipes] Fixed inconsistencies in the k8s pipes example.
- [dagster-pandas-pyspark] Fixed example in the Spark/Pandas SDA guide.

### Dagster Plus

- Fixed an issue where users with Launcher permissions for a particular code location were not able to cancel backfills targeting only assets in that code location.
- Fixed an issue preventing long-running alerts from being sent when there was a quick subsequent run.

## 1.8.8 (core) / 0.24.8 (libraries)

### New

- Added `--partition-range` option to `dagster asset materialize` CLI. This option only works for assets with single-run Backfill Policies.
- Added a new `.without()` method to `AutomationCondition.eager()`, `AutomationCondition.on_cron()`, and `AutomationCondition.on_missing()` which allows sub-conditions to be removed, e.g. `AutomationCondition.eager().without(AutomationCondition.in_latest_time_window())`.
- Added `AutomationCondition.on_missing()`, which materializes an asset partition as soon as all of its parent partitions are filled in.
- `pyproject.toml` can now load multiple Python modules as individual Code Locations. Thanks, [@bdart](https://github.com/bdart)!
- [ui] If a code location has errors, a button will be shown to view the error on any page in the UI.
- [dagster-adls2] The `ADLS2PickleIOManager` now accepts `lease_duration` configuration. Thanks, [@0xfabioo](https://github.com/0xfabioo)!
- [dagster-embedded-elt] Added an option to fetch row count metadata after running a Sling sync by calling `sling.replicate(...).fetch_row_count()`.
- [dagster-fivetran] The dagster-fivetran integration will now automatically pull and attach column schema metadata after each sync.

### Bugfixes

- Fixed an issue which could cause errors when using `AutomationCondition.any_downstream_condition()` with downstream `AutoMaterializePolicy` objects.
- Fixed an issue where `process_config_and_initialize` did not properly handle processing nested resource config.
- [ui] Fixed an issue that would cause some AutomationCondition evaluations to be labeled `DepConditionWrapperCondition` instead of the key that they were evaluated against.
- [dagster-webserver] Fixed an issue with code locations appearing in fluctuating incorrect state in deployments with multiple webserver processes.
- [dagster-embedded-elt] Fixed an issue where Sling column lineage did not correctly resolve int the Dagster UI.
- [dagster-k8s] The `wait_for_pod` check now waits until all pods are available, rather than erroneously returning after the first pod becomes available. Thanks [@easontm](https://github.com/easontm)!

### Dagster Plus

- Backfill daemon logs are now available in the "Coordinator Logs" tab in a backfill details page.
- Users without proper code location permissions can no longer edit sensor cursors.

## 1.8.7 (core) / 0.24.7 (libraries)

### New

- The `AssetSpec` constructor now raises an error if an invalid group name is provided, instead of an error being raised when constructing the `Definitions` object.
- `dagster/relation_identifier` metadata is now automatically attached to assets which are stored using a DbIOManager.
- [ui] Streamlined the code location list view.
- [ui] The “group by” selection on the Timeline Overview page is now part of the query parameters, meaning it will be retained when linked to directly or when navigating between pages.
- [dagster-dbt] When instantiating `DbtCliResource`, the `project_dir` argument will now override the `DBT_PROJECT_DIR` environment variable if it exists in the local environment (thanks, [@marijncv](https://github.com/marijncv)!).
- [dagster-embedded-elt] dlt assets now generate `rows_loaded` metadata (thanks, [@kristianandre](https://github.com/kristianandre)!).
- Added support for pydantic version 1.9.0.

### Bugfixes

- Fixed a bug where setting `asset_selection=[]` on `RunRequest` objects yielded from sensors using `asset_selection` would select all assets instead of none.
- Fixed bug where the tick status filter for batch-fetched graphql sensors was not being respected.
- [examples] Fixed missing assets in `assets_dbt_python` example.
- [dagster-airbyte] Updated the op names generated for Airbyte assets to include the full connection ID, avoiding name collisions.
- [dagster-dbt] Fixed issue causing dagster-dbt to be unable to load dbt projects where the adapter did not have a `database` field set (thanks, [@dargmuesli](https://github.com/dargmuesli)!)
- [dagster-dbt] Removed a warning about not being able to load the `dbt.adapters.duckdb` module when loading dbt assets without that package installed.

### Documentation

- Fixed typo on the automation concepts page (thanks, [@oedokumaci](https://github.com/oedokumaci)!)

### Dagster Plus

- You may now wipe specific asset partitions directly from the execution context in user code by calling `DagsterInstance.wipe_asset_partitions`.
- Dagster+ users with a "Viewer" role can now create private catalog views.
- Fixed an issue where the default IOManager used by Dagster+ Serverless did not respect setting `allow_missing_partitions` as metadata on a downstream asset.

## 1.8.6 (core) / 0.24.6 (libraries)

### Bugfixes

- Fixed an issue where runs in Dagster+ Serverless that materialized partitioned assets would sometimes fail with an `object has no attribute '_base_path'` error.
- [dagster-graphql] Fixed an issue where the `statuses` filter argument to the `sensorsOrError` GraphQL field was sometimes ignored when querying GraphQL for multiple sensors at the same time.

## 1.8.5 (core) / 0.24.5 (libraries)

### New

- Updated multi-asset sensor definition to be less likely to timeout queries against the asset history storage.
- Consolidated the `CapturedLogManager` and `ComputeLogManager` APIs into a single base class.
- [ui] Added an option under user settings to clear client side indexeddb caches as an escape hatch for caching related bugs.
- [dagster-aws, dagster-pipes] Added a new `PipesECSClient` to allow Dagster to interface with ECS tasks.
- [dagster-dbt] Increased the default timeout when terminating a run that is running a `dbt` subprocess to wait 25 seconds for the subprocess to cleanly terminate. Previously, it would only wait 2 seconds.
- [dagster-sdf] Increased the default timeout when terminating a run that is running an `sdf` subprocess to wait 25 seconds for the subprocess to cleanly terminate. Previously, it would only wait 2 seconds.
- [dagster-sdf] Added support for caching and asset selection (Thanks, [akbog](https://github.com/akbog)!)
- [dagster-dlt] Added support for `AutomationCondition` using `DagsterDltTranslator.get_automation_condition()` (Thanks, [aksestok](https://github.com/aksestok)!)
- [dagster-k8s] Added support for setting `dagsterDaemon.runRetries.retryOnAssetOrOpFailure` to False in the Dagster Helm chart to [prevent op retries and run retries from simultaneously firing on the same failure.](https://docs.dagster.io/deployment/run-retries#combining-op-and-run-retries)
- [dagster-wandb] Removed usage of deprecated `recursive` parameter (Thanks, [chrishiste](https://github.com/chrishiste)!)

### Bugfixes

- [ui] Fixed a bug where in-progress runs from a backfill could not be terminated from the backfill UI.
- [ui] Fixed a bug that caused an "Asset must be part of at least one job" error when clicking on an external asset in the asset graph UI
- Fixed an issue where viewing run logs with the latest 5.0 release of the watchdog package raised an exception.
- [ui] Fixed issue causing the “filter to group” action in the lineage graph to have no effect.
- [ui] Fixed case sensitivity when searching for partitions in the launchpad.
- [ui] Fixed a bug which would redirect to the events tab for an asset if you loaded the partitions tab directly.
- [ui] Fixed issue causing runs to get skipped when paging through the runs list (Thanks, [@HynekBlaha](https://github.com/HynekBlaha)!)
- [ui] Fixed a bug where the asset catalog list view for a particular group would show all assets.
- [dagster-dbt] fix bug where empty newlines in raw dbt logs were not being handled correctly.
- [dagster-k8s, dagster-celery-k8s] Correctly set `dagster/image` label when image is provided from `user_defined_k8s_config`. (Thanks, [@HynekBlaha](https://github.com/HynekBlaha)!)
- [dagster-duckdb] Fixed an issue for DuckDB versions older than 1.0.0 where an unsupported configuration option, `custom_user_agent`, was provided by default
- [dagster-k8s] Fixed an issue where Kubernetes Pipes failed to create a pod if the op name contained capital or non-alphanumeric containers.
- [dagster-embedded-elt] Fixed an issue where dbt assets downstream of Sling were skipped

### Deprecations

- [dagser-aws]: Direct AWS API arguments in `PipesGlueClient.run` have been deprecated and will be removed in `1.9.0`. The new `params` argument should be used instead.

### Dagster Plus

- Fixed a bug that caused an error when loading the launchpad for a partition, when using Dagster+ with an agent with version below 1.8.2.
- Fixed an issue where terminating a Dagster+ Serverless run wouldn’t forward the termination signal to the job to allow it to cleanly terminate.

## 1.8.4 (core) / 0.24.4 (libraries)

### Bugfixes

- Fixed an issue where viewing run logs with the latest 5.0 release of the watchdog package raised an exception.
- Fixed a bug that caused an "Asset must be part of at least one job" error when clicking on an external asset in the asset graph UI

### Dagster Plus

- The default io_manager on Serverless now supports the `allow_missing_partitions` configuration option.
- Fixed a bug that caused an error when loading the launchpad for a partition, when using in Dagster+ with an agent with version below 1.8.2

## 1.8.3 (core) / 0.24.3 (libraries) (YANKED)

This version of Dagster resulted in errors when trying to launch runs that target individual asset partitions)

### New

- When different assets within a code location have different `PartitionsDefinition`s, there will no longer be an implicit asset job `__ASSET_JOB_...` for each `PartitionsDefinition`; there will just be one with all the assets. This reduces the time it takes to load code locations with assets with many different `PartitionsDefinition`s.

## 1.8.2 (core) / 0.24.2 (libraries)

### New

- [ui] Improved performance of the Automation history view for partitioned assets
- [ui] You can now delete dynamic partitions for an asset from the ui
- [dagster-sdf] Added support for quoted table identifiers (Thanks, [@akbog](https://github.com/akbog)!)
- [dagster-openai] Add additional configuration options for the `OpenAIResource` (Thanks, [@chasleslr](https://github.com/chasleslr)!)
- [dagster-fivetran] Fivetran assets now have relation identifier metadata.

### Bugfixes

- [ui] Fixed a collection of broken links pointing to renamed Declarative Automation pages.
- [dagster-dbt] Fixed issue preventing usage of `MultiPartitionMapping` with `@dbt_assets` (Thanks, [@arookieds](https://github.com/arookieds)!)
- [dagster-azure] Fixed issue that would cause an error when configuring an `AzureBlobComputeLogManager` without a `secret_key` (Thanks, [@ion-elgreco](https://github.com/ion-elgreco) and [@HynekBlaha](https://github.com/HynekBlaha)!)

### Documentation

- Added API docs for `AutomationCondition` and associated static constructors.
- [dagster-deltalake] Corrected some typos in the integration reference (Thanks, [@dargmuesli](https://github.com/dargmuesli)!)
- [dagster-aws] Added API docs for the new `PipesCloudWatchMessageReader`

## 1.8.1 (core) / 0.24.1 (libraries)

### New

- If the sensor daemon fails while submitting runs, it will now checkpoint its progress and attempt to submit the remaining runs on the next evaluation.
- `build_op_context` and `build_asset_context` now accepts a `run_tags` argument.
- Nested partially configured resources can now be used outside of `Definitions`.
- [ui] Replaced GraphQL Explorer with GraphiQL.
- [ui] The run timeline can now be grouped by job or by automation.
- [ui] For users in the experimental navigation flag, schedules and sensors are now in a single merged automations table.
- [ui] Logs can now be filtered by metadata keys and values.
- [ui] Logs for `RUN_CANCELED` events now display relevant error messages.
- [dagster-aws] The new `PipesCloudWatchMessageReader` can consume logs from CloudWatch as pipes messages.
- [dagster-aws] Glue jobs launched via pipes can be automatically canceled if Dagster receives a termination signal.
- [dagster-azure] `AzureBlobComputeLogManager` now supports service principals, thanks @[ion-elgreco](https://github.com/ion-elgreco)!
- [dagster-databricks] `dagster-databricks` now supports `databricks-sdk<=0.17.0`.
- [dagster-datahub] `dagster-datahub` now allows pydantic versions below 3.0.0, thanks @[kevin-longe-unmind](https://github.com/kevin-longe-unmind)!
- [dagster-dbt] The `DagsterDbtTranslator` class now supports a modfiying the `AutomationCondition` for dbt models by overriding `get_automation_condition`.
- [dagster-pandera] `dagster-pandera` now supports `polars`.
- [dagster-sdf] Table and columns tests can now be used as asset checks.
- [dagster-embedded-elt] Column metadata and lineage can be fetched on Sling assets by chaining the new `replicate(...).fetch_column_metadata()` method.
- [dagster-embedded-elt] dlt resource docstrings will now be used to populate asset descriptions, by default.
- [dagster-embedded-elt] dlt assets now generate column metadata.
- [dagster-embedded-elt] dlt transformers now refer to the base resource as upstream asset.
- [dagster-openai] `OpenAIResource` now supports `organization`, `project` and `base_url` for configurting the OpenAI client, thanks @[chasleslr](https://github.com/chasleslr)!
- [dagster-pandas][dagster-pandera][dagster-wandb] These libraries no longer pin `numpy<2`, thanks @[judahrand](https://github.com/judahrand)!

### Bugfixes

- Fixed a bug for job backfills using backfill policies that materialized multiple partitions in a single run would be launched multiple times.
- Fixed an issue where runs would sometimes move into a FAILURE state rather than a CANCELED state if an error occurred after a run termination request was started.
- [ui] Fixed a bug where an incorrect dialog was shown when canceling a backfill.
- [ui] Fixed the asset page header breadcrumbs for assets with very long key path elements.
- [ui] Fixed the run timeline time markers for users in timezones that have off-hour offsets.
- [ui] Fixed bar chart tooltips to use correct timezone for timestamp display.
- [ui] Fixed an issue introduced in the 1.8.0 release where some jobs created from graph-backed assets were missing the “View as Asset Graph” toggle in the Dagster UI.

### Breaking Changes

- [dagster-airbyte] `AirbyteCloudResource` now supports `client_id` and `client_secret` for authentication - the `api_key` approach is no longer supported. This is motivated by the [deprecation of portal.airbyte.com](https://reference.airbyte.com/reference/portalairbytecom-deprecation) on August 15, 2024.

### Deprecations

- [dagster-databricks] Removed deprecated authentication clients provided by `databricks-cli` and `databricks_api`
- [dagster-embedded-elt] Removed deprecated Sling resources `SlingSourceConnection`, `SlingTargetConnection`
- [dagster-embedded-elt] Removed deprecated Sling resources `SlingSourceConnection`, `SlingTargetConnection`
- [dagster-embedded-elt] Removed deprecated Sling methods `build_sling_assets`, and `sync`

### Documentation

- The Integrating Snowflake & dbt with Dagster+ Insights guide no longer erroneously references BigQuery, thanks @[dnxie12](https://github.com/dnxie12)!

## 1.8.0 (core) / 0.24.0 (libraries)

## Major changes since 1.7.0 (core) / 0.22.0 (libraries)

### Core definition APIs

- You can now pass `AssetSpec` objects to the `assets` argument of `Definitions`, to let Dagster know about assets without associated materialization functions. This replaces the experimental `external_assets_from_specs` API, as well as `SourceAsset`s, which are now deprecated. Unlike `SourceAsset`s, `AssetSpec`s can be used for non-materializable assets with dependencies on Dagster assets, such as BI dashboards that live downstream of warehouse tables that are orchestrated by Dagster. [[docs](https://docs.dagster.io/concepts/assets/external-assets)].
- [Experimental] You can now merge `Definitions` objects together into a single larger `Definitions` object, using the new `Definitions.merge` API ([doc](https://docs.dagster.io/_apidocs/definitions#dagster.Definitions.merge)). This makes it easier to structure large Dagster projects, as you can construct a `Definitions` object for each sub-domain and then merge them together at the top level.

### Partitions and backfills

- `BackfillPolicy`s assigned to assets are now respected for backfills launched from jobs that target those assets.
- You can now wipe materializations for individual asset partitions.

### Automation

- [Experimental] You can now add `AutomationCondition`s to your assets to have them automatically executed in response to specific conditions ([docs](https://docs.dagster.io/concepts/automation/declarative-automation)). These serve as a drop-in replacement and improvement over the `AutoMaterializePolicy` system, which is being marked as deprecated.
- [Experimental] Sensors and schedules can now directly target assets, via the new `target` parameter, instead of needing to construct a job.
- [Experimental] The Timeline page can now be grouped by job or automation. When grouped by automation, all runs launched by a sensor responsible for evaluating automation conditions will get bucketed to that sensor in the timeline instead of the "Ad-hoc materializations" row. Enable this by opting in to the `Experimental navigation` feature flag in user settings.

### Catalog

- The Asset Details page now prominently displays row count and relation identifier (table name, schema, database), when corresponding asset metadata values are provided. For more information, see the [metadata and tags docs](https://docs.dagster.io/concepts/metadata-tags#metadata--tags).
- Introduced code reference metadata which can be used to open local files in your editor, or files in source control in your browser. Dagster can automatically attach code references to your assets’ Python source. For more information, see the [docs](https://docs.dagster.io/guides/dagster/code-references).

### Data quality and reliability

- [Experimental] Metadata bound checks – The new `build_metadata_bounds_checks` API [[doc](https://docs.dagster.io/_apidocs/asset-checks#dagster.build_metadata_bounds_checks)] enables easily defining asset checks that fail if a numeric asset metadata value falls outside given bounds.
- [Experimental] Freshness checks from dbt config - Freshness checks can now be set on dbt assets, straight from dbt. Check out the API docs for [build_freshness_checks_from_dbt_assets](https://docs.dagster.io/_apidocs/libraries/dagster-dbt#dagster_dbt.build_freshness_checks_from_dbt_assets) for more.

### Integrations

- Dagster Pipes (`PipesSubprocessClient`) and its integrations with Lambda (`PipesLambdaClient`), Kubernetes (`PipesK8sClient`), and Databricks (`PipesDatabricksClient`) are no longer experimental.
- The new `DbtProject` class ([docs](https://docs.dagster.io/_apidocs/libraries/dagster-dbt#dagster_dbt.DbtProject)) makes it simpler to define dbt assets that can be constructed in both development and production. `DbtProject.prepare_if_dev()` eliminates boilerplate for local development, and the `dagster-dbt project prepare-and-package` CLI can helps pull deps and generate the manifest at build time.
- [Experimental] The `dagster-looker` package can be used to define a set of Dagster assets from a Looker project that is defined in LookML and is backed by git. See the [GitHub discussion](https://github.com/dagster-io/dagster/discussions/23479) for more details.

### Dagster Plus

- Catalog views — In Dagster+, selections into the catalog can now be saved and shared across an organization as catalog views. Catalog views have a name and description, and can be applied to scope the catalog, asset health, and global asset lineage pages against the view’s saved selection.
- Code location history — Dagster+ now stores a history of code location deploys, including the ability to revert to a previously deployed configuration.

## Changes since 1.7.16 (core) / 0.22.16 (libraries)

### New

- The target of both schedules and sensors can now be set using an experimental `target` parameter that accepts an `AssetSelection` or list of assets. Any assets passed this way will also be included automatically in the `assets` list of the containing `Definitions` object.
- `ScheduleDefinition` and `SensorDefinition` now have a `target` argument that can accept an `AssetSelection`.
- You can now wipe materializations for individual asset partitions.
- `AssetSpec` now has a `partitions_def` attribute. All the `AssetSpec`s provided to a `@multi_asset` must have the same `partitions_def`.
- The `assets` argument on `materialize` now accepts `AssetSpec`s.
- The `assets` argument on `Definitions` now accepts `AssetSpec`s.
- The new `merge` method on `Definitions` enables combining multiple `Definitions` object into a single larger `Definition`s object with their combined contents.
- Runs requested through the Declarative Automation system now have a `dagster/from_automation_condition: true` tag applied to them.
- Changed the run tags query to be more performant. Thanks [@egordm](https://github.com/egordm)!
- Dagster Pipes and its integrations with Lambda, Kubernetes, and Databricks are no longer experimental.
- The `Definitions` constructor will no longer raise errors when the provided definitions aren’t mutually resolve-able – e.g. when there are conflicting definitions with the same name, unsatisfied resource dependencies, etc. These errors will still be raised at code location load time. The new `Definitions.validate_loadable` static method also allows performing the validation steps that used to occur in constructor.
- `AssetsDefinitions` object provided to a `Definitions` object will now be deduped by reference equality. That is, the following will now work:

  ```python
  from dagster import asset, Definitions

  @asset
  def my_asset(): ...

  defs = Definitions(assets=[my_asset, my_asset]) # Deduped into just one AssetsDefinition.
  ```

- [dagster-embedded-elt] Adds translator options for dlt integration to override auto materialize policy, group name, owners, and tags
- [dagster-sdf] Introducing the dagster-sdf integration for data modeling and transformations powered by sdf.
- [dagster-dbt] Added a new `with_insights()` method which can be used to more easily attach Dagster+ Insights metrics to dbt executions: `dbt.cli(...).stream().with_insights()`

### Bugfixes

- Dagster now raises an error when an op yields an output corresponding to an unselected asset.
- Fixed a bug that caused downstream ops within a graph-backed asset to be skipped when they were downstream of assets within the graph-backed assets that aren’t part of the selection for the current run.
- Fixed a bug where code references did not work properly for self-hosted GitLab instances. Thanks [@cooperellidge](https://github.com/cooperellidge)!
- [ui] When engine events with errors appear in run logs, their metadata entries are now rendered correctly.
- [ui] The asset catalog greeting now uses your first name from your identity provider.
- [ui] The create alert modal now links to the alerting documentation, and links to the documentation have been updated.
- [ui] Fixed an issue introduced in the 1.7.13 release where some asset jobs were only displaying their ops in the Dagster UI instead of their assets.
- Fixed an issue where terminating a run while it was using the Snowflake python connector would sometimes move it into a FAILURE state instead of a CANCELED state.
- Fixed an issue where backfills would sometimes move into a FAILURE state instead of a CANCELED state when the backfill was canceled.

### Breaking Changes

- The experimental and deprecated `build_asset_with_blocking_check` has been removed. Use the `blocking` argument on `@asset_check` instead.
- Users with `mypy` and `pydantic` 1 may now experience a “metaclass conflict” error when using `Config`. Previously this would occur when using pydantic 2.
- `AutoMaterializeSensorDefinition` has been renamed `AutomationConditionSensorDefinition`.
- The deprecated methods of the `ComputeLogManager` have been removed. Custom `ComputeLogManager` implementations must also implement the `CapturedLogManager` interface. This will not affect any of the core implementations available in the core `dagster` package or the library packages.
- By default, an `AutomationConditionSensorDefinition` with the name `“default_automation_condition_sensor”` will be constructed for each code location, and will handle evaluating and launching runs for all `AutomationConditions` and `AutoMaterializePolicies` within that code location. You can restore the previous behavior by setting:
  ```yaml
  auto_materialize:
    use_sensors: False
  ```
  in your dagster.yaml file.
- [dagster-dbt] Support for `dbt-core==1.6.*` has been removed because the version is now end-of-life.
- [dagster-dbt] The following deprecated APIs have been removed:
  - `KeyPrefixDagsterDbtTranslator` has been removed. To modify the asset keys for a set of dbt assets, implement`DagsterDbtTranslator.get_asset_key()` instead.
  - Support for setting freshness policies through dbt metadata on field `+meta.dagster_freshness_policy` has been removed. Use `+meta.dagster.freshness_policy` instead.
  - Support for setting auto-materialize policies through dbt metadata on field `+meta.dagster_auto_materialize_policy` has been removed. Use `+meta.dagster.auto_materialize_policy` instead.
  - Support for `load_assets_from_dbt_project`, `load_assets_from_dbt_manifest`, and `dbt_cli_resource` has been removed. Use `@dbt_assets`, `DbtCliResource`, and `DbtProject` instead to define how to load dbt assets from a dbt project and to execute them.
  - Support for rebuilt ops like `dbt_run_op`, `dbt_compile_op`, etc has been removed. Use `@op` and `DbtCliResource` directly to execute dbt commands in an op.
- Properties on `AssetExecutionContext` , `OpExecutionContext` , and `ScheduleExecutionContext` that include `datetime`s now return standard Python `datetime` objects instead of [Pendulum datetimes](https://pendulum.eustace.io/docs/). The types in the public API for these properties have always been `datetime` and this change should not be breaking in the majority of cases, but Pendulum datetimes include some additional methods that are not present on standard Python `datetime`s, and any code that was using those methods will need to be updated to either no longer use those methods or transform the `datetime` into a Pendulum datetime. See the 1.8 migration guide for more information and examples.
- `MemoizableIOManager`, `VersionStrategy`, `SourceHashVersionStrategy`, `OpVersionContext`, `ResourceVersionContext`, and `MEMOIZED_RUN_TAG`, which have been deprecated and experimental since pre-1.0, have been removed.

### Deprecations

- The Run Status column of the Backfills page has been removed. This column was only populated for backfills of jobs. To see the run statuses for job backfills, click on the backfill ID to get to the Backfill Details page.
- The experimental `external_assets_from_specs` API has been deprecated. Instead, you can directly pass `AssetSpec` objects to the `assets` argument of the `Definitions` constructor.
- `AutoMaterializePolicy` has been marked as deprecated in favor of `AutomationCondition` , which provides a significantly more flexible and customizable interface for expressing when an asset should be executed. More details on how to migrate your `AutoMaterializePolicies` can be found in the Migration Guide.
- `SourceAsset` has been deprecated. See the major changes section and migration guide for more details.
- The `asset_partition_key_for_output`, `asset_partition_keys_for_output`, and `asset_partition_key_range_for_output`, and `asset_partitions_time_window_for_output` methods on `OpExecutionContext` have been deprecated. Instead, use the corresponding property: `partition_key`, `partition_keys`, `partition_key_range`, or `partition_time_window`.
- The `partitions_def` parameter on `define_asset_job` is now deprecated. The `partitions_def` for an asset job is determined from the `partitions_def` attributes on the assets it targets, so this parameter is redundant.
- [dagster-shell] `create_shell_command_op` and `create_shell_script_op` have been marked as deprecated in favor of `PipesSubprocessClient` (see details in [Dagster Pipes subprocess reference](https://docs.dagster.io/concepts/dagster-pipes/subprocess/reference))
- [dagster-airbyte] `load_assets_from_airbyte_project` is now deprecated, because the Octavia CLI that it relies on is an experimental feature that is no longer supported. Use `build_airbyte_assets` or `load_assets_from_airbyte_project` instead.

### Documentation

- The Asset Checks concept overview page now includes a table with all the built-in asset checks.
- The Asset Metadata page concept page now includes a table with all the standard “dagster/” metadata keys.
- Fixed a typo in the documentation for `MonthlyPartitionsDefinition`. Thanks [@zero_stroke](https://github.com/zero_stroke)!
- Added a new page about Declarative Automation and a guide about customizing automation conditions
- Fixed a link in the Limiting concurrency guide.

### Dagster Plus

- In Dagster+, selections into the catalog can now be saved and shared across an organization as catalog views. Catalog views have a name and description, and can be applied to scope the catalog, asset health, and global asset lineage pages against the view’s saved selection.
- In Dagster+ run alerts, if you are running Dagster 1.8 or greater in your user code, you will now receive exception-level information in the alert body.

## 1.7.16 (core) / 0.23.16 (libraries)

### Experimental

- [pipes] PipesGlueClient, an AWS Glue pipes client has been added to `dagster_aws`.

## 1.7.15 (core) / 0.23.15 (libraries)

### New

- [dagster-celery-k8s] Added a `per_step_k8s_config` configuration option to the `celery_k8s_job_executor` , allowing the k8s configuration of individual steps to be configured at run launch time. Thanks [@alekseik1](https://github.com/alekseik1)!
- [dagster-dbt] Deprecated the `log_column_level_metadata` macro in favor of the new `with_column_metadata` API.
- [dagster-airbyte] Deprecated `load_assets_from_airbyte_project` as the Octavia CLI has been deprecated.

### Bugfixes

- [ui] Fix global search to find matches on very long strings.
- Fixed an issue introduced in the 1.7.14 release where multi-asset sensors would sometimes raise an error about fetching too many event records.
- Fixes an issue introduced in 1.7.13 where type-checkers interpretted the return type of `RunRequest(...)` as `None`
- [dagster-aws] Fixed an issue where the `EcsRunLauncher` would sometimes fail to launch runs when the `include_sidecars` option was set to `True`.
- [dagster-dbt] Fixed an issue where errors would not propagate through deferred metadata fetches.

### Dagster Plus

- On June 20, 2024, AWS changed the AWS CloudMap CreateService API to allow resource-level permissions. The Dagster+ ECS Agent uses this API to launch code locations. We’ve updated the Dagster+ ECS Agent CloudFormation template to accommodate this change for new users. Existing users have until October 14, 2024 to add the new permissions and should have already received similar communication directly from AWS.
- Fixed a bug with BigQuery cost tracking in Dagster+ insights, where some runs would fail if there were null values for either `total_byte_billed` or `total_slot_ms` in the BigQuery `INFORMATION_SCHEMA.JOBS` table.
- Fixed an issue where code locations that failed to load with extremely large error messages or stack traces would sometimes cause errors with agent heartbeats until the code location was redeployed.

## 1.7.14 (core) / 0.23.14 (libraries)

### New

- [blueprints] When specifying an asset key in `ShellCommandBlueprint`, you can now use slashes as a delimiter to generate an `AssetKey` with multiple path components.
- [community-controbution][mlflow] The mlflow resource now has a `mlflow_run_id` attribute (Thanks Joe Percivall!)
- [community-contribution][mlflow] The mlflow resource will now retry when it fails to fetch the mlflow run ID (Thanks Joe Percivall!)

### Bugfixes

- Fixed an issue introduced in the 1.7.13 release where Dagster would fail to load certain definitions when using Python 3.12.4.
- Fixed an issue where in-progress steps would continue running after an unexpected exception caused a run to fail.
- [dagster-dbt] Fixed an issue where column lineage was unable to be built in self-referential incremental models.
- Fixed an issue where `dagster dev` was logging unexpectedly without the `grpcio<1.65.0` pin.
- Fixed an issue where a `ContextVar was created in a different context` error was raised when executing an async asset.
- [community-contribution] `multi_asset` type-checker fix from @aksestok, thanks!
- [community-contribution][ui] Fix to use relative links for manifest/favicon files, thanks @aebrahim!

### Documentation

- [community-contribution] Fixed helm repo CLI command typo, thanks @fxd24!

### Dagster Plus

- [ui] The deployment settings yaml editor is now on a page with its own URL, instead of within a dialog.

## 1.7.13 (core) / 0.23.13 (libraries)

### New

- The `InputContext` passed to an `IOManager` ’s `load_input` function when invoking the `output_value` or `output_for_node` methods on `JobExecutionResult` now has the name `"dummy_input_name"` instead of `None`.
- [dagster-ui] Asset materializations can now be reported from the dropdown menu in the asset list view.
- [dagster-dbt] `DbtProject` is adopted and no longer experimental. Using `DbtProject` helps achieve a setup where the dbt manifest file and dbt dependencies are available and up-to-date, during development and in production. Check out the API docs for more: [https://docs.dagster.io/\_apidocs/libraries/dagster-dbt#dagster_dbt.DbtProject](https://docs.dagster.io/_apidocs/libraries/dagster-dbt#dagster_dbt.DbtProject).
- [dagster-dbt] The `—use-dbt-project` flag was introduced for the cli command `dagster-dbt project scaffold`. Creating a Dagster project wrapping a dbt project using that flag will include a `DbtProject` .
- [dagster-ui] The Dagster UI now loads events in batches of 1000 in the run log viewer, instead of batches of 10000. This value can be adjusted by setting the `DAGSTER_UI_EVENT_LOAD_CHUNK_SIZE` environment variable on the Dagster webserver.
- Asset backfills will now retry if there is an unexpected exception raised in the middle of the backfill. Previously, they would only retry if there was a problem connecting to the code server while launching runs in the backfill.
- Added the ability to monitor jobs which have failed to start in time with the `RunFailureReason.START_TIMEOUT` run monitoring failure reason. Thanks @jobicarter!
- [experimental] Introduced the ability to attach code references to your assets, which allow you to view source code for an asset in your editor or in git source control. For more information, see the code references docs: [https://docs.dagster.io/guides/dagster/code-references](https://docs.dagster.io/guides/dagster/code-references).
- [ui] Performance improvements to loading the asset overview tab.
- [ui] Performance improvements for rendering gantt charts with 1000’s of ops/steps.
- [dagster-celery] Introduced a new Dagster Celery runner, a more lightweight way to run Dagster jobs without an executor. Thanks, @egordm!

### Bugfixes

- Fixed a bug that caused tags added to `ObserveResult` objects to not be stored with the produced `AssetObservation` event.
- Fixed a bug which could cause `metadata` defined on `SourceAssets` to be unavailable when accessed in an IOManager.
- For subselections of graph-backed multi-assets, there are some situations where we used to unnecessarily execute some of the non-selected assets. Now, we no longer execute them in those situations. There are also some situations where we would skip execution of some ops that might be needed. More information on the particulars is available [here](https://github.com/dagster-io/dagster/pull/22733).
- Fixed the `@graph_asset` decorator overload missing an `owners` argument, thanks @askvinni!
- Fixed behavior of passing custom image config to the K8sRunLauncher, thanks @[marchinho11](https://github.com/marchinho11)!
- [dagster-dbt] Fixed an issue with emitting column lineage when using BigQuery.
- [dagster-k8s] Added additional retries to `execute_k8s_job` when there was a transient failure while loading logs from the launched job. Thanks [@piotrmarczydlo](https://github.com/piotrmarczydlo)!
- [dagster-fivetran] Fixed an issue where the Fivetran connector resource would sometimes hang if there was a networking issue while connecting to the Fivetran API.
- [dagster-aws] Fixed an issue where the EMR step launcher would sometimes fail due to multiple versions of the `dateutil` package being installed in the default EMR python evnrionment.
- [ui] The “Create date” column in the runs table now correctly shows the time at which a run was created instead of the time when it started to execute.
- [ui] Fixed dark mode colors in run partitions graphs.
- [auto-materialize] Fixed an issue which could cause errors in the `AutoMaterializeRule.skip_on_parent_missing` rule when a parent asset had its `PartitionsDefinition` changed.
- [declarative-automation] Fixed an issue which could cause errors when viewing the evaluation history of assets with `AutomationConditions`.
- [declarative-automation] Previously, `AutomationCondition.newly_updated()` would trigger on any `ASSET_OBSERVATION` event. Now, it only triggers when the data version on that event changes.

### Breaking Changes

- [dagster-dbt] The cli command `dagster-dbt project prepare-for-deployment` has been replaced by `dagster-dbt project prepare-and-package`.
- [dagster-dbt] During development,`DbtProject` no longer prepares the dbt manifest file and dbt dependencies in its constructor during initialization. This process has been moved to `prepare_if_dev()`, that can be called on the `DbtProject` instance after initialization. Check out the API docs for more: [https://docs.dagster.io/\_apidocs/libraries/dagster-dbt#dagster_dbt.DbtProject.prepare_if_dev](https://docs.dagster.io/_apidocs/libraries/dagster-dbt#dagster_dbt.DbtProject.prepare_if_devhttps://docs.dagster.io/_apidocs/libraries/dagster-dbt#dagster_dbt.DbtProject.prepare_if_dev).

### Deprecations

- Passing `GraphDefinition` as the `job` argument to schedules and sensors is deprecated. Derive a job from the `GraphDefinition` using `graph_def.to_job()` and pass this instead.

### Documentation

- Added some additional copy, headings, and other formatting to the [dbt quickstart](https://docs.dagster.io/integrations/dbt/quickstart).
- Added information about asset checks to the [Testing assets guide](https://docs.dagster.io/guides/dagster/testing-assets).
- Updated `dagster-plus CLI` in the sidenav to correctly be `dagster-cloud CLI`.
- Thanks to Tim Nordenfur and Dimitar Vanguelov for fixing a few typos!
- Introduced guides to migrate Airflow pipelines to Dagster that leverage the TaskFlow API or are containerized and executed with an operator like the KubernetesPodOperator.
- Fixed instructions on setting secrets in Kubernetes Dagster deployments, thanks @abhinavDhulipala!

### Dagster Plus

- A history of code location deploys can now be viewed on the Code Locations tab under the Deployment view. Previously deployed versions can now be restored from history.
- [ui] Various improvements have been made to the asset health dashboard, which is now no longer experimental.
- [ui] Fixed issues in per-event asset insights where bar charts incorrectly displayed events in reverse order, and with UTC timestamps.
- Fixed a recent regression where creating an alert that notifies asset owners that are teams raises an error.

## 1.7.12 (core)/ 0.23.12 (libraries)

### Bugfixes

- [ui] fixes behavior issues with jobs and asset pages introduced in 1.7.11

## 1.7.11 (core)/ 0.23.11 (libraries)

### New

- [ui] Improved performance for loading assets that are part of big asset graphs.
- [ui] Improved performance for loading job backfills that have thousands of partitions
- [ui] The code location page can now be filtered by status
- [agent] K8s and ECS agent main loop writes a sentinel file that can be used for liveness checks.
- [agent][experimental] ECS CloudFormation template with private IP addresses using NAT Gateways, security groups, IAM role separation, tighter permissions requirements, and improved documentation.
- Ephemeral asset jobs are now supported in run status sensors (thanks [@the4thamigo-uk](https://github.com/the4thamigo-uk))!

### Bugfixes

- In `AssetsDefinition` construction, enforce single key per output name
- Fixed a bug where freshness checks on assets with both observations and materializations would incorrectly miss a materialization if there’s no observation with `dagster/last_updated_timestamp`.
- Fixed a bug with anomaly detection freshness checks where “not enough records” result would cause the sensor to crash loop.
- Fixed a bug that could cause errors in the Asset Daemon if an asset using `AutoMaterializeRule.skip_on_not_all_parents_updated_since_cron()` rule gained a new dependency with a different PartitionsDefinition.
- [ui] Fixed an issue that caused the backfill page not to be scrollable.
- [ui] Fixed an issue where filtering by partition on the Runs page wouldn’t work if fetching all of your partitions timed out.
- [dagster-dlt] Fixed bug with dlt integration in which partitioned assets would change the file name when using the filesystem destination.
- [ui] Fixed an issue where an erroring code location would cause multiple toast popups.
- Allow a string to be provided for `source_key_prefix` arg of `load_assets_from_modules`. (thanks [@drjlin](https://github.com/drjlin))!
- Added a missing debug level log message when loading partitions with polars (thanks [Daniel Gafni](https://github.com/danielgafni))!
- Set postgres timeout via statement, which improves storage-layer compatibility with Amazon RDS (thanks [@james lewis](https://github.com/jameslewisfaculty))!
- In DBT integration, quote the table identifiers to handle cases where table names require quotes due to special characters. (thanks [@alex launi](https://github.com/lamalex))!
- remove deprecated param usage in dagster-wandb integration (thanks [@chris histe](https://github.com/chrishiste))!
- Add missing QUEUED state to DatabricksRunLifeCycleState (thanks [@gabor ratky](https://github.com/gaborratky-db))!
- Fixed a bug with dbt-cloud integration subsetting implementation (thanks [@ivan tsarev](https://github.com/mudravrik))!

### Breaking Changes

- [dagster-airflow] `load_assets_from_airflow_dag` no longer allows multiple tasks to materialize the same asset.

### Documentation

- Added type-hinting to backfills example
- Added syntax highlighting to some examples (thanks [@Niko](https://github.com/nikomancy))!
- Fixed broken link (thanks [@federico caselli](https://github.com/caselit))!

### Dagster Plus

- The `dagster-cloud ci init` CLI will now use the `--deployment` argument as the base deployment when creating a branch deployment. This base deployment will be used for Change Tracking.
- The BigQuery dbt insights wrapper `dbt_with_bigquery_insights` now respects CLI arguments for profile configuration and also selects location / dataset from the profile when available.
- [experimental feature] Fixes a recent regression where the UI errored upon attempting to create an insights metric alert.

## 1.7.10 (core)/ 0.23.10 (libraries)

### New

- Performance improvements when rendering the asset graph while runs are in progress.
- A new API `build_freshness_checks_for_dbt_assets` which allows users to parameterize freshness checks entirely within dbt. Check out the API docs for more: https://docs.dagster.io/_apidocs/libraries/dagster-dbt#dbt-dagster-dbt.
- Asset search results now display compute and storage kind icons.
- Asset jobs where the underlying assets have multiple backfill policies will no longer fail at definition time. Instead, the backfill policy for the job will use the minimum `max_partitions_per_run` from the job’s constituent assets.
- [dagstermill] `asset_tags` can now be specified when building dagstermill assets
- [dagster-embedded-elt] Custom asset tags can be applied to Sling assets via the `DagsterSlingTranslator`
- [dagster-embedded-elt] dlt assets now automatically have `dagster/storage_kind` tags attached

### Bugfixes

- `tags` passed to `outs` in `graph_multi_asset` now get correctly propagated to the resulting assets.
- [ui] Fixed an issue in the where when multiple runs were started at the same time to materialize the same asset, the most recent one was not always shown as in progress in the asset graph in the Dagster UI.
- The “newly updated” auto-materialize rule will now respond to either new observations or materializations for observable assets.
- `build_metadata_bounds_checks` now no longer errors when targeting metadata keys that have special characters.

### Documentation

- The [Schedule concept docs](https://docs.dagster.io/concepts/automation/schedules) got a revamp! Specifically, we:
  - Updated the Schedule concept page to be a “jumping off” point for all-things scheduling, including a high-level look at how schedules work, their benefits, and what you need to know before diving in
  - Added some basic how-to guides for [automating assets](https://docs.dagster.io/concepts/automation/schedules/automating-assets-schedules-jobs) and [ops](https://docs.dagster.io/concepts/automation/schedules/automating-ops-schedules-jobs) using schedules
  - Added a [reference of schedule-focused examples](https://docs.dagster.io/concepts/automation/schedules/examples)
  - Added dedicated guides for common schedule uses, including creating p[artitioned schedules](https://docs.dagster.io/concepts/automation/schedules/partitioned-schedules), [customizing executing timezones](https://docs.dagster.io/concepts/automation/schedules/customizing-executing-timezones), [testing](https://docs.dagster.io/concepts/automation/schedules/testing), and [troubleshooting](https://docs.dagster.io/concepts/automation/schedules/troubleshooting)

### Dagster Plus

- [experimental] The backfill daemon can now store logs and display them in the UI for increased visibility into the daemon’s behavior. Please contact Dagster Labs if you are interested in piloting this experimental feature.
- Added a `--read-only` flag to the `dagster-cloud ci branch-deployment` CLI command, which returns the current branch deployment name for the current code repository branch without update the status of the branch deployment.

## 1.7.9 (core) / 0.23.9 (libraries)

### New

- Dagster will now display a “storage kind” tag on assets in the UI, similar to the existing compute kind. To set storage kind for an asset, set its `dagster/storage_kind` tag.
- You can now set retry policy on dbt assets, to enable coarse-grained retries with delay and jitter. For fine-grained partial retries, we still recommend invoking `dbt retry` within a try/except block to avoid unnecessary, duplicate work.
- `AssetExecutionContext` now exposes a `has_partition_key_range` property.
- The `owners`, `metadata`, `tags`, and `deps` properties on `AssetSpec` are no longer `Optional`. The `AssetSpec` constructor still accepts `None` values, which are coerced to empty collections of the relevant type.
- The `docker_executor` and `k8s_job_executor` now consider at most 1000 events at a time when loading events from the current run to determine which steps should be launched. This value can be tuned by setting the `DAGSTER_EXECUTOR_POP_EVENTS_LIMIT` environment variable in the run process.
- Added a `dagster/retry_on_asset_or_op_failure` tag that can be added to jobs to override run retry behavior for runs of specific jobs. See [the docs](https://docs.dagster.io/deployment/run-retries#combining-op-and-run-retries) for more information.
- Improved the sensor produced by `build_sensor_for_freshness_checks` to describe when/why it skips evaluating freshness checks.
- A new “Runs” tab on the backfill details page allows you to see list and timeline views of the runs launched by the backfill.
- [dagster-dbt] dbt will now attach relation identifier metadata to asset materializations to indicate where the built model is materialized to.
- [dagster-graphql] The GraphQL Python client will now include the HTTP error code in the exception when a query fails. Thanks [@yuvalgimmunai](https://github.com/yuvalgimmunai)!

### Bugfixes

- Fixed sensor logging behavior with the `@multi_asset_sensor`.
- `ScheduleDefinition` now properly supports being passed a `RunConfig` object.
- When an asset function returns a `MaterializeResult`, but the function has no type annotation, previously, the IO manager would still be invoked with a `None` value. Now, the IO manager is not invoked.
- The `AssetSpec` constructor now raises an error if an invalid owner string is passed to it.
- When using the `graph_multi_asset` decorator, the `code_version` property on `AssetOut`s passed in used to be ignored. Now, they no longer are.
- [dagster-deltalake] Fixed GcsConfig import error and type error for partitioned assets (Thanks [@thmswt](https://github.com/thmswt))
- The asset graph and asset catalog now show the materialization status of External assets (when manually reported) rather than showing “Never observed”

### Documentation

- The External Assets REST APIs now have their own [reference page](https://docs.dagster.io/apidocs/external-assets-rest)
- Added details, updated copy, and improved formatting to External Assets REST APIs

### Dagster Plus

- The ability to set a custom base deployment when creating a branch deployment has been enabled for all organizations.
- When a code location fails to deploy, the Kubernetes agent now includes additional any warning messages from the underlying replicaset in the failure message to aid with troubleshooting.
- Serverless deployments now support using a requirements.txt with [hashes](https://pip.pypa.io/en/stable/topics/secure-installs/#secure-installs).
- Fixed an issue where the `dagster-cloud job launch` command did not support specifying asset keys with prefixes in the `--asset-key` argument.
- [catalog UI] Catalog search now allows filtering by type, i.e. `group:`, `code location:`, `tag:`, `owner:`.
- New dagster+ accounts will now start with two default alert policies; one to alert if the default free credit budget for your plan is exceeded, and one to alert if a single run goes over 24 hours. These alerts will be sent as emails to the email with which the account was initially created.

## 1.7.8 (core) / 0.23.8 (libraries)

### New

- Backfills created via GQL can have a custom title and description.
- `Definitions` now has a `get_all_asset_specs` method, which allows iterating over properties of the defined assets
- [ui] In filter dropdowns, it’s now possible to submit before all the suggestions have been loaded (thanks [@bmalehorn](https://github.com/bmalehorn)!)
- [ui] Performance improvements when loading the Dagster UI for asset graphs with thousands of partition keys.
- [dagster-dbt] Dbt asset checks now emit execution duration and the number of failing rows as metadata
- [dagster-embedded-elt] Added support for partitioning in dlt assets (thanks [@edsoncezar16](https://github.com/edsoncezar16)!)
- [dagster-embedded-elt] Added ability to set custom metadata on dlt assets (thanks [@edsoncezar16](https://github.com/edsoncezar16)!)
- [dagster-graphql] Added a `terminate_runs` method to the Python GraphQL Client. (thanks [@baumann-t](https://github.com/baumann-t)!)
- [dagster-polars] dagster-polars IO managers now emit dagster/row_count metadata (thanks [@danielgafni](https://github.com/danielgafni)!)
- [dagster-dbt] `DbtCliInvocation` now has a `.get_error()` method that can be useful when using `dbt.cli(..., raise_on_error=False)`.

### Bugfixes

- Fix a bug with legacy `DynamicPartitionsDefinition` (using `partitions_fn`) that caused a crash during job backfills.
- [ui] On the asset graph, filtering to one or more code locations via the Filter dropdown now works as expected.
- [ui] On the asset overview page, viewing an asset with no definition in a loaded code location no longer renders a clipped empty state.

### Experimental

- The new `build_metadata_bounds_checks` API creates asset checks which verify that numeric metadata values on asset materializations fall within min or max values. See the [documentation](https://docs.dagster.io/_apidocs/asset-checks#dagster.build_metadata_bounds_checks) for more information.

### Documentation

- Added details and links to the [Schedules and Sensors API documentation](https://docs.dagster.io/_apidocs/schedules-sensors)
- Removed leftover mention of Dagster Cloud from the [Dagster+ Hybrid architecture documentation](https://docs.dagster.io/dagster-plus/deployment/hybrid)

### Dagster Plus

- Fixed an incompatibility between `build_sensor_for_freshness_checks` and Dagster Plus. This API should now work when used with Dagster Plus.
- [ui] Billing / usage charts no longer appear black-on-black in Dagster’s dark mode.
- [ui] The asset catalog is now available for teams plans.
- [ui] Fixed a bug where the alert policy editor would misinterpret the threshold on a long-running job alert.
- [kubernetes] Added a `dagsterCloudAgent.additionalPodSpecConfig` to the Kubernetes agent Helm chart allowing arbitrary pod configuration to be applied to the agent pod.
- [ECS] Fixed an issue where the ECS agent would sometimes raise a “Too many concurrent attempts to create a new revision of the specified family” exception when using agent replicas.

## 1.7.7 (core) / 0.23.7 (libraries)

### New

- [ui] Command clicking on nodes in the asset lineage tab will now open them in a separate tab. Same with external asset links in the asset graph.
- Added support for setting a custom job namespace in user code deployments. (thanks [@tmatthews0020](https://github.com/tmatthews0020)!)
- Removed warnings due to use of `datetime.utcfromtimestamp` (thanks @[dbrtly](https://github.com/dbrtly)!)
- Custom smtp user can now be used for e-mail alerts (thanks @[edsoncezar16](https://github.com/edsoncezar16)!)
- [dagster-dbt] Added support for `dbt-core==1.8.*`.
- [dagster-embedded-elt] Failed dlt pipelines are now accurately reflected on the asset materialization (thanks @[edsoncezar16](https://github.com/edsoncezar16)!)

### Bugfixes

- Fixed spurious errors in logs due to module shadowing.
- Fixed an issue in the Backfill Daemon where if the assets to be materialized had different `BackfillPolicy`s, each asset would get materialized in its own run, rather than grouping assets together into single run.
- Fixed an issue that could cause the Asset Daemon to lose information in its cursor about an asset if that asset’s code location was temporarily unavailable.
- [dagster-dbt] Mitigated issues with cli length limits by only listing specific dbt tests as needed when the tests aren’t included via indirect selection, rather than listing all tests.

### Documentation

- Markdoc tags can now be used in place of MDX components (thanks @[nikomancy](https://github.com/nikomancy))

## 1.7.6 (core) / 0.23.6 (libraries)

### New

- The backfill daemon now has additional logging to document the progression through each tick and why assets are and are not materialized during each evaluation of a backfill.
- Made performance improvements in both calculating and storing data version for assets, especially for assets with a large fan-in.
- Standardized table row count metadata output by various integrations to `dagster/row_count` .
- [dagster-aws][community-contribution] Additional parameters can now be passed to the following resources: `CloudwatchLogsHandler`, `ECRPublicClient`, `SecretsManagerResource`, `SSMResource` thanks `@jacob-white-simplisafe` !
- Added additional frontend telemetry. See https://docs.dagster.io/about/telemetry for more information.

### Bugfixes

- Fixed issue that could cause runs to fail if they targeted any assets which had a metadata value of type `TableMetadataValue`, `TableSchemaMetadataValue`, or `TableColumnLineageMetadataValue` defined.
- Fixed an issue which could cause evaluations produced via the Auto-materialize system to not render the “skip”-type rules.
- Backfills of asset jobs now correctly use the `BackfillPolicy` of the underlying assets in the job.
- [dagster-databricks][community-contribution] `databricks-sdk` version bumped to `0.17.0`, thanks `@lamalex` !
- [helm][community-contribution] resolved incorrect comments about `dagster code-server start` , thanks `@SanjaySiddharth` !

### Documentation

- Added section headings to Pipes API references, along with explanatory copy and links to relevant pages
- Added a guide for subletting asset checks
- Add more detailed steps to transition from serverless to hybrid
- [community-contribution] asset selection syntax corrected, thanks `@JonathanLai2004`!

### Dagster Plus

- Fixed an issue where Dagster Cloud agents would wait longer than necessary when multiple code locations were timing out during a deployment.

## 1.7.5 (core) / 0.23.5 (libraries)

### New

- The Asset > Checks tab now allows you to view plots of numeric metadata emitted by your checks.
- The Asset > Events tab now supports infinite-scrolling, making it possible to view all historical materialization and observation events.
- When constructing a `MaterializeResult`, `ObserveResult`, or `Output`, you can now include tags that will be attached to the corresponding `AssetMaterialization` or `AssetObservation` event. These tags will be rendered on these events in the UI.

### Bugfixes

- Fixed an issue where backfills would sometimes fail if a partition definition was changed in the middle of the backfill.
- Fixed an issue where if the code server became unavailable during the first tick of a backfill, the backfill would stall and be unable to submit runs once the code server became available.
- Fixed an issue where the status of an external asset would not get updated correctly.
- Fixed an issue where run status sensors would sometimes fall behind in deployments with large numbers of runs.
- The descriptions and metadata on the experimental `build_last_update_freshness_checks` and `build_time_partition_freshness_checks` APIs have been updated to be clearer.
- The headers of tables no longer become misaligned when a scrollbar is present in some scenarios.
- The sensor type, instigation type, and backfill status filters on their respective pages are now saved to the URL, so sharing the view or reloading the page preserve your filters.
- Typing a `%` into the asset graph’s query selector no longer crashes the UI.
- “Materializing” states on the asset graph animate properly in both light and dark themes.
- Thanks to [@lautaro79](https://github.com/lautaro79) for fixing a helm chart issue.

### Breaking Changes

- Subclasses of `MetadataValue` have been changed from `NamedTuple`s to Pydantic models. `NamedTuple` functionality on these classes was not part of Dagster’s stable public API, but usages relying on their tuple-ness may break. For example: calling `json.dumps` on collections that include them.

### Deprecations

- [dagster-dbt] Support for `dbt-core==1.5.*` has been removed, as it has reached [end of life in April 2024](https://docs.getdbt.com/docs/dbt-versions/core).

### Dagster Plus

- Fixed an issue in the `dagster-cloud` CLI where the `--deployment` argument was ignored when the `DAGSTER_CLOUD_URL` environment variable was set.
- Fixed an issue where `dagster-cloud-cli` package wouldn’t work unless the `dagster-cloud` package was installed as well.
- A new “budget alerts” feature has launched for users on self-serve plans. This feature will alert you when you hit your credit limit.
- The experimental asset health overview now allows you to group assets by compute kind, tag, and tag value.
- The concurrency and locations pages in settings correctly show Dagster Plus-specific options when experimental navigation is enabled.

## 1.7.4 (core) / 0.23.4 (libraries)

### New

- `TimeWindowPartitionMapping` now supports the `start_offset` and `end_offset` parameters even when the upstream `PartitionsDefinition` is different than the downstream `PartitionsDefinition`. The offset is expressed in units of downstream partitions, so `TimeWindowPartitionMapping(start_offset=-1)` between an hourly upstream and a daily downstream would map each downstream partition to 48 upstream partitions – those for the same and preceding day.

### Bugfixes

- Fixed an issue where certain exceptions in the Dagster daemon would immediately retry instead of waiting for a fixed interval before retrying.
- Fixed a bug with asset checks in complex asset graphs that include cycles in the underlying nodes.
- Fixed an issue that would cause unnecessary failures on FIPS-enabled systems due to the use of md5 hashes in non-security-related contexts (thanks [@jlloyd-widen](https://github.com/jlloyd-widen)!)
- Removed `path` metadata from `UPathIOManager` inputs. This eliminates the creation of `ASSET_OBSERVATION` events for every input on every step for the default I/O manager.
- Added support for defining `owners` on `@graph_asset`.
- Fixed an issue where having multiple partitions definitions in a location with the same start date but differing end dates could lead to “`DagsterInvalidSubsetError` when trying to launch runs.

### Documentation

- Fixed a few issues with broken pages as a result of the Dagster+ rename.
- Renamed a few instances of Dagster Cloud to Dagster+.
- Added a note about external asset + alert incompatibility to the Dagster+ alerting docs.
- Fixed references to outdated apis in freshness checks docs.

### Dagster Plus

- When creating a Branch Deployment via GraphQL or the `dagster-cloud branch-deployment` CLI, you can now specify the base deployment. The base deployment will be used for comparing assets for Change Tracking. For example, to set the base deployment to a deployment named `staging`: `dagster-cloud branch-deployment create-or-update --base-deployment-name staging ...`. Note that once a Branch Deployment is created, the base deployment cannot be changed.
- Fixed an issue where agents serving many branch deployments simultaneously would sometimes raise a `413: Request Entity Too Large` error when uploading a heartbeat to the Dagster Plus servers.

## 1.7.3 (core) / 0.23.3 (libraries)

### New

- `@graph_asset` now accepts a `tags` argument
- [ui] For users whose light/dark mode theme setting is set to match their system setting, the theme will update automatically when the system changes modes (e.g. based on time of day), with no page reload required.
- [ui] We have introduced the typefaces Geist and Geist Mono as our new default fonts throughout the Dagster app, with the goal of improving legibility, consistency, and maintainability.
- [ui] [experimental] We have begun experimenting with a [new navigation structure](https://github.com/dagster-io/dagster/discussions/21370) for the Dagster UI. The change can be enabled via User Settings.
- [ui] [experimental] Made performance improvements to the Concurrency settings page.
- [dagster-azure] [community-contribution] ADLS2 IOManager supports custom timeout. Thanks @tomas-gajarsky!
- [dagster-fivetran] [community-contribution] It’s now possible to specify destination ids in `load_asset_defs_from_fivetran_instance`. Thanks @lamalex!

### Bugfixes

- Fixed an issue where pressing the “Reset sensor status” button in the UI would also reset the sensor’s cursor.
- Fixed a bug that caused input loading time not to be included in the reported step duration.
- Pydantic warnings are no longer raised when importing Dagster with Pydantic 2.0+.
- Fixed an issue which would cause incorrect behavior when auto-materializing partitioned assets based on updates to a parent asset in a different code location.
- Fixed an issue which would cause every tick of the auto-materialize sensor to produce an evaluation for each asset, even if nothing had changed from the previous tick.
- [dagster-dbt] Fixed a bug that could raise `Duplicate check specs` errors with singular tests ingested as asset checks.
- [embedded-elt] resolved an issue where subset of resources were not recognized when using `source.with_resources(...)`
- [ui] Fixed an issue where a sensor that targeted an invalid set of asset keys could cause the asset catalog to fail to load.
- [ui] Fixed an issue in which runs in the Timeline that should have been considered overlapping were not correctly grouped together, leading to visual bugs.
- [ui] On the asset overview page, job tags no longer render poorly when an asset appears in several jobs.
- [ui] On the asset overview page, hovering over the timestamp tags in the metadata table explains where each entry originated.
- [ui] Right clicking the background of the asset graph now consistently shows a context menu, and the lineage view supports vertical as well as horizontal layout.

### Documentation

- Sidebar navigation now appropriately handles command-click and middle-click to open links in a new tab.
- Added a section for asset checks to the [Testing guide](https://docs.dagster.io/concepts/testing#testing-asset-checks).
- Added a guide about [Column-level lineage for assets](https://docs.dagster.io/concepts/metadata-tags/asset-metadata/column-level-lineage).
- Lots of updates to examples to reflect the new opt-in approach to I/O managers.

### Dagster+

- [ui] [experimental] A new Overview > Asset Health page provides visibility into failed and missing materializations, check warnings and check errors.
- [ui] You can now share feedback with the Dagster team directly from the app. Open the Help menu in the top nav, then “Share feedback”. Bugs and feature requests are submitted directly to the Dagster team.
- [ui] When editing a team, the list of team members is now virtualized, allowing for the UI to scale better for very large team sizes.
- [ui] Fixed dark mode for billing components.

## 1.7.2 (core) / 0.23.2 (libraries)

### New

- Performance improvements when loading large asset graphs in the Dagster UI.
- `@asset_check` functions can now be invoked directly for unit testing.
- `dagster-embedded-elt` dlt resource `DagsterDltResource` can now be used from `@op` definitions in addition to assets.
- `UPathIOManager.load_partitions` has been added to assist with helping `UpathIOManager` subclasses deal with serialization formats which support partitioning. Thanks `@danielgafni`!
- [dagster-polars] now supports other data types rather than only string for the partitioning columns. Also `PolarsDeltaIOManager` now supports `MultiPartitionsDefinition` with `DeltaLake` native partitioning. Metadata value `"partition_by": {"dim_1": "col_1", "dim_2": "col_2"}` should be specified to enable this feature. Thanks `@danielgafni`!

### Bugfixes

- [dagster-airbyte] Auto materialization policies passed to `load_assets_from_airbyte_instance` and `load_assets_from_airbyte_project` will now be properly propagated to the created assets.
- Fixed an issue where deleting a run that was intended to materialize a partitioned asset would sometimes leave the status of that asset as “Materializing” in the Dagster UI.
- Fixed an issue with `build_time_partition_freshness_checks` where it would incorrectly intuit that an asset was not fresh in certain cases.
- [dagster-k8s] Fix an error on transient ‘none’ responses for pod waiting reasons. Thanks @**[piotrmarczydlo](https://github.com/piotrmarczydlo)!**
- [dagster-dbt] Failing to build column schema metadata will now result in a warning rather than an error.
- Fixed an issue where incorrect asset keys would cause a backfill to fail loudly.
- Fixed an issue where syncing unmaterialized assets could include source assets.

### Breaking Changes

- [dagster-polars] `PolarsDeltaIOManager` no longer supports loading natively partitioned DeltaLake tables as dictionaries. They should be loaded as a single `pl.DataFrame`/`pl.LazyFrame` instead.

### Documentation

- Renamed `Dagster Cloud` to `Dagster+` all over the docs.
- Added a page about [Change Tracking](https://docs.dagster.io/dagster-plus/managing-deployments/branch-deployments/change-tracking) in Dagster+ branch deployments.
- Added a section about [user-defined metrics](https://docs.dagster.io/concepts/metadata-tags/asset-metadata#asset-owners) to the Dagster+ Insights docs.
- Added a section about [Asset owners](https://docs.dagster.io/concepts/metadata-tags/asset-metadata#asset-owners) to the asset metadata docs.

### Dagster Cloud

- Branch deployments now have Change Tracking. Assets in each branch deployment will be compared to the main deployment. New assets and changes to code version, dependencies, partitions definitions, tags, and metadata will be marked in the UI of the branch deployment.
- Pagerduty alerting is now supported with Pro plans. See the [documentation](https://docs.dagster.io/dagster-cloud/managing-deployments/alerts/pagerduty) for more info.
- Asset metadata is now included in the insights metrics for jobs materializing those assets.
- Per-run Insights are now available on individual assets.
- Previously, the `before_storage_id` / `after_storage_id` values in the `AssetRecordsFilter` class were ignored. This has been fixed.
- Updated the output of `dagster-cloud deployment alert-policies list` to match the format of `sync`.
- Fixed an issue where Dagster Cloud agents with many code locations would sometimes leave code servers running after the agent shut down.

## 1.7.1 (core) / 0.23.1 (libraries)

### New

- [dagster-dbt][experimental] A new cli command `dagster-dbt project prepare-for-deployment` has been added in conjunction with `DbtProject` for managing the behavior of rebuilding the manifest during development and preparing a pre-built one for production.

### Bugfixes

- Fixed an issue with duplicate asset check keys when loading checks from a package.
- A bug with the new `build_last_update_freshness_checks` and `build_time_partition_freshness_checks` has been fixed where multi_asset checks passed in would not be executable.
- [dagster-dbt] Fixed some issues with building column lineage for incremental models, models with implicit column aliases, and models with columns that have multiple dependencies on the same upstream column.

### Breaking Changes

- [dagster-dbt] The experimental `DbtArtifacts` class has been replaced by `DbtProject`.

### Documentation

- Added a dedicated concept page for all things [metadata and tags](https://docs.dagster.io/concepts/metadata-tags)
- Moved asset metadata content to a dedicated concept page: [Asset metadata](https://docs.dagster.io/concepts/metadata-tags/asset-metadata)
- Added section headings to the [Software-defined Assets API reference](https://docs.dagster.io/_apidocs/assets), which groups APIs by asset type or use
- Added a guide about [user settings in the Dagster UI](https://docs.dagster.io/concepts/webserver/ui-user-settings)
- Added `AssetObservation` to the Software-defined Assets API reference
- Renamed Dagster Cloud GitHub workflow files to the new, consolidated `dagster-cloud-deploy.yml`
- Miscellaneous formatting and copy updates
- [community-contribution] [dagster-embedded-elt] Fixed `get_asset_key` API documentation (thanks @aksestok!)
- [community-contribution] Updated Python version in contributing documentation (thanks @piotrmarczydlo!)
- [community-contribution] Typo fix in README (thanks @MiConnell!)

### Dagster Cloud

- Fixed a bug where an incorrect value was being emitted for BigQuery bytes billed in Insights.

## 1.7.0 (core) / 0.23.0 (libraries)

## Major Changes since 1.6.0 (core) / 0.22.0 (libraries)

- Asset definitions can now have tags, via the `tags` argument on `@asset`, `AssetSpec`, and `AssetOut`. [Tags](https://docs.dagster.io/concepts/metadata-tags/tags) are meant to be used for organizing, filtering, and searching for assets.
- The Asset Details page has been revamped to include an “Overview” tab that centralizes the most important information about the asset – such as current status, description, and columns – in a single place.
- Assets can now be assigned owners.
- Asset checks are now considered generally available and will no longer raise experimental warnings when used.
- Asset checks can now be marked `blocking`, which causes downstream assets in the same run to be skipped if the check fails with ERROR-level severity.
- The new `@multi_asset_check` decorator enables defining a single op that executes multiple asset checks.
- The new `build_last_updated_freshness_checks` and `build_time_partition_freshness_checks` APIs allow defining asset checks that error or warn when an asset is overdue for an update. Refer to the [Freshness checks guide](https://docs.dagster.io/concepts/assets/asset-checks/checking-for-data-freshness) for more info.
- The new `build_column_schema_change_checks` API allows defining asset checks that warn when an asset’s columns have changed since its latest materialization.
- In the asset graph UI, the “Upstream data”, “Code version changed”, and “Upstream code version” statuses have been collapsed into a single “Unsynced” status. Clicking on “Unsynced” displays more detailed information.
- I/O managers are now optional. This enhances flexibility for scenarios where they are not necessary. For guidance, see [When to use I/O managers](https://docs.dagster.io/concepts/io-management/io-managers#when-to-use-io-managers).
  - Assets with `None` or `MaterializeResult` return type annotations won't use I/O managers; dependencies for these assets can be set using the `deps` parameter in the `@asset` decorator.
- [dagster-dbt] Dagster’s dbt integration can now be configured to automatically collect [metadata about column schema and column lineage](https://docs.dagster.io/integrations/dbt/reference#emit-column-level-metadata-as-materialization-metadata-).
- [dagster-dbt] dbt tests are now pulled in as Dagster asset checks by default.
- [dagster-dbt] dbt resource tags are now automatically pulled in as Dagster asset tags.
- [dagster-snowflake] [dagster-gcp] The dagster-snowflake and dagster-gcp packages now both expose a `fetch_last_updated_timestamps` API, which makes it straightforward to collect data freshness information in source asset observation functions.

## Changes since 1.6.14 (core) / 0.22.14 (libraries)

### New

- Metadata attached during asset or op execution can now be accessed in the I/O manager using `OutputContext.output_metadata`.
- [experimental] Single-run backfills now support batched inserts of asset materialization events. This is a major performance improvement for large single-run backfills that have database writes as a bottleneck. The feature is off by default and can be enabled by setting the `DAGSTER_EVENT_BATCH_SIZE` environment variable in a code server to an integer (25 recommended, 50 max). It is only currently supported in Dagster Cloud and OSS deployments with a postgres backend.
- [ui] The new Asset Details page is now enabled for new users by default. To turn this feature off, you can toggle the feature in the User Settings.
- [ui] Queued runs now display a link to view all the potential reasons why a run might remain queued.
- [ui] Starting a run status sensor with a stale cursor will now warn you in the UI that it will resume from the point that it was paused.
- [asset-checks] Asset checks now support asset names that include `.`, which can occur when checks are ingested from dbt tests.
- [dagster-dbt] The env var `DBT_INDIRECT_SELECTION` will no longer be set to `empty` when executing dbt tests as asset checks, unless specific asset checks are excluded. `dagster-dbt` will no longer explicitly select all dbt tests with the dbt cli, which had caused argument length issues.
- [dagster-dbt] Singular tests with a single dependency are now ingested as asset checks.
- [dagster-dbt] Singular tests with multiple dependencies must have the primary dependency must be specified using dbt meta.

```sql
{{
    config(
        meta={
            'dagster': {
                'ref': {
                    'name': <ref_name>,
                    'package': ... # Optional, if included in the ref.
                    'version': ... # Optional, if included in the ref.
                },
            }
        }
    )
}}

...
```

- [dagster-dbt] Column lineage metadata can now be emitted when invoking dbt. See the [documentation for details](https://docs.dagster.io/integrations/dbt/reference#emit-column-level-metadata-as-materialization-metadata-).
- [experimental][dagster-embedded-elt] Add the data load tool (dlt) integration for easily building and integration dlt ingestion pipelines with Dagster.
- [dagster-dbt][community-contribution] You can now specify a custom schedule name for schedules created with `build_schedule_from_dbt_selection`. Thanks [@dragos-pop](https://github.com/dragos-pop)!
- [helm][community-contribution] You can now specify a custom job namespace for your user code deployments. Thanks [@tmatthews0020](https://github.com/tmatthews0020)!
- [dagster-polars][community-contribution] Column schema metadata is now integrated using the dagster-specific metadata key in `dagster_polars`. Thanks [@danielgafni](https://github.com/danielgafni)!
- [dagster-datadog][community-contribution] Added `datadog.api` module to the `DatadogClient` resource, enabling direct access to API methods. Thanks [@shivgupta](https://github.com/shivonchain)!

### Bugfixes

- Fixed a bug where run status sensors configured to monitor a specific job would trigger for jobs with the same name in other code locations.
- Fixed a bug where multi-line asset check result descriptions were collapsed into a single line.
- Fixed a bug that caused a value to show up under “Target materialization” in the asset check UI even when an asset had had observations but never been materialized.
- Changed typehint of `metadata` argument on `multi_asset` and `AssetSpec` to `Mapping[str, Any]`.
- [dagster-snowflake-pandas] Fixed a bug introduced in 0.22.4 where column names were not using quote identifiers correctly. Column names will now be quoted.
- [dagster-aws] Fixed an issue where a race condition where simultaneously materializing the same asset more than once would sometimes raise an Exception when using the `s3_io_manager`.
- [ui] Fixed a bug where resizable panels could inadvertently be hidden and never recovered, for instance the right panel on the global asset graph.
- [ui] Fixed a bug where opening a run with an op selection in the Launchpad could lose the op selection setting for the subsequently launched run. The op selection is now correctly preserved.
- [community-contribution] Fixed `dagster-polars` tests by excluding `Decimal` types. Thanks [@ion-elgreco](https://github.com/ion-elgreco)!
- [community-contribution] Fixed a bug where auto-materialize rule evaluation would error on FIPS-compliant machines. Thanks [@jlloyd-widen](https://github.com/jlloyd-widen)!
- [community-contribution] Fixed an issue where an excessive DeprecationWarning was being issued for a `ScheduleDefinition` passed into the `Definitions` object. Thanks [@2Ryan09](https://github.com/2Ryan09)!

### Breaking Changes

- Creating a run with a custom non-UUID `run_id` was previously private and only used for testing. It will now raise an exception.
- [community-contribution] Previously, calling `get_partition_keys_in_range` on a `MultiPartitionsDefinition` would erroneously return partition keys that were within the one-dimensional range of alphabetically-sorted partition keys for the definition. Now, this method returns the cartesian product of partition keys within each dimension’s range. Thanks, [@mst](https://github.com/mst)!
- Added `AssetCheckExecutionContext` to replace `AssetExecutionContext` as the type of the `context` param passed in to `@asset_check` functions. `@asset_check` was an experimental decorator.
- [experimental] `@classmethod` decorators have been removed from [dagster-embedded-slt.sling](http://dagster-embedded-slt.sling) `DagsterSlingTranslator`
- [dagster-dbt] `@classmethod` decorators have been removed from `DagsterDbtTranslator`.
- [dagster-k8s] The default merge behavior when raw kubernetes config is supplied at multiple scopes (for example, at the instance level and for a particluar job) has been changed to be more consistent. Previously, configuration was merged shallowly by default, with fields replacing other fields instead of appending or merging. Now, it is merged deeply by default, with lists appended to each other and dictionaries merged, in order to be more consistent with how kubernetes configuration is combined in all other places. See [the docs](https://docs.dagster.io/deployment/guides/kubernetes/customizing-your-deployment#precedence-rules) for more information, including how to restore the previous default merge behavior.

### Deprecations

- `AssetSelection.keys()` has been deprecated. Instead, you can now supply asset key arguments to `AssetSelection.assets()` .
- Run tag keys with long lengths and certain characters are now deprecated. For consistency with asset tags, run tags keys are expected to only contain alpha-numeric characters, dashes, underscores, and periods. Run tag keys can also contain a prefix section, separated with a slash. The main section and prefix section of a run tag are limited to 63 characters.
- `AssetExecutionContext` has been simplified. Op-related methods and methods with existing access paths have been marked deprecated. For a full list of deprecated methods see this [GitHub Discussion](https://github.com/dagster-io/dagster/discussions/20974).
- The `metadata` property on `InputContext` and `OutputContext` has been deprecated and renamed to `definition_metadata` .
- `FreshnessPolicy` is now deprecated. For monitoring freshness, use freshness checks instead. If you are using `AutoMaterializePolicy.lazy()`, `FreshnessPolicy` is still recommended, and will continue to be supported until an alternative is provided.

### Documentation

- Lots of updates to examples to reflect the recent opt-in nature of I/O managers
- [Dagster Cloud alert guides](https://docs.dagster.io/dagster-cloud/managing-deployments/alerts) have been split up by alert type:
  - [Managing alerts in the Dagster Cloud UI](https://docs.dagster.io/dagster-cloud/managing-deployments/alerts/managing-alerts-in-ui)
  - [Managing alerts using the dagster-cloud CLI](https://docs.dagster.io/dagster-cloud/managing-deployments/alerts/managing-alerts-cli)
  - [Email alerts](https://docs.dagster.io/dagster-cloud/managing-deployments/alerts/email)
  - [Microsoft Teams alerts](https://docs.dagster.io/dagster-cloud/managing-deployments/alerts/microsoft-teams)
  - [Slack alerts](https://docs.dagster.io/dagster-cloud/managing-deployments/alerts/slack)
- Added info about asset check-based-alerts to the Dagster Cloud [alerting docs](https://docs.dagster.io/dagster-cloud/managing-deployments/alerts)
- The [Asset checks documentation](https://docs.dagster.io/concepts/asset-checks) got a face lift - info about defining and executing asset checks [now lives in its own guide](https://docs.dagster.io/concepts/assets/asset-checks/define-execute-asset-checks)
- Added a new guide for [using freshness checks](https://docs.dagster.io/concepts/assets/asset-checks/checking-for-data-freshness) to the Asset checks documentation
- Cleaned up the [Getting help guide](https://docs.dagster.io/getting-started/getting-help) - it now includes a high-level summary of all Dagster support resources, making it easier to skim!
- [community-contribution] Fixed the indentation level of a code snippet in the `dagster-polars` documentation. Thanks [@danielgafni](https://github.com/danielgafni)!

### Dagster Cloud

- The Dagster Cloud agent will now monitor the code servers that it spins to detect whether they have stopped serving requests, and will automatically redeploy the code server if it has stopped responding for an extended period of time.
- New additions and bugfixes in Insights:
  - Added per-metric cost estimation. Estimates can be added via the “Insights settings” button, and will appear in the table and chart for that metric.
  - Branch deployments are now included in the deployment filter control.
  - In the Deployments view, fixed deployment links in the data table.
  - Added support for BigQuery cost metrics.

## 1.6.14 (core) / 0.22.14 (libraries)

### Bugfixes

- [dagster-dbt] Fixed some issues with building column lineage metadata.

## 1.6.13 (core) / 0.22.13 (libraries)

### Bugfixes

- Fixed a bug where an asset with a dependency on a subset of the keys of a parent multi-asset could sometimes crash asset job construction.
- Fixed a bug where a Definitions object containing assets having integrated asset checks and multiple partitions definitions could not be loaded.

## 1.6.12 (core) / 0.22.12 (libraries)

### New

- `AssetCheckResult` now has a text `description` property. Check evaluation descriptions are shown in the Checks tab on the asset details page.
- Introduced `TimestampMetadataValue`. Timestamp metadata values are represented internally as seconds since the Unix epoch. They can be constructed using `MetadataValue.timestamp`. In the UI, they’re rendered in the local timezone, like other timestamps in the UI.
- `AssetSelection.checks` can now accept `AssetCheckKeys` as well as `AssetChecksDefinition`.
- [community-contribution] Metadata attached to an output at runtime (via either `add_output_metadata` or by passing to `Output`) is now available on `HookContext` under the `op_output_metadata` property. Thanks [@JYoussouf](https://github.com/JYoussouf)!
- [experimental] `@asset`, `AssetSpec`, and `AssetOut` now accept a `tags` property. Tags are key-value pairs meant to be used for organizing asset definitions. If `"__dagster_no_value"` is set as the value, only the key will be rendered in the UI. `AssetSelection.tag` allows selecting assets that have a particular tag.
- [experimental] Asset tags can be used in asset CLI selections, e.g. `dagster asset materialize --select tag:department=marketing`
- [experimental][dagster-dbt] Tags can now be configured on dbt assets, using `DagsterDbtTranslator.get_tags`. By default, we take the dbt tags configured on your dbt models, seeds, and snapshots.
- [dagster-gcp] Added get_gcs_keys sensor helper function.

### Bugfixes

- Fixed a bug that prevented external assets with dependencies from displaying properly in Dagster UI.
- Fix a performance regression in loading code locations with large multi-assets.
- [community-contribution] [dagster-databricks] Fix a bug with the `DatabricksJobRunner` that led to an inability to use dagster-databricks with Databricks instance pools. Thanks [@smats0n](https://github.com/smats0n)!
- [community-contribution] Fixed a bug that caused a crash when external assets had hyphens in their `AssetKey`. Thanks [@maxfirman](https://github.com/maxfirman)!
- [community-contribution] Fix a bug with `load_assets_from_package_module` that would cause a crash when any submodule had the same directory name as a dependency. Thanks [@CSRessel](https://github.com/CSRessel)!
- [community-contribution] Fixed a mypy type error, thanks @parthshyara!
- [community-contribution][dagster-embedded-elt] Fixed an issue where Sling assets would not properly read group and description metadata from replication config, thanks @jvyoralek!
- [community-contribution] Ensured annotations from the helm chart properly propagate to k8s run pods, thanks @maxfirman!

### Dagster Cloud

- Fixed an issue in Dagster Cloud Serverless runs where multiple runs simultaneously materializing the same asset would sometimes raise a “Key not found” exception.
- Fixed an issue when using [agent replicas](https://docs.dagster.io/dagster-cloud/deployment/agents/running-multiple-agents#running-multiple-agents-in-the-same-environment) where one replica would sporadically remove a code server created by another replica due to a race condition, leading to a “code server not found” or “Deployment not found” exception.
- [experimental] The metadata key for specifying column schema that will be rendered prominently on the new Overview tab of the asset details page has been changed from `"columns"` to `"dagster/column_schema"`. Materializations using the old metadata key will no longer result in the Columns section of the tab being filled out.
- [ui] Fixed an Insights bug where loading a view filtered to a specific code location would not preserve that filter on pageload.

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

## 1.6.4 (core) / 0.22.4 (libraries)

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

## 1.6.3 (core) / 0.22.3 (libraries)

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

## 1.6.2 (core) / 0.22.2 (libraries)

### New

- The warning for unloadable sensors and schedules in the Dagster UI has now been removed.
- When viewing an individual sensor or schedule, we now provide a button to reset the status of the sensor or schedule back to its default status as defined in code.

### Experimental

- [asset-checks] dbt asset checks now respect `warn_if`/ `error_if` severities

### Dagster Cloud

- Fixed a bug introduced in `1.6.0` where run status sensors did not cursor correctly when deployed on Dagster Cloud.
- Schedule and sensor mutations are now tracked in the audit log.

## 1.6.1 (core) / 0.22.1 (libraries)

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

## 1.6.0 (core) / 0.22.0 (libraries)

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

## 1.5.14 / 0.21.14 (libraries)

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

## 1.5.13 / 0.21.13 (libraries)

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

## 1.5.12 / 0.21.12 (libraries)

### Bugfixes

- [dagster-embedded-elt] Fixed an issue where `EnvVar`s used in Sling source and target configuration would not work properly in some circumstances.
- [dagster-insights] Reworked the Snowflake insights ingestion pipeline to improve performance and increase observability.

## 1.5.11 / 0.21.11 (libraries)

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

## 1.5.10 / 0.21.10 (libraries)

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

## 1.5.9 / 0.21.9 (libraries)

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

## 1.5.8 / 0.21.8 (libraries)

### Bugfixes

- Fixed an error when trying to directly invoke a run status sensor when passing resources.
- [dagster-airbyte][dagster-fivetran] Fixed an issue where `EnvVars` used in Airbyte or Fivetran resources would show up as their processed values in the launchpad when loading assets from a live Fivetran or Airbyte instance.

### Dagster Cloud

- Substantially improved performance of the Dagster insights DBT/Snowflake usage job.

## 1.5.7 / 0.21.7 (libraries)

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

## 1.5.6 / 0.21.6 (libraries)

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

## 1.5.5 / 0.21.5 (libraries)

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
- Improved readability of [API docs landing page](https://docs.dagster.io/api)
- Removed straggling mention of Dagit from the [Kubernetes OSS deployment guide](https://docs.dagster.io/deployment/guides/kubernetes/deploying-with-helm)

## 1.5.4 / 0.21.4 (libraries)

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

## 1.5.3 / 0.21.3 (libraries)

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

## 1.5.2 / 0.21.2 (libraries)

### Bugfixes

- Previously, asset backfills targeting assets with multi-run backfill policies would raise a "did not submit all run requests" error. This has been fixed.

### Dagster Cloud

- The experimental dagster-insights package has receieved some API surface area updates and bugfixes.

## 1.5.1 / 0.21.1 (libraries)

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

## 1.5.0 (core) / 0.21.0 (libraries) "How Will I Know"

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
## old
@op
def my_op(context: AssetExecutionContext):
    ...

## correct
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

## 1.4.17 / 0.20.17 (libraries)

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

## 1.4.16 / 0.20.16 (libraries)

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

## 1.4.15 / 0.20.15 (libraries)

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

## 1.4.14 / 0.20.14 (libraries)

### New

- Added a new tooltip to asset runs to either view the asset list or lineage

### Bugfixes

- [ui] Fixed an issue where re-executing a run from a particular run's page wouldn’t navigate to the newly created run

### Experimental

- [dagster-ext] An initial version of the `dagster-ext` module along with subprocess, docker, databricks, and k8s pod integrations are now available. Read more at https://github.com/dagster-io/dagster/discussions/16319. Note that the module is temporarily being published to PyPI under `dagster-ext-process`, but is available in python as `import dagster_ext`.
- [asset checks] Added an ‘execute’ button to run checks without materializing the asset. Currently this is only supported for checks defined with `@asset_check` or `AssetChecksDefinition`.
- [asset checks] Added `check_specs` argument to `@graph_multi_asset`
- [asset checks] Fixed a bug with checks on `@graph_asset` that would raise an error about nonexistant checks

## 1.4.13 / 0.20.13 (libraries)

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

## 1.4.12 / 0.20.12 (libraries)

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

## 1.4.11 / 0.20.11 (libraries)

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

## 1.4.10 / 0.20.10 (libraries)

### Bugfixes

- [dagster-webserver] Fixed an issue that broke loading static files on Windows.

## 1.4.9 / 0.20.9 (libraries)

### Bugfixes

- [dagster-webserver] Fixed an issue that caused some missing icons in the UI.

## 1.4.8 / 0.20.8 (libraries)

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

## 1.4.7 / 0.20.7 (libraries)

### Experimental

- Added a `respect_materialization_data_versions` option to auto materialization. It can enabled in `dagster.yaml` with

  ```yaml
  auto_materialize:
    respect_materialization_data_versions: True
  ```

  This flag may be changed or removed in the near future.

## 1.4.6 / 0.20.6 (libraries)

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

## 1.4.5 / 0.20.5 (libraries)

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

## 1.4.4 / 0.20.4 (libraries)

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

## 1.4.3 / 0.20.3 (libraries)

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

## 1.4.2 / 0.20.2 (libraries)

### Bugfixes

- Fixes a bug in `dagster-dbt` that was preventing it from correctly materializing subselections of dbt asset.

## 1.4.1 / 0.20.1 (libraries)

### Bugfixes

- Fixes a bug in `dagster-dbt` that was preventing it efficiently loading dbt projects from a manifest.

## 1.4.0 / 0.20.0 (libraries) "Material Girl"

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

## 1.3.14 (core) / 0.19.14 (libraries)

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

## 1.3.13 (core) / 0.19.13 (libraries)

### Bugfixes

- Fixes a bug in `dagster project from-example` that was preventing it from downloading examples correctly.

## 1.3.12 (core) / 0.19.12 (libraries)

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

## 1.3.11 (core) / 0.19.11 (libraries)

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

## 1.3.10 (core) / 0.19.10 (libraries)

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

## 1.3.9 (core) / 0.19.9 (libraries)

### Dagster Cloud

- Fixed an issue in the `1.3.8` release where the Dagster Cloud agent would sometimes fail to start up with an import error.

## 1.3.8 (core) / 0.19.8 (libraries)

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

## 1.3.7 (core) / 0.19.7 (libraries)

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

## 1.3.6 (core) / 0.19.6 (libraries)

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

## 1.3.5 (core) / 0.19.5 (libraries)

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

## 1.3.4 (core) / 0.19.4 (libraries)

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

## 1.3.3 (core) / 0.19.3 (libraries)

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

## 1.3.2 (core) / 0.19.2 (libraries)

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

## 1.3.1 (core) / 0.19.1 (libraries)

### New

- Performance improvements when evaluating time-partitioned run requests within sensors and schedules.
- [ui] Performance improvements when loading the asset catalog and launchpad for deployments with many time-partitioned assets.

### Bugfixes

- Fixed an issue where loading a Definitions object that included sensors attached to multiple jobs would raise an error.
- Fixed a bug in which Pythonic resources would produce underlying resource values that would fail reference equality checks. This would lead to a conflicting resource version error when using the same Pythonic resource in multiple places.

## 1.3.0 (core) / 0.19.0 (libraries) "Smooth Operator"

## **Major Changes since 1.2.0 (core) / 0.18.0 (libraries)**

### Core

- **Auto-materialize policies replace the asset reconciliation sensor** - We significantly renovated the APIs used for specifying which assets are scheduled declaratively. Compared to `build_asset_reconciliation_sensor`s , `AutoMaterializePolicy` works across code locations, as well as allow you to customize the conditions under which each asset is auto-materialized. [[docs](https://docs.dagster.io/concepts/assets/asset-auto-execution)]
- **Asset backfill page** - A new page in the UI for monitoring asset backfills shows the progress of each asset in the backfill.
- **Clearer labels for tracking changes to data and code** - Instead of the opaque “stale” indicator, Dagster’s UI now indicates whether code, upstream data, or dependencies have changed. When assets are in violation of their `FreshnessPolicy`s, Dagster’s UI now marks them as “overdue” instead of “late”.
- **Auto-materialization and observable source assets** - Assets downstream of an observable source asset now use the source asset observations to determine whether upstream data has changed and assets need to be materialized.
- **Pythonic Config and Resources** - The set of APIs introduced in 1.2 is no longer experimental [[community memo](https://dagster.io/blog/pythonic-config-and-resources)]. Examples, integrations, and documentation have largely ported to the new APIs. Existing resources and config APIs will continue to be supported for the foreseeable future. Check out [migration guide](https://docs.dagster.io/guides/dagster/migrating-to-pythonic-resources-and-config) to learn how to incrementally adopt the new APIs.

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

## 1.2.7 (core) / 0.18.7 (libraries)

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

## 1.2.6 (core) / 0.18.6 (libraries)

### Bugfixes

- Fixed a GraphQL resolution error which occurred when retrieving metadata for step failures in the event log.

## 1.2.5 (core) / 0.18.5 (libraries)

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

## 1.2.4 (core) / 0.18.4 (libraries)

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

## 1.2.3 (core) / 0.18.3 (libraries)

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

## 1.2.2 (core) / 0.18.2 (libraries)

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

## 1.2.1 (core) / 0.18.1 (libraries)

### Bugfixes

- Fixed a bug with postgres storage where daemon heartbeats were failing on instances that had not been migrated with `dagster instance migrate` after upgrading to `1.2.0`.

## 1.2.0 (core) / 0.18.0 (libraries)

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

## 1.1.21 (core) / 0.17.21 (libraries)

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

## 1.1.20 (core) / 0.17.20 (libraries)

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

## 1.1.19 (core) / 0.17.19 (libraries)

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

## 1.1.18 (core) / 0.17.18 (libraries)

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

## 1.1.17 (core) / 0.17.17 (libraries)

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

## 1.1.15 (core) / 0.17.15 (libraries)

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

## 1.1.14 (core) / 0.17.14 (libraries)

### New

- Large asset graphs can now be materialized in Dagit without needing to first enter an asset subset. Previously, if you wanted to materialize every asset in such a graph, you needed to first enter `*` as the asset selection before materializing the assets.
- Added a pin of the `sqlalchemy` package to `<2.0.0` due to a breaking change in that version.
- Added a pin of the `dbt-core` package to `<1.4.0` due to breaking changes in that release that affected the Dagster dbt integration. We plan to remove this pin in the next release.
- Added a pin of the `jupyter-client` package to `<8.0` due to an issue with the most recent release causing hangs while running dagstermill ops.

### Bugfixes

- Fixed an issue where the Backfills page in Dagit didn't show partition status for some backfills.
- [dagster-aws] Fixed an issue where the `EcsRunLauncher` sometimes waited much longer than intended before retrying after a failure launching a run.
- [dagster-mysql] Fixed an issue where some implementations of MySQL storage were raising invalid version errors.

## 1.1.13 (core) / 0.17.13 (libraries)

### Bugfixes

- The `nux` section of `dagster.yaml` config has been fixed.
- Changes when heartbeats occur in the daemon to avoid crashes in certain conditions.
- Fixed an issue where passing a workspace file as an argument into the `dagster dev` command raised an error
- [dagit] Fixes an issue with asset names being truncated by long asset descriptions in the asset catalog, making them impossible to click.
- [dagit] The backfill page no longer fails to load if any of the asset backfills had assets that were partitioned at the time of the backfill but are no longer partitioned.

## 1.1.12 (core) / 0.17.12 (libraries)

### Bugfixes

- [dagit] Fixes a "maximum call stack size exceeded" error when viewing a materialization of a root asset in Asset Details

## 1.1.11 (core) / 0.17.11 (libraries)

### New

- Added a new `dagster dev` command that can be used to run both Dagit and the Dagster daemon in the same process during local development. See the new [Running Dagster Locally guide](https://docs.dagster.io/deployment/guides/running-locally) in the docs for more information.
- Added instructions for installing the `dagster` package on M1 and M2 Macs that avoids installation errors when building the `grpcio` package. See [the Installing Dagster guide in the docs](https://docs.dagster.io/getting-started/install) for more information.
- `create_repository_using_definitions_args` has been added for users to backport their repository definitions to the new `Definitions` API
- When running Dagit on your local machine, a prompt will now appear that allows you to optionally enter an email address to receive Dagster security updates or subscribe to the Dagster newsletter. This prompt can be dismissed in the UI, or permanently disabled by adding the following to your `dagster.yaml` file:

```
nux:
  enabled: false
```

- The `grpcio` pin in Dagster to \<1.48.1 has been restored for Python versions 3.10 and 3.11, due to [upstream issues](https://github.com/grpc/grpc/issues/31885) in the grpcio package causing hangs in Dagster.
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

## 1.1.10 (core) / 0.17.10 (libraries)

### New

- The `selection` argument of `define_asset_job` now accepts lists of `AssetKey`s or `AssetsDefinitions`.
- `RunRequest` now takes a `stale_assets_only` flag that filters the full set of assets that would be materialized by a job to stale assets only. This can be used in schedules and sensors.
- Dagit will now choose a different open port on the local machine to run on when no port is specified to the `dagit` command and the default port 3000 is already in use.
- The `grpcio` pin in Dagster to \<1.48.1 has been removed for Python versions 3.10 and 3.11. Python 3.7, 3.8, and 3.9 are still pinned to \<1.48.1 due to a bug in the grpc library that is causing the process to sometimes hang.
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

## 1.1.9 (core) / 0.17.9 (libraries)

### Bugfixes

- Fixed an issue which would cause errors when using built-in generic types in annotations for asset and op parameters.
- Fixed an unintentional dependency on Pydantic >=1.8 which lacked a pin, now older versions of the package may be used.

## 1.1.8 (core) / 0.17.8 (libraries)

### New

- Asset backfills launched from the asset graph now respect partition mappings. For example, if partition N of asset2 depends on partition N-1 of asset1, and both of those partitions are included in a backfill, asset2’s partition N won’t be backfilled until asset1’s partition N-1 has been materialized.
- Asset backfills launched from the asset graph will now only materialize each non-partitioned asset once - after all upstream partitions within the backfill have been materialized.
- Executors can now be configured with a `tag_concurrency_limits` key that allows you to specify limits on the number of ops with certain tags that can be executing at once within a single run. See the [docs](https://docs.dagster.io/concepts/ops-jobs-graphs/job-execution#op-concurrency-limits) for more information.
- `ExecuteInProcessResult`, the type returned by `materialize`, `materialize_to_memory`, and `execute_in_process`, now has an `as
