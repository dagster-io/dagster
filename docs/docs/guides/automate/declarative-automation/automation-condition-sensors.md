---
description: Explanation of the AutomationConditionSensorDefinition
sidebar_position: 1000
title: Automation condition sensors
---

All automation conditions must be evaluated by a [sensor](/guides/automate/sensors). If you have any assets with an automation condition in your code location, a sensor with the name `default_automation_condition_sensor` will be created for you automatically. You'll need to toggle this sensor on in the UI for your code location under the **Automation** tab.

By default, this sensor will evaluate all automation conditions in your code location, and execute the asset or asset check if the condition is met.

### Adding additional sensors

If you have a code location with a large number of assets using automation conditions, you may want to create additional sensors to evaluate only a subset of the conditions. This has a few benefits:

- Individual evaluations will execute more quickly
- Operational issues with a single sensor will not impact unrelated assets managed by a different sensor
- You can toggle automation on and off for targeted sets of assets

To add an additional sensor, create a <PyObject section="assets" module="dagster" object="AutomationConditionSensorDefinition" /> and pass it to the `sensors` argument of your `Definitions` object:

<CodeExample path="docs_snippets/docs_snippets/concepts/declarative_automation/sensors/multiple_sensors.py" />

When you create new sensors, the `default_automation_condition_sensor` will only target the automation conditions that are not already covered by the additional sensors.

### Default to running

As with other sensor types, all `AutomationConditionSensorDefinitions` will default to the `STOPPED` state when they are first added to a code location. To modify this behavior, create an `AutomationConditionSensorDefinition` with the `default_status` argument set to `RUNNING`:

<CodeExample path="docs_snippets/docs_snippets/concepts/declarative_automation/sensors/default_running.py" />

### Adding run tags

To add tags to runs produced by a given <PyObject section="assets" module="dagster" object="AutomationConditionSensorDefinition" />, pass a `run_tags` argument to the `AutomationConditionSensorDefinition`:

<CodeExample path="docs_snippets/docs_snippets/concepts/declarative_automation/sensors/run_tags.py" />
