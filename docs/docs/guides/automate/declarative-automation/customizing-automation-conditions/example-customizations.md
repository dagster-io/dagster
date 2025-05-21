---
description: Example use cases for Dagster Declarative Automation.
sidebar_position: 200
title: Example customizations
---

## Ignoring missing upstream data when using AutomationCondition.eager()

By default, `AutomationCondition.eager()` will not materialize a target if it has any missing upstream data.

If it is expected to have missing upstream data, remove `~AutomationCondition.any_deps_missing()` from the eager policy to allow execution:

<CodeExample path="docs_snippets/docs_snippets/concepts/declarative_automation/allow_missing_upstreams.py" />

## Updating older time partitions

### Updating older time partitions with AutomationCondition.eager()

By default, `AutomationCondition.eager()` will only update the latest time partition of an asset.

If updates to historical partitions should result in downstream updates, then this sub-condition can be removed:

<CodeExample path="docs_snippets/docs_snippets/concepts/declarative_automation/update_older_time_partitions.py" />

### Updating older time partitions with AutomationCondition.on_cron()

By default, `AutomationCondition.on_cron()` will target the latest time partition of an asset.

If you instead want to update partitions on a delay, then you can replace this condition with one that targets a partition that has a specific lag from the latest time window:

<CodeExample path="docs_snippets/docs_snippets/concepts/declarative_automation/update_specific_older_partition.py" />

## Ignoring dependencies when using AutomationCondition.on_cron()

By default, `AutomationCondition.on_cron()` will wait for all upstream dependencies to be updated before executing the asset it's attached to. In some cases, it can be useful to ignore some upstream dependencies in this calculation. This can be done by passing in an <PyObject section="assets" module="dagster" object="AssetSelection" /> to be ignored:

<CodeExample path="docs_snippets/docs_snippets/concepts/declarative_automation/ignore_dependencies_cron.py" />

Alternatively, you can pass in an <PyObject section="assets" module="dagster" object="AssetSelection" /> to be allowed:

<CodeExample path="docs_snippets/docs_snippets/concepts/declarative_automation/allow_dependencies_cron.py" />

## Waiting for all blocking asset checks to complete before executing

The `AutomationCondition.all_deps_blocking_checks_passed()` condition becomes true after all upstream blocking checks have passed.

This can be combined with built-in conditions such as `AutomationCondition.on_cron()` and `AutomationCondition.eager()` to ensure that your asset does not execute if upstream data is in a bad state:

<CodeExample path="docs_snippets/docs_snippets/concepts/declarative_automation/blocking_checks_condition.py" />

## Ignoring runs from non-automated runs when using AutomationCondition.eager()

By default, `AutomationCondition.eager()` materializes a target whenever any upstream event occurs, regardless of the source of that event.

It can be useful to ignore runs of certain types when determining if an upstream asset should be considered "updated". This can be done using `AutomationCondition.executed_with_tags()` to filter updates for runs with tags matching particular keys:

<CodeExample path="docs_snippets/docs_snippets/concepts/declarative_automation/executed_with_tags_condition.py" />
