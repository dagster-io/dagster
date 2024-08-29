---
title: "Tailoring your search experience with catalog views"
displayed_sidebar: "dagsterPlus"
sidebar_label: "Customizing the catalog with views"
---

# Tailoring your search experience with catalog views

Catalog views enable you to filter down your view of the Dagster Asset catalog in Dagster+. You can save catalog views for your own use, or share them with your team.

This guide covers how to create, access, and share catalog views with others.


<details>
<summary>Prerequisites</summary>

- A Dagster+ organization
- Familiarity with [Assets](/concepts/assets)

</details>


## Tailored catalog views

Catalog views allow you to toggle between sets of assets that you care about most. Here are a few examples of how your team might use catalog views:

- **Team view**: A view that filters assets based on ownership to show only the assets owned by your team.
- **Ingestion view**: A view that filters assets based on the asset kind to give insight into the status of your ELT ingestion.
- **Gold medallion view**: A view which displays assets that have a "gold" medallion tag, showing only refined, high-quality data that analysts can use with confidence.


## Create catalog views

In any Dagster+ catalog page, you can access the current catalog view, or create a new catalog view with the catalog view button on the top left of the screen. By default, this button is labeled **All assets** and has a globe icon.

To create a new catalog view, you have two options:
1. Create a new catalog view from scratch, from the catalog view menu.
2. Create a new catalog view from your current set of filters.

### Create a new catalog view from scratch

1. Click the catalog view button to open the catalog view menu. From here, click the **New** button.
2. Give the view a name and optionally, a description and icon.
3. Click **Add filters** to select filters to apply to the view. Filters can select a subset of assets based on their metadata, tags, kinds, owners, asset groups, or other properties.
4. To make the view shareable, toggle the **Public view** switch.
5. Click **Create view** to create the view.

### Create a new catalog view from your current filters

When viewing the global asset lineage or asset list, you can create a new catalog view from your current set of filters. 

1. On these pages, select one or more asset filters. 
2. Click **Create new catalog view**, located near the top right of the page. This will open the catalog view creation dialog with your current filters pre-populated.
3. Give the view a name and optionally, a description and icon.
4. To make the view shareable, toggle the **Public view** switch.
5. Click **Create view** to create the view.

## Edit, duplicate, or delete catalog views

To edit, duplicate, or delete a catalog view, navigate to the catalog view menu by clicking the catalog view button on the top left of the screen. From here, you can search for the view you want to modify, duplicate, or delete. Use the three-dot menu on the right side of the view to show the available actions.

When editing a catalog view, any active filters will automatically be included in the set of changes. You can modify the view's name, description, icon, and sharing settings. To save your changes, click "Save changes".
