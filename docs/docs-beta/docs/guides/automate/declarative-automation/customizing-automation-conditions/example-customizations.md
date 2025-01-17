---
title: "Example customizations"
sidebar_position: 200
---

## Ignoring missing upstream data when using AutomationCondition.eager()

By default, `AutomationCondition.eager()` will not materialize a target if it has any missing upstream data.

If it is expected to have missing upstream data, remove `~AutomationCondition.any_deps_missing()` from the eager policy to allow execution:

{/* TODO convert to <CodeExample> */}
```python file=concepts/declarative_automation/allow_missing_upstreams.py
import dagster as dg

condition = (
    dg.AutomationCondition.eager()
    .without(~dg.AutomationCondition.missing())
    .with_label("eager_allow_missing")
)
```

## Updating older time partitions

### Updating older time partitions with AutomationCondition.eager()

By default, `AutomationCondition.eager()` will only update the latest time partition of an asset.

If updates to historical partitions should result in downstream updates, then this sub-condition can be removed:

{/* TODO convert to <CodeExample> */}
```python file=concepts/declarative_automation/update_older_time_partitions.py
from dagster import AutomationCondition

condition = AutomationCondition.eager().without(
    AutomationCondition.in_latest_time_window(),
)
```

### Updating older time partitions with AutomationCondition.on_cron()

By default, `AutomationCondition.on_cron()` will target the latest time partition of an asset.

If you instead want to update partitions on a delay, then you can replace this condition with one that targets a partition that has a specific lag from the latest time window:

{/* TODO convert to <CodeExample> */}
```python file=concepts/declarative_automation/update_specific_older_partition.py
from datetime import timedelta

from dagster import AutomationCondition

five_days_ago_condition = AutomationCondition.in_latest_time_window(
    timedelta(days=5)
) & ~AutomationCondition.in_latest_time_window(timedelta(days=4))

condition = AutomationCondition.eager().replace(
    "in_latest_time_window", five_days_ago_condition
)
```

## Ignoring dependencies when using AutomationCondition.on_cron()

By default, `AutomationCondition.on_cron()` will wait for all upstream dependencies to be updated before executing the asset it's attached to. In some cases, it can be useful to ignore some upstream dependencies in this calculation. This can be done by passing in an <PyObject section="assets" module="dagster" object="AssetSelection" /> to be ignored:

{/* TODO convert to <CodeExample> */}
```python file=concepts/declarative_automation/ignore_dependencies_cron.py
import dagster as dg

all_deps_except_foo_updated = dg.AutomationCondition.all_deps_updated_since_cron(
    "@hourly"
).ignore(dg.AssetSelection.assets("foo"))

condition = (
    dg.AutomationCondition.on_cron("@hourly").without(
        dg.AutomationCondition.all_deps_updated_since_cron("@hourly")
    )
) & all_deps_except_foo_updated
```

Alternatively, you can pass in an <PyObject section="assets" module="dagster" object="AssetSelection" /> to be allowed:

{/* TODO convert to <CodeExample> */}
```python file=concepts/declarative_automation/allow_dependencies_cron.py
import dagster as dg

group_abc_updated = dg.AutomationCondition.all_deps_updated_since_cron("@hourly").allow(
    dg.AssetSelection.groups("abc")
)

condition = (
    dg.AutomationCondition.on_cron("@hourly").without(
        dg.AutomationCondition.all_deps_updated_since_cron("@hourly")
    )
) & group_abc_updated
```

## Waiting for all blocking asset checks to complete before executing

The `AutomationCondition.all_deps_blocking_checks_passed()` condition becomes true after all upstream blocking checks have passed.

This can be combined with built-in conditions such as `AutomationCondition.on_cron()` and `AutomationCondition.eager()` to ensure that your asset does not execute if upstream data is in a bad state:

{/* TODO convert to <CodeExample> */}
```python file=concepts/declarative_automation/blocking_checks_condition.py
import dagster as dg

condition = (
    dg.AutomationCondition.eager()
    & dg.AutomationCondition.all_deps_blocking_checks_passed()
)
```
