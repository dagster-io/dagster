---
title: "Declarative automation"
description: "Learn to automatically materialize assets when criteria are met."
sidebar_position: 10
sidebar_label: "Declarative automation"
---

# Declarative Automation

TODO: ADD EXPERIMENTAL CALLOUT

Dagster can automatically materialize assets when criteria are met, enabling a declarative approach to asset materialization. Instead of defining explicit workflows to materialize assets, you describe the conditions under which they should be materialized and let the system kick off runs in response.

For example, you have an asset that's scheduled to execute every day at midnight. Instead of executing whether there's new data or not, you can use Declarative Automation to materialize the asset only after its parent has been updated.

Using Declarative Automation helps you:

- Ensure you're working with the most up-to-date data
- Optimize resource usage by only materializing assets when needed
- Simplify how your team understands their assets by consolidating all asset logic to a single location

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need familiarity with:

- [Assets](/concepts/assets)
- [Sensors](/todo)
- [Code locations](/todo)

</details>

## Define automation conditions

Automation conditions describe the conditions under which an asset should be executed. They can be set on native Dagster assets (`@asset`) or [external assets](/guides/external-assets) (`AssetSpec`).

```python
from dagster import dg

# Condition that materializes an asset that's never been materialized, or
# when the asset's parents update, as long as they're not missing or currently updating
@dg.asset(automation_condition=dg.AutomationCondition.eager())
def my_eager_asset(): ...

# Condition that materializes an asset once per cron schedule tick
dg.AssetSpec("my_cron_asset", automation_condition=dg.AutomationCondition.on_cron("@daily"))
```

When automation conditions for an asset are met, a [sensor](/guides/sensors) will kick off a run to materialize the asset. This sensor, named `default_automation_condition_sensor`, will be available for each code location and monitor all assets within that location.

To use multiple sensors or change the properties of the default sensor, refer to the `AutomationConditionSensorDefinition` documentation.

TODO: Add something here about the operand reference

:::tip
By default, sensors aren't enabled when first deployed to a Dagster instance.
In the Dagster UI, click **Automation > Sensors** to find and enable the sensor.
:::

## Conditions targeting dependencies

Upstream assets commonly influence downstream materialization decisions. To create automation conditions that target dependencies, use the `AutomationCondition.any_deps_match()` operator. This operator takes an arbitrary `AutomationCondition`, applies it to each upstream asset, and then maps the results to the corresponding downstream partitions.

This operator and `AutomationCondition.all_deps_match()` can be further customized to only target specific sets of upstream assets by using `.allow()` and `.ignore()`.

```python
import dagster as dg

# Monitor updates only from a specific asset group
dg.AutomationCondition.any_deps_match(
    dg.AutomationCondition.newly_updated()
).allow(dg.AssetSelection.groups("metrics")) # Asset group to monitor


# Ignore missing upstream partitions from a specific asset
dg.AutomationCondition.any_deps_match(
    dg.AutomationCondition.missing()
).ignore(dg.AssetSelection.keys("taxi_trips")) # Asset to ignore
```

## Condition labels

To make conditions easier to understand, you can attach labels to sub-conditions, which will then display in the Dagster UI.

Arbitrary string labels can be attached to any node in the `AutomationCondition` tree by using the `with_label()` method, allowing you to describe the purpose of a specific sub-condition:

```python
import dagster as dg

in_progress_or_failed_parents = dg.AutomationCondition.any_deps_match(
    dg.AutomationCondition.in_progress() | dg.AutomationCondition.failed()
).with_label("Any parents in progress or failed")
```

Then, when viewing evaluation results in the UI, the label will display next to the condition:

[TODO]

## Event and status-based conditions

TODO: REWORK THIS SECTION

In some cases, you may want to use statuses and events in your automation conditions:

- **Statuses** are persistent states that are and will be true for some period of time. For example, the `AutomationCondition.missing()` condition will be true only if an asset partition has never been materialized or observed.
- **Events** are transient and reflect something that may only be true for an instant. For example, the `AutomationCondition.newly_updated()` condition will be true only if an asset partition was materialized since the previous evaluation.

Using the `<A>.since(<B>)` operator, you can create conditions that detect if one event has happened more recently than another. Think of this as converting two events to a status - in this case, `A has occurred more recently than B` - as this will stay true for some period of time. This operator becomes true whenever `<A>` is true, and will remain true until `<B>` is also true.

Conversely, it can also be useful to convert statuses to events. For example, the default `eager()` condition ensures that Dagster only tries to materialize a missing asset partition once using the following sub-condition:

```python
from dagster import AutomationCondition

AutomationCondition.missing().newly_true().since(
    AutomationCondition.newly_requested() | AutomationCondition.newly_updated()
)
```

By using the `<A>.newly_true()` operator, you can turn the status of _"being missing"_ into a single event, specifically the point in time where an asset partition entered the _missing_ state. From there, you can ensure that an asset is materialized only once in response to detecting a missing partition.

## Chain runs with conditions

Imagine you have a series of dependent assets, each with an `AutomationCondition.eager()` condition. When you update the first asset in the chain, the desired behavior is typically to have all downstream assets grouped into a single run, rather than executing each asset in order in individual runs.

To create this scenario, use `AutomationCondition.will_be_requested()`. Because each `AutomationCondition` is evaluated in order, you can query if an upstream asset will be requested on the current tick. For example:

```python
import dagster as dg

any_parent_missing = dg.AutomationCondition.any_deps_match(
    dg.AutomationCondition.missing() & ~dg.AutomationCondition.will_be_requested()
)
```

## Next steps