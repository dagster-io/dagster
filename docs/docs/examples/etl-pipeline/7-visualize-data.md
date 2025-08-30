---
title: Build a dashboard to visualize data
description: Visualize data with an Evidence dashboard
sidebar_position: 80
---

In this final step, we will visualize some of the data we have been modeling in a dashboard using [Evidence](https://evidence.dev/) connected to our model assets.

## 1. Add the Evidence project

First, we will clone an Evidence project that is already configured to work with the data we have modeled with dbt:

<CliInvocationExample contents="git clone --depth=1 https://github.com/dagster-io/jaffle-dashboard.git dashboard && rm -rf dashboard/.git" />

There will now be a directory `dashboard` within the root of the project.

```
.
├── pyproject.toml
├── dashboard # Evidence project
├── src
├── tests
├── transform
└── uv.lock
```

Change into that directory and install the necessary packages with [`npm`](https://www.npmjs.com):

<CliInvocationExample contents="cd dashboard && npm install" />

## 2. Define the Evidence Component

Next, we will need to install Dagster's [Evidence integration](https://docs.dagster.io/integrations/libraries/evidence):

<Tabs groupId="package-manager">
   <TabItem value="uv" label="uv">
      Install the required dependencies:

         ```shell
         uv add dagster-evidence
         ```

   </TabItem>

   <TabItem value="pip" label="pip">
      Install the required dependencies:

         ```shell
         pip install dagster-evidence
         ```

   </TabItem>
</Tabs>

Now we can scaffold Evidence with `dg`:

<CliInvocationExample path="docs_projects/project_etl_tutorial/commands/dg-scaffold-evidence.txt" />

This will add the directory `dashboard` to the `etl_tutorial` module:

<CliInvocationExample path="docs_projects/project_etl_tutorial/tree/evidence.txt" />

## 3. Configure the Evidence `defs.yaml`

Unlike the other components we used, which generated individual assets for each model in our project, the Evidence component will register a single asset for the entire Evidence deployment. This asset will build all the sources and dashboards within our Evidence project.

However, we can still configure our Evidence component to be dependent on multiple upstream assets by setting the `deps` value within the `attributes` key of the Evidence component `defs.yaml` file:

<CodeExample
  path="docs_projects/project_etl_tutorial/src/etl_tutorial/defs/dashboard/defs.yaml"
  language="yaml"
  title="src/etl_tutorial/defs/dashboard/defs.yaml"
/>

## 4. Execute the Evidence asset

With the Evidence component configured, our assets graph should look like this:

![2048 resolution](/images/tutorial/etl-tutorial/assets-evidence.png)

You can now execute the Evidence asset and view the output:

1. Reload your Definitions.
2. Execute the `dashboard` asset (assuming the upstream assets have been materialized).
3. After the `dashboard` asset has successfully materialized, on the command line, execute the following to run the Evidence server:

   <CliInvocationExample contents="cd dashboard/build && python -m http.server" />

4. Navigate to the dashboard at [http://localhost:8000/](http://localhost:8000/):

   ![2048 resolution](/images/tutorial/etl-tutorial/evidence-dashboard.png)

## Summary

Here is the final structure of our `etl_tutorial` project:

<CliInvocationExample path="docs_projects/project_etl_tutorial/tree/step-7.txt" />

Congratulations! You've just built a fully functional, end-to-end data platform—one that seamlessly handles everything from raw data ingestion to transformation, modeling, and even downstream visualization. This is no small feat! You've laid the foundation for a scalable, maintainable, and observable data ecosystem using modern tools and best practices.

## Recommended next steps

- Join our [Slack community](https://dagster.io/slack).
- Continue learning with [Dagster University](https://courses.dagster.io) courses.
- Start a [free trial of Dagster+](https://dagster.cloud/signup) for your own project.
