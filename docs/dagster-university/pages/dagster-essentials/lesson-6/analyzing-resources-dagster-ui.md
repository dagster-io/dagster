---
title: 'Lesson 6: Analyzing resource usage using the Dagster UI'
module: 'dagster_essentials'
lesson: '6'
---

# Analyzing resource usage using the Dagster UI

We briefly mentioned earlier the **Resources** tab on the **Overview** page. We only spent a little bit of time going over it as this page was not previously helpful. Now that your assets are using the database resource, you can use it to understand more about your resources.

{% table %}

- Accessing the Resources tab

---

- {% width="60%" %}

  1. In the Dagster UI, click **Deployment**, then the `dagster_university` code location.
  2. Next, click the **Resources** tab. Now that the assets have been updated to use the `database` resource, the **Uses** column now displays **4.**
  3. In the **Name** column, click `database`.

- ![The Resources tab for the dagster_university code location](/images/dagster-essentials/lesson-6/resources-tab-2.png) {% rowspan=2 %}

{% /table %}

{% table %}

- Viewing a resource's details

---

- {% width="60%" %}
  This page contains details about the resource, such as the type of resource it is and how it’s configured.

- ![The Configuration tab of the Resource details page](/images/dagster-essentials/lesson-6/resource-details.png) {% rowspan=2 %}

{% /table %}

{% table %}

- Viewing resource usage

---

- {% width="60%" %}
  Click the **Uses** tab to view information about the assets that use the resource.

  This page is essential in understanding what resources are available and how they’re used. Some common use cases for this info include:

  - Identifying potential impacts of a database migration
  - Investigating increases in service costs and trying to track down where the growth is coming from

- ![The Uses tab of the Resource details page](/images/dagster-essentials/lesson-6/resource-uses-tab.png) {% rowspan=2 %}

{% /table %}
