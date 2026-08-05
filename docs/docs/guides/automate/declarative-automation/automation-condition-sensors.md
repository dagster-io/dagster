---
description: Explanation of the AutomationConditionSensorDefinition
sidebar_position: 200
title: Automation condition sensors
---

All automation conditions must be evaluated by a [sensor](/guides/automate/sensors). If you have any assets with an automation condition in your code location, a sensor with the name `default_automation_condition_sensor` will be created for you automatically. You'll need to toggle this sensor on in the UI for your code location under the **Automation** tab.

By default, this sensor will evaluate all automation conditions in your code location, and execute the asset, asset check, or asset job if the condition is met. For more information about asset jobs with automation conditions, see [Automating jobs](/guides/automate/declarative-automation/automating-jobs).

The `default_automation_condition_sensor` is created when all of the following are true:

- The code location contains at least one asset, asset check, or asset job with an `AutomationCondition` (or legacy `AutoMaterializePolicy`).
- You're on Dagster 1.5 or later.
- The code location loads and registers definitions successfully.

If you're migrating from `AutoMaterializePolicy`, you must set `use_sensors: true` in your `auto_materialize` configuration. Toggling sensors on in the UI alone is not enough; without `use_sensors: true`, the sensor will not drive automation. If a default sensor is missing, verify the conditions above before troubleshooting further.

### Adding additional sensors

If you have a code location with a large number of assets using automation conditions, you may want to create additional sensors to evaluate only a subset of the conditions. This has a few benefits:

- Individual evaluations will execute more quickly
- Operational issues with a single sensor will not impact unrelated assets managed by a different sensor
- You can toggle automation on and off for targeted sets of assets

To add an additional sensor, create a <PyObject section="assets" module="dagster" object="AutomationConditionSensorDefinition" /> and pass it to the `sensors` argument of your `Definitions` object:

<CodeExample
  path="docs_snippets/docs_snippets/guides/automate/declarative_automation/sensors/multiple_sensors.py"
  title="src/<project_name>/defs/sensors.py"
/>

When you create new sensors, the `default_automation_condition_sensor` will only target the automation conditions that are not already covered by the additional sensors.

:::note

Asset jobs with automation conditions are always evaluated by the `default_automation_condition_sensor` — additional sensors cannot target jobs. For more information, see [Automating jobs](/guides/automate/declarative-automation/automating-jobs).

:::

### Default to running

As with other sensor types, all `AutomationConditionSensorDefinitions` will default to the `STOPPED` state when they are first added to a code location. To modify this behavior, create an `AutomationConditionSensorDefinition` with the `default_status` argument set to `RUNNING`:

<CodeExample
  path="docs_snippets/docs_snippets/guides/automate/declarative_automation/sensors/default_running.py"
  title="src/<project_name>/defs/sensors.py"
/>

### Adding run tags

To add tags to runs produced by a given <PyObject section="assets" module="dagster" object="AutomationConditionSensorDefinition" />, pass a `run_tags` argument to the `AutomationConditionSensorDefinition`:

<CodeExample
  path="docs_snippets/docs_snippets/guides/automate/declarative_automation/sensors/run_tags.py"
  title="src/<project_name>/defs/sensors.py"
/>
