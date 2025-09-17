---
title: Custom dashboards (Dagster+)
description: Flexibly build dashboards in the Dagster+ asset catalog scoped by tags, teams, owners, or asset groups in order to enable everyone on your team to focus on the assets that matter most to them.
tags: [dagster-plus-feature]
---

import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';

<DagsterPlus />

In the Dagster+ asset catalog, you can use the [asset selection syntax](/guides/build/assets/asset-selection-syntax) to build custom dashboards scoped by tags, teams, owners, asset groups, and more, enabling you to model and observe data products inside of the catalog.

You can create dashboards for your own use or share them with your team. For example, you could create dashboards that:

- Select assets based on ownership to only show those owned by your team
- Select assets based on the asset kind to give insight into the status of your ELT ingestion
- Display assets with a "gold" medallion tag, showing only refined, high-quality data that analysts can use with confidence

In this guide, you'll learn how to create and edit custom dashboards, and share them with others.

:::note

Custom dashboards require **Organization Admin**, **Admin**, or **Editor** permissions on Dagster+.

:::

## Creating dashboards

On any Dagster+ catalog page, you can access the current dashboards, or create a new dashboard with the **Create** button.

![Create button](/images/guides/observe/asset-catalog/create-button.png)

To create a new dashboard, you have two options:

- [Create a new dashboard from scratch](#from-scratch), from the **Create** button.
- [Create a new dashboard from your current asset selection](#from-asset-selection).

### Creating a new dashboard from scratch \{#from-scratch}

1. Click the **Create** button to open the **Create saved selection** modal.
2. In the **Create saved selection** modal, enter an asset selection using the [asset selection syntax](/guides/build/assets/asset-selection-syntax/reference).
3. Give your selection a name and optionally, a description and icon.
4. To share your selection, toggle the **Public selection** switch.
5. Click **Create saved selection** to create the selection.

![Create saved selection modal](/images/guides/observe/asset-catalog/new-selection-modal.png)

### Creating a new dashboard from your current asset selection \{#from-asset-selection}

When viewing the asset list, you can create a new dashboard from your current asset selection.

1. On this page, enter an asset selection using the [asset selection syntax](/guides/build/assets/asset-selection-syntax/reference) in the search box.
2. Click **Save Selection** to the right of the search box. This will open the **Create saved selection** modal with your current asset selection pre-populated.
3. Give your selection a name and optionally, a description and icon.
4. To share your view, toggle the **Public view** switch.
5. Click **Create saved selection** to create the selection.

![Create selection from asset selection](/images/guides/observe/asset-catalog/new-selection-from-asset-list.png)

## Editing, duplicating, or deleting dashboards

1. Navigate to the Asset Catalog.
2. Click on the selection you want to edit, duplicate, or delete.
3. Click the **Actions** dropdown, then select **Edit saved selection**, **Duplicate**, or **Delete**.
4. If editing the selection, note that any active filters will automatically be included in the set of changes. You can also change the selection's name, description, icon, and sharing settings.
5. When finished, click **Save**.

![Edit selection modal](/images/guides/observe/asset-catalog/edit-selection.png)

:::info Coming soon

Job selection syntax and automation selection syntax are coming soon.

:::
