---
title: "Example customizations"
sidebar_position: 200
---

## Ignoring missing upstream data when using AutomationCondition.eager()

By default, `AutomationCondition.eager()` will not materialize a target if it has any missing upstream data.

If it is expected to have missing upstream data, remove `~AutomationCondition.any_deps_missing()` from the eager policy to allow execution:


<CodeExample path="concepts/declarative_automation/allow_missing_upstreams.py" language="Python" />

## Require data version updates when using AutomationCondition.eager()

By default, `AutomationCondition.eager()` will treat a dependency as updated whenever it materializes, regardless of if that materialization resulted in a change to the data version of the asset. If you want to ignore updates that do not change the data version, you can do so by replacing `AutomationCondition.newly_updated()` with `AutomationCondition.data_version_changed()`:

<CodeExample path="concepts/declarative_automation/require_data_version_update.py" language="Python" />

## Updating older time partitions

### Updating older time partitions with AutomationCondition.eager()

By default, `AutomationCondition.eager()` will only update the latest time partition of an asset.

If updates to historical partitions should result in downstream updates, then this sub-condition can be removed:

<CodeExample path="concepts/declarative_automation/update_older_time_partitions.py" language="Python" />

### Updating older time partitions with AutomationCondition.on_cron()

By default, `AutomationCondition.on_cron()` will target the latest time partition of an asset.

If you instead want to update partitions on a delay, then you can replace this condition with one that targets a partition that has a specific lag from the latest time window:

<CodeExample path="concepts/declarative_automation/update_specific_older_partition.py" language="Python" />

## Ignoring dependencies when using AutomationCondition.on_cron()

By default, `AutomationCondition.on_cron()` will wait for all upstream dependencies to be updated before executing the asset it's attached to. In some cases, it can be useful to ignore some upstream dependencies in this calculation. This can be done by passing in an <PyObject section="assets" module="dagster" object="AssetSelection" /> to be ignored:

<CodeExample path="concepts/declarative_automation/ignore_dependencies_cron.py" language="Python" />

Alternatively, you can pass in an <PyObject section="assets" module="dagster" object="AssetSelection" /> to be allowed:

<CodeExample path="concepts/declarative_automation/allow_dependencies_cron.py" language="Python" />

### Wait for all blocking asset checks to complete before executing

The `AutomationCondition.all_deps_blocking_checks_passed()` condition becomes true after all upstream blocking checks have passed. This can be combined with built-in conditions such as `AutomationCondition.on_cron()` and `AutomationCondition.eager()` to ensure that your asset does not execute if upstream data is in a bad state:


<CodeExample path="concepts/declarative_automation/blocking_checks_condition.py" language="Python" />