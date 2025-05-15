---
description: Guide on automating AssetChecks
sidebar_position: 100
title: Automating asset checks
---

While it is most common to use automation conditions to automate the execution of assets, you can also use them to automate the execution of asset checks. This is particularly helpful in cases where you want to automate your data quality checks independently of the assets they are associated with.

## Recommended automation conditions

The core builtin automation conditions are designed to work with asset checks in addition to assets, and can be used and customized in the same way regardless of whether they are applied to an asset or an asset check.

<Tabs>
  <TabItem value="on_cron" label="on_cron" default>

The <PyObject section="assets" module="dagster" object="AutomationCondition.on_cron" /> will execute an asset check once per cron schedule tick, after all upstream dependencies have updated. This allows you to check the quality of your data on a lower frequency than the asset itself updates, which can be helpful in cases where the data quality check is slow or expensive to execute.

In the following example, at the start of each hour, the above check will start waiting for its associated asset to be updated. Once this happens, the check will immediately be requested. The check will not be requested again until the next hour.

<CodeExample path="docs_snippets/docs_snippets/concepts/declarative_automation/on_cron/basic_check.py" />

**Behavior**

- If at least one upstream partition of _all_ upstream assets has been updated since the previous cron schedule tick, and the downstream check has not yet been requested or executed, it will be requested.
- If all upstream assets **do not** update within the given cron tick, the check will not be requested.

If you would like to customize aspects of this behavior, refer to the [customizing on_cron](customizing-automation-conditions/customizing-on-cron-condition) guide.

</TabItem>

<TabItem value="eager" label="eager">

The <PyObject section="assets" module="dagster" object="AutomationCondition.eager" /> condition allows you to automatically execute an asset check whenever any of its dependencies are updated. This is used to ensure that whenever upstream changes happen, they are automatically checked for data quality issues.

In the following example, the asset check will be automatically requested whenever any of its upstream dependencies are updated.

<CodeExample path="docs_snippets/docs_snippets/concepts/declarative_automation/eager/basic_check.py" />

**Behavior**

If you would like to customize aspects of this behavior, refer to the [customizing eager](customizing-automation-conditions/customizing-eager-condition) guide.

- If _any_ upstream partitions have not been materialized, the downstream check will not be requested.
- If _any_ upstream partitions are currently part of an in-progress run, the downstream check will wait for those runs to complete before being requested.
- If the asset check is already part of an in-progress run, it will wait for that run to complete before being requested.
- If an upstream asset is _observed_, this will only be treated as an update to the upstream asset if the data version has changed since the previous observation.
- If an upstream asset is _materialized_, this will be treated as an update to the upstream asset regardless of the data version of that materialization.

</TabItem>
</Tabs>
