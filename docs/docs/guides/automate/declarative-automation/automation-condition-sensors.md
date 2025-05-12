---
description: Explanation of the AutomationConditionSensorDefinition
sidebar_position: 1000
title: Automation condition sensors
---

All automation conditions must be evaluated by a sensor. If you have any assets with an automation condition in your code location, a sensor with the name `default_automation_condition_sensor` will be created for you automatically.

By default, this sensor will evaluate all automation conditions in your code location, and execute the asset or asset check if the condition is met.

To learn more about sensors, check out the [sensors documentation](/guides/automate/sensors).

### Adding additional sensors

In code locations with large numbers of assets using automation conditions, it may be useful to create additional sensors to evaluate only a subset of the conditions. This has a few benefits:

- Individual evaluations will execute more quickly
- Operational issues with a single sensor will not impact unrelated assets managed by a different sensor
- Ability to toggle automation on and off for more targeted sets of assets

This can be done by creating a <PyObject section="assets" module="dagster" object="AutomationConditionSensorDefinition" /> and passing it to the `sensors` argument of your `Definitions` object:

<CodeExample path="docs_snippets/docs_snippets/concepts/declarative_automation/sensors/multiple_sensors.py" />

When you do this, the `default_automation_condition_sensor` will only target the automation conditions that are not already covered by the additional sensors.

### Default to running

As with other sensor types, all `AutomationConditionSensorDefinitions` will default to the `STOPPED` state when they are first added to a code location. You can modify this by creating a `AutomationConditionSensorDefinition` with the `default_status` argument set to `RUNNING`:

<CodeExample path="docs_snippets/docs_snippets/concepts/declarative_automation/sensors/default_running.py" />

### Adding run tags

It can be useful to add tags to runs produced by a given <PyObject section="assets" module="dagster" object="AutomationConditionSensorDefinition" />. This can be done by passing a `run_tags` argument:

<CodeExample path="docs_snippets/docs_snippets/concepts/declarative_automation/sensors/run_tags.py" />
