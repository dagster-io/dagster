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
  path="docs_projects/project_atproto_dashboard/project_atproto_dashboard/dashboard/definitions.py"
  language="python"
  startAfter="start_powerbi"
  endBefore="end_powerbi"
/>

Then, like dbt, we will define a translator. This time since the Power BI assets live downstream of our dbt models, we will map the Power BI assets to those model assets.

<CodeExample
  path="docs_projects/project_atproto_dashboard/project_atproto_dashboard/dashboard/definitions.py"
  language="python"
  startAfter="start_dbt"
  endBefore="end_dbt"
/>

Finally we define the definition for our dashboard assets and Power BI resource.

<CodeExample
  path="docs_projects/project_atproto_dashboard/project_atproto_dashboard/dashboard/definitions.py"
  language="python"
  startAfter="start_def"
  endBefore="end_def"
/>

## Definition merge

With the dashboard definition set, we have all three layers of the end-to-end project ready to go. We can now define a single definition which will be the definition used in our code location.

<CodeExample
  path="docs_projects/project_atproto_dashboard/project_atproto_dashboard/definitions.py"
  language="python"
  startAfter="start_def"
  endBefore="end_def"
/>

You can see that organizing your project into domain specific definitions leads to a clean definition. We do this with our own [internal Dagster project](https://github.com/dagster-io/dagster-open-platform/blob/main/dagster_open_platform/definitions.py) that combines over a dozen domain specific definitions for the various tools and services we use.
