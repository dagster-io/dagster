---
description: Example use cases for customizing AutomationCondition.on_cron()
sidebar_position: 100
title: Customizing on_cron
---

import ScaffoldAsset from '@site/docs/partials/\_ScaffoldAsset.md';

<ScaffoldAsset />

## Ignoring dependencies

By default, <PyObject module="dagster" section="assets" object="AutomationCondition.on_cron" displayText="AutomationCondition.on_cron()" /> will wait for all upstream dependencies to be updated before executing the asset it's attached to. In some cases, it can be useful to ignore some upstream dependencies in this calculation. This can be done by passing in an <PyObject section="assets" module="dagster" object="AssetSelection" /> to be ignored:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/on_cron/ignore_dependencies.py"
  title="src/<project_name>/defs/assets.py"
/>

Alternatively, you can pass in an <PyObject section="assets" module="dagster" object="AssetSelection" /> to be allowed:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/on_cron/allow_dependencies.py"
  title="src/<project_name>/defs/assets.py"
/>

## Waiting for all blocking asset checks to complete before executing

The `AutomationCondition.all_deps_blocking_checks_passed()` condition becomes true after all upstream blocking checks have passed.

This can be combined with `AutomationCondition.on_cron()` to ensure that your asset does not execute if upstream data is failing data quality checks:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/on_cron/blocking_checks_condition.py"
  title="src/<project_name>/defs/assets.py"
/>

## Executing later than upstream assets

By default, a single cron schedule determines the point in time that an asset starts looking for upstream data, as well as the earliest point that it would be valid to execute that asset. Sometimes, it can be useful to start looking for upstream updates at an earlier time than the cron schedule on which you want the asset to execute.

This can be achieved by modifying the `AutomationCondition.all_deps_updated_since_cron()` sub-condition. In this example, we want our asset to materialize at 9:00 AM each day, but start looking for upstream data as soon as the midnight boundary is passed:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/on_cron/multiple_cron_schedules.py"
  title="src/<project_name>/defs/assets.py"
/>

## Updating older time partitions

By default, `AutomationCondition.on_cron()` will target the latest time partition of an asset.

If you instead want to update partitions on a delay, then you can replace this condition with one that targets a partition that has a specific lag from the latest time window:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/on_cron/update_specific_older_partition.py"
  title="src/<project_name>/defs/assets.py"
/>
