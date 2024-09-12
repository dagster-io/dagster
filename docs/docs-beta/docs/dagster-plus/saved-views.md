---
title: "Saving asset filters as catalog views"
displayed_sidebar: "dagsterPlus"
---

# Saving asset filters as catalog views

Catalog views enable you to filter down your view of the Dagster Asset catalog in Dagster+, allowing you to toggle between sets of assets that you care about most.

You can save catalog views for your own use or share them with your team. For example, you could create views that:

- Filter assets based on ownership to only show those owned by your team
- Filter assets based on the asset kind to give insight into the status of your ELT ingestion
- Display assets with a "gold" medallion tag, showing only refined, high-quality data that analysts can use with confidence analysts can use with confidence

In this guide, you'll learn how to create, access, and share catalog views with others.

<details>
<summary>Prerequisites</summary>

- **Organization Admin**, **Admin**, or **Editor** permissions on Dagster+
- Familiarity with [Assets](/concepts/assets) and [Asset metadata](/guides/metadata)

</details>




## Create catalog views

To view the Dagster+ Asset catalog, use the **Catalog** button on the top navigation.

In any Dagster+ catalog page, you can access the current catalog view, or create a new catalog view with the catalog view button on the top left of the screen. By default, this button is labeled **All assets**, and has a globe icon.

![Screenshot of the catalog view dropdown](/img/placeholder.svg)

To create a new catalog view, you have two options:
1. Create a new catalog view from scratch, from the catalog view menu.
2. Create a new catalog view from your current set of filters.

### Create a new catalog view from scratch

1. Click the catalog view button to open the catalog view menu. From here, click the **New** button.
2. Give the view a name and optionally, a description and icon.
3. Click **Add filters** to select filters to apply to the view. Filters can select a subset of assets based on their metadata, tags, kinds, owners, asset groups, or other properties.
4. To make the view shareable, toggle the **Public view** switch.
5. Click **Create view** to create the view.

![Screenshot of catalog view customization UI](/img/placeholder.svg)

Give your view a name and optionally a description and icon. Next, you can select one or more filters to apply to your view by clicking the "Add filters" button. Filters can select a subset of assets based on their metadata, tags, kinds, owners, asset groups, or other properties.

### Create a new catalog view from your current set of filters

When viewing the global asset lineage or asset list, you can create a new catalog view from your current set of filters.

1. On these pages, select one or more asset filters.
2. Click **Create new catalog view**, located near the top right of the page. This will open the catalog view creation dialog with your current filters pre-populated.
3. Give the view a name and optionally, a description and icon.
4. To make the view shareable, toggle the **Public view** switch.
5. Click **Create view** to create the view.

## Edit, duplicate, or delete catalog views

1. Click the catalog view button to open the catalog view menu.
2. Search for the view you want to edit, duplicate, or delete.
3. Click the **three dot menu** to the right of the view to display available options.
4. If modifying the view, note that any active filters will automatically be included in the set of changes. You can also change the view's name, description, icon, and sharing settings. 5. When finished, click **Save changes**.
