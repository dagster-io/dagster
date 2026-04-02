---
description: How to migrate from asset sensors, multi-asset sensors, and external-system-polling sensors to Declarative Automation, with pattern mappings, caveats, and strategies for handling run config.
keywords:
  - declarative automation
  - sensor migration
  - multi-asset sensor
  - asset sensor
  - automation condition
  - external assets
  - information schema
sidebar_position: 500
title: Migrating from sensors to Declarative Automation
---

Asset sensors and multi-asset sensors provide imperative control over when to launch runs in response to asset materializations. [Declarative Automation](/guides/automate/declarative-automation) replaces much of this with a composable, condition-based model where you describe what should happen rather than how to detect it.

This guide covers common sensor patterns, their Declarative Automation equivalents, caveats, and strategies for handling scenarios like dynamic run configuration.

## Advantages of Declarative Automation

Declarative Automation provides several advantages over imperative sensors for asset-centric workflows:

- **Asset-level observability.** With sensors, understanding _why_ an asset did or didn't execute requires reading sensor logs and tracing cursor state. With Declarative Automation, every asset shows its automation condition evaluation directly in the Dagster UI — you can inspect the condition tree, see which sub-conditions are true or false, and understand exactly why an asset was or wasn't requested on any given tick.
- **No separate orchestration code.** Sensors require a separate sensor function definition and job definition. Declarative Automation conditions are declared directly on the asset, eliminating the need for standalone orchestration code that can drift out of sync with the assets it manages.
- **Dependency-aware by default.** Built-in conditions like `eager()` and `on_cron()` automatically respect the asset graph — they understand upstream/downstream relationships, partition mappings, and in-progress state. Sensors must manually implement this awareness through cursor management and event inspection.
- **Composable and reusable.** Conditions are built from small, composable operators (`since`, `newly_true`, `all_deps_match`) that can be combined, customized, and shared across assets. Sensor logic tends to be bespoke per sensor, making it harder to maintain consistency across a growing asset graph.
- **Reduced boilerplate.** Common patterns like "run after all dependencies update" or "run on a schedule when dependencies are fresh" are one-liners with `on_cron()`, replacing dozens of lines of sensor code with cursor management, event filtering, and job wiring.

## When to migrate

Declarative Automation is a good fit if your sensor does one of the following:

- Triggers downstream assets when upstream assets update
- Waits for all (or any) of a set of dependencies before launching a run
- Schedules assets on a cron cadence after dependencies are fresh
- Fills in missing partitions when upstream data arrives

**Keep your sensor** if it:

- It's working as intended. If declarative automation does not help you achieve a concrete goal, we recommend keeping your sensor approach.
- Performs side effects (sends Slack notifications, writes audit logs, calls external APIs).
- Needs to inspect materialization metadata (for example, row count thresholds) to decide whether to trigger. However, this can often be handled with [asset checks](#conditional-trigger-based-on-metadata) and an automation condition that gates on upstream checks passing.
- Produces `RunRequest` objects with dynamic `run_config` that varies per materialization event (though see [Migrating run config](#migrating-run-config) for strategies to move this logic).
- Needs to accumulate multiple materialization events before triggering (for example, "wait for 5 materializations before firing"). Declarative Automation conditions are boolean per evaluation tick, not counters.

## Migrating single-asset sensors

Single-asset sensors (`@asset_sensor`) monitor one upstream asset and trigger a job when it materializes. These are the simplest sensors to migrate because <PyObject section="assets" module="dagster" object="AutomationCondition.eager" /> is a near-direct replacement.

### Basic trigger on upstream update

<Tabs>
  <TabItem value="sensor" label="Sensor" default>

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/migration/sensor_basic_trigger.py"
  title="sensors.py"
/>

  </TabItem>
  <TabItem value="da" label="Declarative Automation">

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/migration/da_basic_trigger.py"
  title="assets.py"
/>

  </TabItem>
</Tabs>

`eager()` triggers whenever any dependency updates, which for a single dependency is equivalent to "trigger when this asset updates." It also includes guards that prevent execution when dependencies are missing or in progress. See [the docs](/guides/automate/declarative-automation#recommended-automation-conditions) to learn more.

:::tip Cross-code location sensors

If your `@asset_sensor` monitors an asset in a different code location, no special handling is needed, since Declarative Automation natively detects materializations across code locations. Declare the upstream asset key as a dependency and use `eager()` as shown above.

:::

### Conditional trigger based on metadata

<Tabs>
  <TabItem value="sensor" label="Sensor" default>

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/migration/sensor_metadata_trigger.py"
  title="sensors.py"
/>

  </TabItem>
  <TabItem value="da" label="Declarative Automation">

Automation conditions don't have access to materialization metadata directly. Instead, use an [asset check](/guides/test/asset-checks) to inspect the metadata and gate downstream execution:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/migration/da_metadata_trigger.py"
  title="assets.py"
/>

  </TabItem>
</Tabs>

How this works:

1. `daily_sales` materializes and reports `row_count` in its metadata.
2. `sales_row_count_check` is an asset check on `daily_sales` — it reads the materialization metadata from the event log and fails with `ERROR` severity if the row count is below the threshold.
3. `analytics` uses `eager()` combined with a custom condition that gates on all upstream asset checks passing. The `eager()` condition detects that `daily_sales` updated, but the checks condition holds execution until no upstream checks are in a failed state. If any check fails, `analytics` does not execute.

## Migrating multi-asset sensors

### Pattern 1: All dependencies updated to trigger downstream \{#pattern-1}

<Tabs>
  <TabItem value="sensor" label="Sensor" default>

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/migration/sensor_all_deps.py"
  title="sensors.py"
/>

  </TabItem>
  <TabItem value="da" label="Declarative Automation">

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/migration/da_all_deps.py"
  title="assets.py"
/>

  </TabItem>
</Tabs>

This sensor checks that **every** monitored asset has a new materialization before triggering. <PyObject section="assets" module="dagster" object="AutomationCondition.eager" /> is **not** the right replacement, since it fires when any dep updates. Use <PyObject section="assets" module="dagster" object="AutomationCondition.on_cron" /> instead.

#### Why `on_cron` is recommended \{#recommended-on-cron}

`on_cron` waits until _all_ dependencies have updated since the latest cron tick before requesting execution. For more detail on how `on_cron` works, see [the guide](/guides/automate/declarative-automation#recommended-automation-conditions).

- **Synchronization guarantee.** The cron tick acts as a synchronization barrier. All dependencies must update within the same cron window, preventing desynchronization issues that plague event-driven "all dependencies" approaches (see [why custom all-dependencies conditions are risky](#why-custom-all-deps-risky)).
- **Simple to reason about.** "Run once per hour after all dependencies are fresh" is easy to understand and debug.
- **Built-in deduplication.** Only fires once per cron window, even if dependencies update multiple times.

The trade-off is that you need to pick a cron schedule. The interval must be wide enough that all dependencies complete within a single window. If your dependencies all complete within a 30-minute window, an hourly cron works. A very frequent cron like `"* * * * *"` (every minute) actually makes this worse, as it creates more cron ticks that can land between dependency updates and reset the tracking.

For advanced uses of `on_cron`, see the [customizing on_cron guide](/guides/automate/declarative-automation/customizing-automation-conditions/customizing-on-cron-condition#executing-later-than-upstream-assets).

#### Why custom "all dependencies updated" conditions are risky \{#why-custom-all-deps-risky}

If you want to trigger as soon as all dependencies have updated since the target's last materialization (no cron boundary), you might try building a custom condition using <PyObject section="assets" module="dagster" object="AutomationCondition.asset_matches" />:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/migration/da_all_deps_custom.py"
  title="assets.py"
  startAfter="start_all_deps_custom"
  endBefore="end_all_deps_custom"
/>

This condition individually tracks each upstream dependency and checks whether it has been updated more recently than the target asset was last requested or materialized. Unlike the broken `all_deps_match(newly_updated())` approach (where `newly_updated()` is only true for a single tick), this uses `.since()` to create persistent per-dep tracking.

**However, this approach has serious desynchronization risks.** Consider a target asset with two upstream dependencies that update on different cadences, one daily and one weekly:

1. **Normal operation works fine.** Both dependencies update, the condition is satisfied, the target materializes. The `.since()` resets and waits for both dependencies to update again.

2. **Manual backfill breaks synchronization.** If someone manually backfills the weekly asset mid-week, the daily asset has already updated since the target's last materialization. The condition is immediately satisfied and fires an unwanted run — the target materializes against the backfilled weekly data and the latest daily data, even though you probably wanted to wait for the next natural cycle.

3. **Desynchronization can persist.** With two weekly dependencies, a mid-week backfill of one doesn't fire (the other weekly hasn't updated). But the next week, whichever weekly dependency materializes first now satisfies the condition for the backfilled dependency (which updated mid-week, more recently than the target). The target fires before the second weekly dependency has this week's data, and this off-by-one-week pattern continues indefinitely.

The root cause is that an event-driven "all dependencies updated since target" condition has no synchronization barrier. Unlike a cron tick that forces all dependencies into the same time window, the condition can be satisfied by dependencies that updated at different times for different reasons.

**`on_cron` avoids this entirely** because the cron tick resets tracking for every dependency simultaneously. A backfilled asset's update only counts if it happened after the latest cron tick, which is the same tick that every other dependency is measured against.

:::note

The `asset_matches` approach also requires hardcoding the target asset key in the condition because there is currently no built-in way for a condition to reference the asset it is applied to. This means the condition is not reusable across assets.

:::

### Pattern 2: Any dependency updated to trigger downstream

<Tabs>
  <TabItem value="sensor" label="Sensor" default>

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/migration/sensor_any_dep.py"
  title="sensors.py"
/>

  </TabItem>
  <TabItem value="da" label="Declarative Automation">

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/migration/da_any_dep.py"
  title="assets.py"
/>

  </TabItem>
</Tabs>

`eager()` triggers when any dependency updates. It also includes guards: it won't fire if any dependency is missing or if the target is already in progress.

### Pattern 3: Partitioned assets — map upstream to downstream partitions

<Tabs>
  <TabItem value="sensor" label="Sensor" default>

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/migration/sensor_partitioned.py"
  title="sensors.py"
/>

  </TabItem>
  <TabItem value="da" label="Declarative Automation">

When both assets have partition definitions with a defined mapping, Declarative Automation automatically handles the partition fan-in/fan-out. Choose between <PyObject section="assets" module="dagster" object="AutomationCondition.on_missing" /> and `eager()` based on whether the downstream should re-materialize when upstream partitions re-run:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/migration/da_partitioned.py"
  title="assets.py"
  startAfter="start_on_missing"
  endBefore="end_on_missing"
/>

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/migration/da_partitioned.py"
  title="assets.py"
  startAfter="start_eager"
  endBefore="end_eager"
/>

  </TabItem>
</Tabs>

For most partition fan-in use cases, `on_missing` is the better default. If you need re-materialization on upstream refreshes, use `eager`, but be aware of the volume of downstream runs it can produce.

### Pattern 4: Only trigger when specific upstream assets update

<Tabs>
  <TabItem value="sensor" label="Sensor" default>

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/migration/sensor_selective.py"
  title="sensors.py"
/>

  </TabItem>
  <TabItem value="da" label="Declarative Automation">

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/migration/da_selective.py"
  title="assets.py"
/>

  </TabItem>
</Tabs>

Use `.ignore()` to exclude specific dependencies from triggering automation, and `.allow()` to restrict to only specific dependencies.

## Migrating sensors that poll external system \{#migrating-external-system-sensors}

A common pattern is a sensor that queries an external system (e.g., a relational database's information schema, or a set of files in blob storage) to detect when the data within that system has been updated, and then launches a Dagster job in response.

<Tabs>
  <TabItem value="sensor" label="Sensor" default>

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/migration/sensor_external_db_tables.py"
  title="sensors.py"
/>

The sensor handles two responsibilities: detecting external changes and triggering downstream work. This couples detection logic to orchestration, and the downstream assets have no visibility into which upstream tables actually changed.

  </TabItem>
  <TabItem value="da" label="Declarative Automation">

The recommended approach splits these responsibilities:

1. **Model the external tables as [external assets](/guides/build/assets/external-assets).** Each table gets an `AssetSpec`, making it visible in the asset graph and available as a dependency.
2. **Use a sensor to report materializations** when the information schema shows a table has been updated. This sensor doesn't launch jobs — it just records that an external asset was updated.
3. **Downstream assets use Declarative Automation** (`eager()`, `on_cron()`, etc.) to react to those updates through the normal asset graph.

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/migration/da_external_db_tables.py"
  title="assets.py"
/>

  </TabItem>
</Tabs>

This approach gives you:

- **Full lineage visibility.** External tables appear in the asset graph alongside Dagster-managed assets, so you can trace data flow from source to downstream.
- **Decoupled detection from orchestration.** The sensor's only job is to report that external data changed. Downstream scheduling is handled by automation conditions, which can differ per asset — `eager()` for latency-sensitive assets, `on_cron()` for batch assets that need all dependencies fresh.
- **Standard automation tooling.** The same condition evaluation UI, tick history, and debugging tools that work for Dagster-native assets also work for assets downstream of external assets.

For full details on modeling external assets, reporting materializations with sensors or the REST API, and building dependency graphs of external assets, see the [External assets guide](/guides/build/assets/external-assets).

## Migrating run config \{#migrating-run-config}

Sensors can build `RunRequest` objects with arbitrary `run_config` that varies per materialization event. Declarative Automation launches runs with a fixed configuration. This section covers strategies for handling this gap.

### Strategy 1: Move config into the asset function

If your sensor passes configuration derived from upstream metadata, move that logic into the asset itself. The asset can read from the event log at execution time.

<Tabs>
  <TabItem value="sensor" label="Sensor" default>

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/migration/sensor_run_config.py"
  title="sensors.py"
/>

  </TabItem>
  <TabItem value="da" label="Declarative Automation">

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/migration/da_run_config.py"
  title="assets.py"
/>

  </TabItem>
</Tabs>

This is the most common approach. The asset is self-contained and doesn't rely on external orchestration to pass it the right parameters.

### Strategy 2: Use tags on the automation sensor

If you need to attach fixed metadata to all runs launched by automation, use `run_tags` on the <PyObject section="assets" module="dagster" object="AutomationConditionSensorDefinition" />:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/migration/da_run_tags.py"
  title="definitions.py"
/>

This doesn't replace dynamic run config, but it handles the common case of tagging runs for observability or routing.

### When to keep the sensor

If your sensor's run config truly varies per materialization event in ways that can't be derived at execution time (e.g., the sensor receives webhook payloads with one-time tokens, or the config depends on which specific materialization event triggered the sensor out of many), keep the sensor. Not every sensor needs to be migrated.

## Setting up the automation condition sensor

Declarative Automation conditions are evaluated by an <PyObject section="assets" module="dagster" object="AutomationConditionSensorDefinition" />. A default sensor is created automatically for any code location with automation conditions — you just need to toggle it on in the UI under **Automation**. For custom sensor configurations (evaluation frequency, run tags, asset selection scoping), see [Automation condition sensors](/guides/automate/declarative-automation/automation-condition-sensors).

## Caveats

### Declarative Automation is job-less

Declarative automation is powerful, but because it is at the asset level, there is no longer a job with a schedule that "contains" a set of assets. Jobs provide a helpful way to observe and reason about your data pipelines, and we recommend using schedules and jobs as long as they are useful before switching to a more complex and flexible system like declarative automation.

### `eager()` fires on any dependency update, not all

If your multi-asset sensor waits for all monitored assets before triggering, `eager()` is not a replacement, since it fires when any dependency updates. For alternatives, see [Pattern 1](#pattern-1).

### No side effects in conditions

Automation conditions should be true or false. Move side effects to [run status sensors](/guides/automate/sensors/run-status-sensors) or [asset checks](/guides/test/asset-checks).

### Cursor semantics are different

In Declarative Automation, cursor state is managed automatically via `.since()` and `.since_last_handled()`. You can't implement patterns like "skip every other materialization" or "batch N events."

### Evaluation frequency

The automation condition sensor defaults to 30 second evaluations, but complex conditions over many assets can take longer. For large deployments, consider splitting into multiple sensors with targeted <PyObject section="assets" module="dagster" object="AssetSelection" />.

### Run grouping behavior

Declarative Automation groups assets into runs automatically when downstream conditions depend on upstream assets being requested in the same tick. This means you have less control over run boundaries than with explicit `RunRequest` objects.

### Partitioned assets with `on_cron`

For time-partitioned assets, `on_cron` only targets the _latest_ time partition. For all partitions or specific historical partitions, use `on_missing()` or a custom condition with `in_latest_time_window(lookback_delta=...)`.

### Observable source assets

If your upstream is an `@observable_source_asset`, `eager()` only treats an observation as an "update" if the data version changes. Regular `@asset` materializations are always treated as updates.
