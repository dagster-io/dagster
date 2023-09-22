---
title: 'Lesson 5: Code locations in the Dagster UI'
module: 'dagster_essentials'
lesson: '5'
---

# Code locations in the Dagster UI

In this section, we’ll walk you through code locations in the Dagster UI.

{% table %}

- Viewing all code locations

---

- {% width="60%; fixed" %}
  To view code locations in the Dagster UI, click **Deployments** in the top navigation. The list of code locations will be under the code locations tab, with the status, last updated and other information.

  By default, code locations are named using the name of the module loaded by Dagster. In this case, that’s `dagster_university`, which is the name of the folder (or module) the project is contained in.

- ![The Code locations tab in the Dagster UI, showing the project's dagster_university code location](/images/dagster-essentials/lesson-5/code-locations-ui.png) {% rowspan=2 %}

{% /table %}

{% table %}

- Viewing code location loading errors

---

- {% width="60%; fixed" %}
  If something is wrong with your code location, the status will appear as **Failed.**

  Click **View Error** to view the stack trace and troubleshoot issues.

- ![Code locations will have a status of Failed if there's an issue](/images/dagster-essentials/lesson-5/code-location-error-ui.png) {% rowspan=2 %}

{% /table %}

{% table %}

- Reloading definitions

---

- {% width="60%; fixed" %}
  As you add or change definitions in your project, you may need to refresh the code location. When you reload definitions, you’re telling Dagster to retrieve and use the last saved version of your project’s files.

  You can reload definitions in the UI by:

  - Navigating to **Deployment > Code locations** and clicking the **Reload** button next to a code location
  - Navigating to the **Global Asset Lineage** page and clicking the **Reload definitions page**

- ![The Reload button in the Code locations tab in the Dagster UI](/images/dagster-essentials/lesson-5/code-locations-reload.png) {% rowspan=2 %}

{% /table %}
