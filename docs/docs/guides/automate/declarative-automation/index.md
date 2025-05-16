---
description: Dagster Declarative Automation is a framework that allows you to access information about events that impact the status of your assets, and the dependencies between them.
keywords:
  - declarative
  - automation
  - schedule
sidebar_position: 20
title: Declarative Automation
---

Declarative Automation is a framework that allows you to access information about events that impact the status of your assets, and the dependencies between them, in order to:

- Ensure you're working with the most up-to-date data.
- Optimize resource usage by only materializing assets or executing checks when needed.
- Precisely define when specific assets should be updated based on the state of other assets.

Declarative Automation has two components:

- An **[automation condition](#automation-conditions)**, set on an asset or asset check, which represents when an individual asset or check should be executed.
- An **[automation condition sensor](#automation-condition-sensors)**, which evaluates automation conditions and launches runs in response to their statuses.

## Using Declarative Automation

To use Declarative Automation, you must:

- [Set automation conditions on assets or asset checks in your code](#setting-automation-conditions-on-assets-and-asset-checks).
- Enable the automation condition sensor in the Dagster UI:
  1. Navigate to **Automation**.
  2. Locate the desired code location.
  3. Toggle on the **default_automation_condition_sensor** sensor.

## Automation conditions

An <PyObject section="assets" module="dagster" object="AutomationCondition" /> on an asset or asset check describe the conditions under which work should be executed.

Dagster provides a few pre-built automation conditions to handle common use cases:

| Name                                         | Condition                                                                                                                                                                                                                                              | Useful for                                                                                               |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------- |
| `AutomationCondition.on_cron(cron_schedule)` | This condition will materialize an asset on a provided `cron_schedule`, after all of its dependencies have been updated.                                                                                                                               | Regularly updating an asset without worrying about the specifics of how its dependencies update.         |
| `AutomationCondition.on_missing()`           | This condition will materialize an asset if all its dependencies have been updated, but the asset itself has not.                                                                                                                                      | Filling in partitioned assets as soon as upstream data is available.                                     |
| `AutomationCondition.eager()`                | This condition will materialize an asset: <ul><li>If the asset has never been materialized before, or</li><li>When the asset's dependencies update, as long as none of the dependencies are currently missing or have an update in progress.</li></ul> | Automatically propagating changes through the asset graph.<br /><br />Ensuring assets remain up to date. |

### Setting automation conditions on assets and asset checks

You can set automation conditions on the <PyObject section="assets" module="dagster" object="asset" decorator /> decorator or on an <PyObject section="assets" module="dagster" object="AssetSpec" /> object:

```python
import dagster as dg

@dg.asset(automation_condition=dg.AutomationCondition.eager())
def my_eager_asset(): ...

AssetSpec("my_cron_asset", automation_condition=AutomationCondition.on_cron("@daily"))
```

You can also set automation conditions on the <PyObject section="asset-checks" module="dagster" object="asset_check" decorator /> decorator or on an <PyObject section="asset-checks" module="dagster" object="AssetCheckSpec" /> object:

```python
@dg.asset_check(asset=dg.AssetKey("orders"), automation_condition=dg.AutomationCondition.on_cron("@daily"))
def my_eager_check() -> dg.AssetCheckResult:
    return dg.AssetCheckResult(passed=True)


dg.AssetCheckSpec(
    "my_cron_check",
    asset=dg.AssetKey("orders"),
    automation_condition=dg.AutomationCondition.on_cron("@daily"),
)
```

### Customizing automation conditions

If the [pre-built automation conditions](#automation-conditions) don't fit your needs, you can build your own. For more information, see "[Customizing automation conditions](customizing-automation-conditions/)".

## Automation condition sensors

The **default_automation_conditition_sensor** monitors all assets and asset checks in a code location in which it is [enabled](#using-declarative-automation). When automation conditions for an asset or asset check in that code location are met, the sensor will execute a run in response.

The sensor's evaluation history will be visible in the UI:

![Default automation sensor evaluations in the Dagster UI](/images/guides/automate/declarative-automation/default-automation-sensor.png)

You can also view a detailed history of each asset's evaluations on the asset's Asset Details page. This allows you to see why an asset was or wasn't materialized at different points in time:

![Automation condition evaluations in the Asset Details page](/images/guides/automate/declarative-automation/evaluations-asset-details.png)

To use multiple sensors or change the properties of the default sensor, see the <PyObject section="assets" module="dagster" object="AutomationConditionSensorDefinition" /> API documentation.
