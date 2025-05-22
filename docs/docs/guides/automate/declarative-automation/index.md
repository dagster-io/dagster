---
description: Dagster Declarative Automation is a framework that allows you to access information about events that impact the status of your assets, and the dependencies between them.
keywords:
  - declarative
  - automation
  - schedule
  - automation condition
sidebar_position: 20
title: Declarative Automation
---

Declarative Automation is a framework that uses information about the status of your assets and their dependencies to launch executions of your assets.

Not sure what automation method to use? Check out the [automation overview](/guides/automate) for a comparison of the different automation methods available in Dagster.

:::note

To use Declarative Automation, you will need to enable the default **[automation condition sensor](automation-condition-sensors)** in the UI, which evaluates automation conditions and launches runs in response to their statuses. To do so, navigate to **Automation**, find the desired code location, and toggle on the **default_automation_condition_sensor** sensor.

:::

## Recommended automation conditions

An <PyObject section="assets" module="dagster" object="AutomationCondition" /> on an asset or asset check describe the conditions under which work should be executed.

While the system can be customized to fit your specific needs, we recommend starting with one of the built-in conditions below, rather than building up your own condition from scratch.

<Tabs>
  <TabItem value="on_cron" label="on_cron" default>

The <PyObject section="assets" module="dagster" object="AutomationCondition.on_cron" /> will execute an asset once per cron schedule tick, after all upstream dependencies have updated. This allows you to schedule assets to execute on a regular cadence regardless of the exact time that upstream data arrives.

In the example below, the asset will start waiting for each of its dependencies to be updated at the start of each hour. Once all dependencies have updated since the start of the hour, this asset will be immediately requested.

<CodeExample path="docs_snippets/docs_snippets/concepts/declarative_automation/on_cron/basic.py" />

**Behavior**

If you would like to customize aspects of this behavior, refer to the [customizing on_cron](customizing-automation-conditions/customizing-on-cron-condition) guide.

- If at least one upstream partition of _all_ upstream assets has been updated since the previous cron schedule tick, and the downstream asset has not yet been requested or updated, the downstream asset will be requested.
- If all upstream assets **do not** update within the given cron tick, the downstream asset will not be requested.
- For **time-partitioned** assets, this condition will only request the _latest_ time partition of the asset.
- For **static** and **dynamic-partitioned** assets, this condition will request _all_ partitions of the asset.

</TabItem>

<TabItem value="eager" label="eager">

The <PyObject section="assets" module="dagster" object="AutomationCondition.eager" /> condition allows you to automatically update an asset whenever any of its dependencies are updated. This is used to ensure that whenever upstream changes happen, they are automatically propagated downstream.

In the example below, the following asset will be automatically updated whenever any of its upstream dependencies are updated:

<CodeExample path="docs_snippets/docs_snippets/concepts/declarative_automation/eager/basic.py" />

**Behavior**

- If _any_ upstream partitions have not been materialized, the downstream asset will not be requested.
- If _any_ upstream partitions are currently part of an in-progress run, the downstream asset will wait for those runs to complete before being requested.
- If the downstream asset is already part of an in-progress run, the downstream asset will wait for that run to complete before being requested.
- For **time-partitioned** assets, this condition will only consider the _latest_ time partition of the asset.
- For **static** and **dynamic-partitioned** assets, this condition will consider _all_ partitions of the asset.
- If an upstream asset is _observed_, this will only be treated as an update to the upstream asset if the data version has changed since the previous observation.
- If an upstream asset is _materialized_, this will be treated as an update to the upstream asset regardless of the data version of that materialization.

To customize this behavior, see the [customizing eager](customizing-automation-conditions/customizing-eager-condition) guide.

</TabItem>

  <TabItem value="on_missing" label="on_missing">

The <PyObject section="assets" module="dagster" object="AutomationCondition.on_missing" /> condition will execute a missing asset partition when all upstream partitions of the asset are available. This is typically used to manage dependencies between partitioned assets, where partitions should fill in as soon as upstream data is available.

In the example below, as soon as all hourly partitions of the upstream asset are filled in, the downstream asset will be immediately requested:

<CodeExample path="docs_snippets/docs_snippets/concepts/declarative_automation/on_missing/basic.py" />

**Behavior**

- If _any_ upstream partition of any upstream asset has not been materialized, the downstream asset will not be requested.
- For **time-partitioned** assets, this condition will only request the _latest_ time partition of the asset.
- This condition will only consider partitions that were added to the asset after the condition was enabled.

To customize this behavior, see the [customizing on_missing](customizing-automation-conditions/customizing-on-missing-condition) guide.

</TabItem>

</Tabs>
