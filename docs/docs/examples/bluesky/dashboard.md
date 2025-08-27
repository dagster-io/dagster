---
title: Dashboard
description: Managing dashboard objects
last_update:
  author: Dennis Hume
sidebar_position: 50
---

The final step in our pipeline is configuring our dashboard. Including the presentation layer in our project helps ensure the full lineage of our project and ensures that data will be updated as soon as it is transformed. This is much easier than trying to coordinate schedules across services.

For this example we will use [Power BI](https://www.microsoft.com/en-us/power-platform/products/power-bi) but Dagster has native support for BI tools such as Tableau, Looker and Sigma. And like the native dbt resource, we will not need to add much code to include our PowerBI assets.

First we will initialize the `PowerBIWorkspace` resource which allows Dagster to communicate with Power BI.

<CodeExample
  path="docs_projects/project_atproto_dashboard/src/project_atproto_dashboard/defs/dashboard.py"
  language="python"
  startAfter="start_powerbi"
  endBefore="end_powerbi"
  title="src/project_atproto_dashboard/defs/dashboard.py"
/>

Then, like dbt, we will define a translator. This time since the Power BI assets live downstream of our dbt models, we will map the Power BI assets to those model assets.

<CodeExample
  path="docs_projects/project_atproto_dashboard/src/project_atproto_dashboard/defs/dashboard.py"
  language="python"
  startAfter="start_dbt"
  endBefore="end_dbt"
  title="src/project_atproto_dashboard/defs/dashboard.py"
/>

## Definition merge

With the dashboard assets set, we have all three layers of the end-to-end project ready to go. We can now initialize and define all the resources used by the assets across the three layers of the project.

<CodeExample
  path="docs_projects/project_atproto_dashboard/src/project_atproto_dashboard/defs/resources.py"
  language="python"
  startAfter="start_def"
  endBefore="end_def"
  title="src/project_atproto_dashboard/defs/resources.py"
/>

Defining our `Definitions` this way will automatically load all the assets defined in the project. The only things that need to be set explicitly are the resources used by those assets.

You can see that organizing your project into domain specific definitions leads to a clean definition. We do this with our own [internal Dagster project](https://github.com/dagster-io/dagster-open-platform/blob/main/dagster_open_platform/definitions.py) that combines over a dozen domain specific definitions for the various tools and services we use.
