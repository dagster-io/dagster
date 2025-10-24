---
description: Example use cases for customizing AutomationCondition.eager()
sidebar_position: 300
title: Customizing eager
---

import ScaffoldAsset from '@site/docs/partials/\_ScaffoldAsset.md';

<ScaffoldAsset />

## Ignoring missing upstream data

By default, <PyObject module="dagster" section="assets" object="AutomationCondition.eager" displayText="AutomationCondition.eager()" /> will not materialize a target if it has any missing upstream data.

If it is expected to have missing upstream data, remove `~AutomationCondition.any_deps_missing()` from the eager policy to allow execution:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/eager/allow_missing_upstreams.py"
  title="src/<project_name>/defs/assets.py"
/>

## Updating older time partitions

By default, `AutomationCondition.eager()` will only update the latest time partition of an asset.

If updates to historical partitions should result in downstream updates, then this sub-condition can be removed:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/eager/update_older_time_partitions.py"
  title="src/<project_name>/defs/assets.py"
/>

## Waiting for all blocking asset checks to complete before executing

The `AutomationCondition.all_deps_blocking_checks_passed()` condition becomes true after all upstream blocking checks have passed.

This can be combined with `AutomationCondition.eager()` to ensure that your asset does not execute if upstream data is failing data quality checks:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/eager/blocking_checks_condition.py"
  title="src/<project_name>/defs/assets.py"
/>

## Ignoring materializations from manual runs

By default, `AutomationCondition.eager()` materializes a target whenever any upstream event occurs, regardless of the source of that event.

It can be useful to ignore runs of certain types when determining if an upstream asset should be considered "updated". This can be done using `AutomationCondition.any_new_update_has_run_tags()` to filter updates for runs with tags matching particular keys:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/eager/executed_with_tags_condition.py"
  title="src/<project_name>/defs/assets.py"
/>

## Ignoring dependencies

By default, `AutomationCondition.eager()` will trigger a target if any upstream dependencies are updated.

In some cases, it can be useful to ignore some upstream dependencies that should not trigger downstream compute. This can be done by passing in an <PyObject section="assets" module="dagster" object="AssetSelection" /> to be ignored:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/eager/ignore_dependencies.py"
  title="src/<project_name>/defs/assets.py"
/>
Alternatively, you can pass in an <PyObject section="assets" module="dagster" object="AssetSelection" /> to be allowed:
<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/eager/allow_dependencies.py"
  title="src/<project_name>/defs/assets.py"
/>

## Respecting data versioning

By default, `AutomationCondition.eager()` will consider any upstream asset to be "updated" if it has been materialized, regardless of the data version of that materialization.

If you want to only consider upstream assets to be "updated" if the data version has changed, you can use `AutomationCondition.data_version_changed()`:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/eager/data_version_changed_condition.py"
  title="src/<project_name>/defs/assets.py"
/>

## Combining scheduled and dependency-driven execution

For more complex automation patterns, you can combine scheduled execution with dependency-driven updates. This pattern ensures regular execution on a schedule while also allowing for more frequent updates when dependencies change, with additional safety checks:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/declarative_automation/eager/combined.py"
  title="src/<project_name>/defs/assets.py"
/>

The `custom_condition` in this example will execute the target asset in two scenarios:

1. **Scheduled execution**: Runs on the specified cron schedule (every 5 minutes in this example)
2. **Dependency-driven execution**: Runs when upstream dependencies are updated, but only if:
   - The asset was successfully updated since the last scheduled run
   - No upstream dependencies are missing
   - No upstream dependencies are currently in progress

This approach is particularly useful for assets that need guaranteed regular execution ,but should also respond quickly to upstream changes, while avoiding execution during problematic states.
