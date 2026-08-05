---
title: Preventing runs when reactivating a sensor
description: Use a time-aware AutomationCondition to avoid catch-up materializations when re-enabling an automation condition sensor that was off for an extended period.
sidebar_position: 400
---

When you reactivate an automation condition sensor that has been off for an extended period, the default <PyObject section="assets" module="dagster" object="AutomationCondition.eager" /> condition triggers execution for every partition that became eligible while the sensor was off. For high-cardinality or expensive workloads (GPU jobs, large batch transforms), this can produce thousands of unwanted runs the moment the sensor turns back on.

This guide shows how to write a time-aware automation condition that only triggers for newly updated dependencies going forward, ignoring the gap during which the sensor was inactive.

## Preview before reactivating

Before reactivating, click into the **target** section of your automation condition sensor in the Dagster UI to preview which assets and partitions would be triggered. This is the cheapest way to confirm whether the default condition would cause a flood of runs.

## Time-aware automation condition

Replace the default condition with one that gates execution on a cron tick:

<CodeExample
  path="docs_snippets/docs_snippets/guides/automate/declarative_automation/preventing_runs_on_reactivation.py"
  startAfter="start_time_aware_condition"
  endBefore="end_time_aware_condition"
  title="src/<project_name>/defs/automation.py"
/>

This condition triggers only when a dependency was updated _since_ the most recent cron tick, rather than at any point during the sensor's downtime.

Roll the change out incrementally:

1. Apply the condition to a small subset of assets first.
2. Observe behavior for a day or two, watching for unexpected materializations or skips.
3. Apply to the remaining downstream assets once you're confident.

:::warning

Simple conditions like `AutomationCondition.any_deps_updated() & ~AutomationCondition.initial_evaluation()` do not account for time gaps. They will still trigger for partitions added during the inactive period.

:::

## Filtering by date range

For more complex scenarios, define a custom <PyObject section="assets" module="dagster" object="AutomationCondition" /> subclass that filters partitions based on a fixed date range:

<CodeExample
  path="docs_snippets/docs_snippets/guides/automate/declarative_automation/preventing_runs_on_reactivation.py"
  startAfter="start_recent_partitions_only"
  endBefore="end_recent_partitions_only"
  title="src/<project_name>/defs/automation.py"
/>

Use the custom condition in place of the time-aware example above when the cron-tick approach is too coarse for your use case.

## Prevention

When you know a sensor will be deactivated for an extended period, design the condition with a time-aware bound from the start. That way, reactivation does not produce a backlog burst regardless of how long the sensor was off.

## Related documentation

- [Automation condition sensors](/guides/automate/declarative-automation/automation-condition-sensors)
- [Customizing eager](/guides/automate/declarative-automation/customizing-automation-conditions/customizing-eager-condition)
- [Sensors](/guides/automate/sensors)
