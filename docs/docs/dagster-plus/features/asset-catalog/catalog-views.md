---
title: 'Catalog views'
sidebar_position: 100
---

Catalog views enable you to filter down your view of the Dagster Asset catalog in Dagster+ with the [asset selection syntax](/guides/build/assets/asset-selection-syntax/), allowing you to toggle between sets of assets that you care about most.

You can save catalog views for your own use or share them with your team. For example, you could create views that:

- Select assets based on ownership to only show those owned by your team
- Select assets based on the asset kind to give insight into the status of your ELT ingestion
- Display assets with a "gold" medallion tag, showing only refined, high-quality data that analysts can use with confidence

In this guide, you'll learn how to create, access, and share catalog views with others.

:::note

Catalog views require **Organization Admin**, **Admin**, or **Editor** permissions on Dagster+.

:::

## Creating catalog views

On any Dagster+ Catalog page, you can access the current catalog view, or create a new catalog view with the catalog view dropdown at the top left of the screen. By default, this button is labeled **All assets**, and has a globe icon.

![Screenshot of the catalog view dropdown](/images/dagster-plus/features/asset-catalog/catalog-views.png)

To create a new catalog view, you have two options:

- [Create a new catalog view from scratch](#creating-a-new-catalog-view-from-scratch), from the catalog view menu.
- [Create a new catalog view from your current asset selection](#creating-a-new-catalog-view-from-your-current-asset-selection).

### Creating a new catalog view from scratch

1. Click the catalog view dropdown to open the catalog view menu. From here, click the **New** button.
2. In the search box, enter an asset selection using the [asset selection syntax](/guides/build/assets/asset-selection-syntax/reference).
3. Give your view a name and optionally, a description and icon.
4. To share your view, toggle the **Public view** switch.
5. Click **Create view** to create the view.

![Screenshot of new catalog view modal](/images/dagster-plus/features/asset-catalog/new-catalog-view.png)

### Creating a new catalog view from your current asset selection

When viewing the global asset lineage or asset list, you can create a new catalog view from your current asset selection.

1. On these pages, enter an asset selection using the [asset selection syntax](/guides/build/assets/asset-selection-syntax/reference) in the search box.
2. Click the **globe icon** located to the right of the search box. This will open the catalog view creation dialog with your current asset selection pre-populated.
3. Give your view a name and optionally, a description and icon.
4. To share your view, toggle the **Public view** switch.
5. Click **Create view** to create the view.

![Screenshot of creating catalog view from asset selection](/images/dagster-plus/features/asset-catalog/new-catalog-view-from-asset-list-page.png)

## Editing, duplicating, or deleting catalog views

1. Click the **catalog view** button to open the catalog view menu.
2. Search for the view you want to edit, duplicate, or delete.
3. Click the **three dot menu** to the right of the view to display available options.
4. If modifying the view, note that any active filters will automatically be included in the set of changes. You can also change the view's name, description, icon, and sharing settings.
5. When finished, click **Save changes**.

![Screenshot of editing catalog views](/images/dagster-plus/features/asset-catalog/edit-catalog-view.png)
