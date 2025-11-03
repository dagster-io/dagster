---
description: Dagster+ branch deployments compare asset definitions in the branch deployment against the asset definitions in the base deployment, helping your team identify how changes in a pull request will impact data assets.
sidebar_position: 7320
title: Change tracking in branch deployments
tags: [dagster-plus-feature]
---

import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';

<DagsterPlus />

Change tracking in branch deployments makes it easier for you and your team to identify how changes in a pull request will impact data assets.

## How it works

Branch deployments compare asset definitions in the branch deployment against the asset definitions in the branch's base deployment. The UI will then mark changed assets accordingly. For example, if the pull request associated with the branch deployment adds a new asset, the UI will display a **New in branch** label indicating the addition.

You can also apply filters to show only new and changed assets in the UI. This makes it easy to understand which assets will be impacted by the changes in the pull request associated with the branch deployment.

:::note

The default behavior is to compare the branch deployment against the **current** state of the [base deployment](/deployment/dagster-plus/deploying-code/branch-deployments/setting-up-branch-deployments#changing-the-base-deployment). Depending on deployment and development cadence, the code deployed in the base deployment can get ahead of the branch causing changes to appear that are from the base getting ahead of the branch.

To address this, the `dagster-cloud` CLI command `branch-deployment create-or-update` has an option `--snapshot-base-condition` that can be set to either `on-create` to snapshot the base only when the branch is first created or `on-update` to refresh the base snapshot anytime the branch is updated.

:::

## Supported change types

Change tracking can detect the following changes to assets:

- [New assets](#new-assets)
- [Code versions](#code-versions)
- [Upstream dependencies](#upstream-dependencies)
- [Partitions definitions](#partitions-definitions)
- [Tags](#tags)
- [Metadata](#metadata)

### New assets

If an asset is new in the branch deployment, the asset will have a **New in branch** label in the asset graph:

![Change tracking new](/images/dagster-plus/deployment/management/managing-deployments/change-tracking-new.png)

### Code versions

If using the `code_version` argument on the asset decorator, change tracking can detect when this value changes.

Some Dagster integrations, like `dagster-dbt`, automatically compute code versions for you. For more information on Dagster code versioning, see [Asset versioning and caching](/guides/build/assets/asset-versioning-and-caching).

<Tabs groupId="changedEntity">
<TabItem value="Asset in the Dagster UI">

In this example, the `customers` asset has a **Changed in branch** label indicating its `code_version` has been changed.

![Change tracking code version](/images/dagster-plus/deployment/management/managing-deployments/change-tracking-code-version.png)

</TabItem>
<TabItem value="Asset definition">

**In the main branch**, we have a `customers` asset with a code version of `v1`:

<CodeExample
  path="docs_snippets/docs_snippets/dagster_cloud/branch_deployments/change_tracking_code_version.py"
  startAfter="start_main_deployment"
  endBefore="end_main_deployment"
  dedent="4"
/>

**In the pull request**, `customers` is modified to change the code version to `v2`:

<CodeExample
  path="docs_snippets/docs_snippets/dagster_cloud/branch_deployments/change_tracking_code_version.py"
  startAfter="start_branch_deployment"
  endBefore="end_branch_deployment"
  dedent="4"
/>

</TabItem>
</Tabs>

### Upstream dependencies

Change tracking can detect when an asset's upstream dependencies have changed, whether they've been added or removed.

:::note

If an asset is marked as having changed dependencies, it means that the <PyObject section="assets" module="dagster" object="AssetKey" pluralize /> defining its upstream dependencies have changed. It doesn't mean that an upstream dependency has new data.

:::

<Tabs groupId="changedEntity">
<TabItem value="Asset in the Dagster UI">

In this example, the `returns` asset has a **Changed in branch** label indicating it has changed dependencies.

![Change tracking dependencies](/images/dagster-plus/deployment/management/managing-deployments/change-tracking-dependencies.png)

</TabItem>
<TabItem value="Asset definition">

**In the main branch**, we have a `returns` asset with a single upstream dependency, `orders`:

<CodeExample
  path="docs_snippets/docs_snippets/dagster_cloud/branch_deployments/change_tracking_dependencies.py"
  startAfter="start_main_deployment"
  endBefore="end_main_deployment"
  dedent="4"
/>

**In the pull request**, we change the upstream dependencies of the `returns` asset to `orders` and `customers`:

<CodeExample
  path="docs_snippets/docs_snippets/dagster_cloud/branch_deployments/change_tracking_dependencies.py"
  startAfter="start_branch_deployment"
  endBefore="end_branch_deployment"
  dedent="4"
/>

</TabItem>
</Tabs>

### Partitions definitions

Change tracking can detect if an asset's <PyObject section="partitions" object="PartitionsDefinition" /> has been changed, whether it's been added, removed, or updated.

<Tabs groupId="changedEntity">
<TabItem value="Asset in the Dagster UI">

In this example, the `weekly_orders` asset has a **Changed in branch** label indicating a changed partitions definition.

![Change tracking partitions](/images/dagster-plus/deployment/management/managing-deployments/change-tracking-partitions.png)

</TabItem>
<TabItem value="Asset definition">

**In the main branch**, we have a `weekly_orders` asset:

<CodeExample
  path="docs_snippets/docs_snippets/dagster_cloud/branch_deployments/change_tracking_partitions_definition.py"
  startAfter="start_main_deployment"
  endBefore="end_main_deployment"
  dedent="4"
/>

**In the pull request**, we updated the <PyObject section="partitions" object="WeeklyPartitionsDefinition" /> to start one year earlier:

<CodeExample
  path="docs_snippets/docs_snippets/dagster_cloud/branch_deployments/change_tracking_partitions_definition.py"
  startAfter="start_branch_deployment"
  endBefore="end_branch_deployment"
  dedent="4"
/>

</TabItem>
</Tabs>

### Tags

Change tracking can detect when an [asset's tags](/guides/build/assets/metadata-and-tags/tags) have changed, whether they've been added, modified, or removed.

<Tabs groupId="changedEntity">
<TabItem value="Asset in the Dagster UI">

In this example, the `fruits_in_stock` asset has a **Changed in branch** label indicating it has changed tags.

![Change tracking tags](/images/dagster-plus/deployment/management/managing-deployments/change-tracking-tags.png)

</TabItem>
<TabItem value="Asset definition">

**In the main branch**, we have a `fruits_in_stock` asset:

<CodeExample
  path="docs_snippets/docs_snippets/dagster_cloud/branch_deployments/change_tracking_tags.py"
  startAfter="start_main_deployment"
  endBefore="end_main_deployment"
  dedent="4"
/>

**In the pull request**, we added the `type: perishable` tag to `fruits_in_stock`:

<CodeExample
  path="docs_snippets/docs_snippets/dagster_cloud/branch_deployments/change_tracking_tags.py"
  startAfter="start_branch_deployment"
  endBefore="end_branch_deployment"
  dedent="4"
/>

</TabItem>
</Tabs>

### Metadata

Change tracking can detect when an [asset's definition metadata](/guides/build/assets/metadata-and-tags) has changed, whether it's been added, modified, or removed.

<Tabs groupId="changedEntity">
<TabItem value="Asset in the Dagster UI">

In this example, the `products` asset has a **Changed in branch** label indicating it has changed metadata.

![Asset definitions tab](/images/dagster-plus/deployment/management/managing-deployments/change-tracking-metadata.png)

</TabItem>
<TabItem value="Asset definition">

**In the main branch**, we have a `products` asset:

<CodeExample
  path="docs_snippets/docs_snippets/dagster_cloud/branch_deployments/change_tracking_metadata.py"
  startAfter="start_main_deployment"
  endBefore="end_main_deployment"
  dedent="4"
/>

**In the pull request**, we update the value of the `expected_columns` metadata on `products`:

<CodeExample
  path="docs_snippets/docs_snippets/dagster_cloud/branch_deployments/change_tracking_metadata.py"
  startAfter="start_branch_deployment"
  endBefore="end_branch_deployment"
  dedent="4"
/>

</TabItem>
</Tabs>
