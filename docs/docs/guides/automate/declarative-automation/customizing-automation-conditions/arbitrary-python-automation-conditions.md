---
description: Define custom AutomationConditions in Dagster to execute arbitrary Python code to handle complex business logic.
sidebar_position: 600
title: Arbitrary Python automation conditions
---

import Preview from '@site/docs/partials/\_Preview.md';

<Preview />

Some automation use cases require custom business logic that cannot be expressed with off-the-shelf components. In these cases, you can define AutomationConditions which execute arbitrary Python code, and compose them with the built-in conditions.

## Setup

By default, Dagster executes `AutomationConditionSensorDefinitions` in a daemon process that does not have access to your user code. In order to execute arbitrary Python code, you'll need to update this to execute on your user code server. This is the same place that your `@sensor` methods are evaluated.

:::note

Automation condition evaluation can be more resource-intensive than a typical sensor. A limit of 500 assets or checks per sensor is enforced.

:::

import ScaffoldSensor from '@site/docs/partials/\_ScaffoldSensor.md';

<ScaffoldSensor />

To do this, add an automation condition sensor to your definitions with the `use_user_code_server` flag set to `True`:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/sensors/arbitrary_python.py"
  title="src/<project_name>/defs/sensors.py"
/>

This will allow your sensor to target automation conditions containing custom python code.

## Defining a custom condition

You can create your own subclass of `AutomationCondition`, defining the `evaluate()` method. For example, imagine you want to avoid executing anything on a company holiday. To do this, you can first define a condition which detects if it's currently a company holiday:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/sensors/custom_condition.py"
  startAfter="start_custom_condition"
  endBefore="end_custom_condition"
  title="src/<project_name>/defs/sensors.py"
/>

In this example, we build up a subset of the evaluated asset for which this condition is True. We use `EntitySubsets`, rather than a pure `True` / `False` to account for partitioned assets, for which individual partitions may have different results.

In our case, the condition will be applied the same regardless of if it's partitioned or not, so we don't need to have any special logic to differentiate between these cases. If it's not a company holiday, we can return an empty subset (meaning that this condition is not true for any subset of the asset), and if it is a company holiday, we return the `candidate_subset`, which is the subset of the asset that we need to evaluate. This subset shrinks as we filter partitions out using the `&` condition, so if you have an expression `A & B`, and `A` returns the empty subset, then the candidate subset for `B` will be empty as well. This helps avoid expensive computation in cases where we know it won't impact the final output.

Once this condition is defined, you can use this condition as part of a broader expression, for example:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/sensors/custom_condition.py"
  startAfter="start_conditional"
  endBefore="end_conditional"
  title="src/<project_name>/defs/sensors.py"
/>
