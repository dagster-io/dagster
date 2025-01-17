---
title: "Change tracking in branch deployments"
sidebar_position: 200
unlisted: true
---

:::note
This guide is applicable to Dagster+.
:::

Branch Deployments Change Tracking makes it easier for you and your team to identify how changes in a pull request will impact data assets. By the end of this guide, you'll understand how Change Tracking works and what types of asset changes can be detected.

## How it works

Branch Deployments compare asset definitions in the branch deployment against the asset definitions in the main deployment. The UI will then mark changed assets accordingly. For example, if the pull request associated with the branch deployment adds a new asset, the UI will display a label indicating the addition.

You can also apply filters to show only new and changed assets in the UI. This makes it easy to understand which assets will be impacted by the changes in the pull request associated with the branch deployment.

{/* **Note:** The default main deployment is `prod`. To configure a different deployment as the main deployment, [create a branch deployment using the dagster-cloud CLI](/dagster-plus/managing-deployments/branch-deployments/using-branch-deployments) and specify it using the optional `--base-deployment-name` parameter. */}
**Note:** The default main deployment is `prod`. To configure a different deployment as the main deployment, [create a branch deployment using the dagster-cloud CLI](/todo) and specify it using the optional `--base-deployment-name` parameter.

## Supported change types

Change Tracking can detect the following changes to assets:

- [New assets](#new-assets)
- [Code versions](#code-versions)
- [Upstream dependencies](#upstream-dependencies)
- [Partitions definitions](#partitions-definitions)
- [Tags](#tags)
- [Metadata](#metadata)

### New assets

If an asset is new in the branch deployment, the asset will have a **New in branch** label in the asset graph:

![Change tracking new](/images/dagster-cloud/managing-deployments/change-tracking-new.png)

### Code versions

If using the `code_version` argument on the asset decorator, Change Tracking can detect when this value changes.

{/* Some Dagster integrations, like `dagster-dbt`, automatically compute code versions for you. For more information on code versions, refer to the [Code versioning guide](/guides/dagster/asset-versioning-and-caching). */}
Some Dagster integrations, like `dagster-dbt`, automatically compute code versions for you. For more information on code versions, refer to the [Code versioning guide](/todo).

<Tabs>
<TabItem value="Asset in the Dagster UI">

In this example, the `customers` asset has a **Changed in branch** label indicating its `code_version` has been changed.

Click the **Asset definition** tab to see the code change that created this label.

![Change tracking code version](/images/dagster-cloud/managing-deployments/change-tracking-code-version.png)

</TabItem>
<TabItem value="Asset definition">

**In the main branch**, we have a `customers` asset with a code version of `v1`:

```python file=/dagster_cloud/branch_deployments/change_tracking_code_version.py startafter=start_main_deployment endbefore=end_main_deployment dedent=4
@asset(code_version="v1")
def customers(): ...
```

**In the pull request**, `customers` is modified to change the code version to `v2`:

```python file=/dagster_cloud/branch_deployments/change_tracking_code_version.py startafter=start_branch_deployment endbefore=end_branch_deployment dedent=4
@asset(code_version="v2")
def customers(): ...
```

</TabItem>
</Tabs>

### Upstream dependencies

Change Tracking can detect when an asset's upstream dependencies have changed, whether they've been added or removed.

**Note**: If an asset is marked as having changed dependencies, it means that the <PyObject section="assets" module="dagster" object="AssetKey" pluralize /> defining its upstream dependencies have changed. It doesn't mean that an upstream dependency has new data.

<Tabs>
<TabItem value="Asset in the Dagster UI">

In this example, the `returns` asset has a **Changed in branch** label indicating it has changed dependencies.

Click the **Asset definition** tab to see the code change that created this label.

![Change tracking dependencies](/images/dagster-cloud/managing-deployments/change-tracking-dependencies.png)

```python file=/dagster_cloud/branch_deployments/change_tracking_dependencies.py startafter=start_branch_deployment endbefore=end_branch_deployment dedent=4
@asset(deps=[orders, customers])
def returns(): ...
```

</TabItem>
</Tabs>

### Partitions definitions

Change Tracking can detect if an asset's <PyObject section="partitions" object="PartitionsDefinition" /> has been changed, whether it's been added, removed, or updated.

<Tabs>
<TabItem value="Asset in the Dagster UI">

In this example, the `weekly_orders` asset has a **Changed in branch** label indicating a changed partitions definition.

Click the **Asset definition** tab to see the code change that created this label.

![Change tracking partitions](/images/dagster-cloud/managing-deployments/change-tracking-partitions.png)

</TabItem>
<TabItem value="Asset definition">

**In the main branch**, we have a `weekly_orders` asset:

```python file=/dagster_cloud/branch_deployments/change_tracking_partitions_definition.py startafter=start_main_deployment endbefore=end_main_deployment dedent=4
@asset(partitions_def=WeeklyPartitionsDefinition(start_date="2024-01-01"))
def weekly_orders(): ...
```

**In the pull request**, we updated the <PyObject section="partitions" object="WeeklyPartitionsDefinition" /> to start one year earlier:

```python file=/dagster_cloud/branch_deployments/change_tracking_partitions_definition.py startafter=start_branch_deployment endbefore=end_branch_deployment dedent=4
@asset(partitions_def=WeeklyPartitionsDefinition(start_date="2023-01-01"))
def weekly_orders(): ...
```

</TabItem>
</Tabs>

### Tags

{/* Change Tracking can detect when an [asset's tags](/concepts/metadata-tags/tags) have changed, whether they've been added, modified, or removed. */}
Change Tracking can detect when an [asset's tags](/todo) have changed, whether they've been added, modified, or removed.

<Tabs>
<TabItem value="Asset in the Dagster UI">

In this example, the `fruits_in_stock` asset has a **Changed in branch** label indicating it has changed tags.

Click the **Asset definition** tab to see the code change that created this label.

![Change tracking tags](/images/dagster-cloud/managing-deployments/change-tracking-tags.png)

</TabItem>
<TabItem value="Asset definition">

**In the main branch**, we have a `fruits_in_stock` asset:

```python file=/dagster_cloud/branch_deployments/change_tracking_tags.py startafter=start_main_deployment endbefore=end_main_deployment dedent=4
@asset(tags={"section": "produce"})
def fruits_in_stock(): ...
```

**In the pull request**, we added the `type: perishable` tag to `fruits_in_stock`:

```python file=/dagster_cloud/branch_deployments/change_tracking_tags.py startafter=start_branch_deployment endbefore=end_branch_deployment dedent=4
@asset(tags={"section": "produce", "type": "perishable"})
def fruits_in_stock(): ...
```

</TabItem>
</Tabs>

### Metadata

{/* Change Tracking can detect when an [asset's definition metadata](/concepts/metadata-tags/asset-metadata#attaching-definition-metadata) has changed, whether it's been added, modified, or removed. */}
Change Tracking can detect when an [asset's definition metadata](/todo) has changed, whether it's been added, modified, or removed.

<Tabs>
<TabItem value="Asset in the Dagster UI">

In this example, the `produtcs` asset has a **Changed in branch** label indicating it has changed metadata.

Click the **Asset definition** tab to see the code change that created this label.

![Change tracking metadata](/images/dagster-cloud/managing-deployments/change-tracking-metadata.png)

</TabItem>
<TabItem value="Asset definition">

**In the main branch**, we have a `products` asset:

```python file=/dagster_cloud/branch_deployments/change_tracking_metadata.py startafter=start_main_deployment endbefore=end_main_deployment dedent=4
@asset(metadata={"expected_columns": ["sku", "price", "supplier"]})
def products(): ...
```

**In the pull request**, we update the value of the `expected_columns` metadata on `products`:

```python file=/dagster_cloud/branch_deployments/change_tracking_metadata.py startafter=start_branch_deployment endbefore=end_branch_deployment dedent=4
@asset(metadata={"expected_columns": ["sku", "price", "supplier", "backstock"]})
def products(): ...
```

</TabItem>
</Tabs>

## Related

{/*
<ArticleList>
  <ArticleListItem
    title="Branch deployments"
    href="/dagster-plus/managing-deployments/branch-deployments"
  ></ArticleListItem>
  <ArticleListItem
    title="Managing Dagster+ deployments"
    href="/dagster-plus/managing-deployments"
  ></ArticleListItem>
  <ArticleListItem title="Dagster Cloud" href="/dagster-plus"></ArticleListItem>
</ArticleList>
*/}
