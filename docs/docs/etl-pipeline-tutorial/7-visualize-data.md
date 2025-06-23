---
title: Visualize data
description: Visualize data with Evidence
sidebar_position: 80
---

We will include one final component downstream of everything we have built. This will visualize some of the data we have been modeling in a dashboard using [Evidence](https://evidence.dev/). In this step, you will:

- Integrate with Evidence
- Build an Evidence deployment asset connected to your model assets

## 1. Add the Evidence project

We need an Evidence project. We will clone one that is already configured to work with the data we have modeled with dbt:

```bash
git clone --depth=1 https://github.com/dagster-io/jaffle-dashboard.git dashboard && rm -rf dashboard/.git
```

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

Change into that directory and install the necessary packages with [`npm`](https://www.npmjs.com/):

```bash
cd dashboard && npm install
```

## 2. Define the Evidence Component

Let's add the Dagster's Evidence integration:

```bash
uv pip install dagster-evidence
```

Now we can scaffold Evidence with `dg`:

```bash
dg scaffold defs dagster_evidence.EvidenceProject dashboard
```

This will add the directory `dashboard` to the `etl_tutorial` module:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/tree/evidence.txt" />

## 3. Configure the Evidence `defs.yaml`

Unlike our other components which generated individual assets for each model in our project. The Evidence component will register a single asset for the entire Evidence deployment.

However we can still configure our Evidence component to be dependent on multiple upstream assets.

<CodeExample
    path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/src/etl_tutorial/defs/dashboard/defs.yaml"
    language="yaml"
    title="src/etl_tutorial/defs/dashboard/defs.yaml"
/>

## 4. Execute the Evidence asset

With the Evidence component configured, our assets graph should look like this.

![2048 resolution](/images/tutorial/etl-tutorial/assets-evidence.png)

Execute the downstream `dashboard` asset which will build our Evidence dashboards. You can now run Evidence:

```bash
cd dashboard/build && python -m http.server
```

You should see a dashboard like the following at [http://localhost:8000/](http://localhost:8000/).

![2048 resolution](/images/tutorial/etl-tutorial/evidence-dashboard.png)

## Summary

Here is the final structure of our `etl_tutorial` project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/tree/step-7.txt" />

We have now built a fully functional, end-to-end data platform that handles everything from data ingestion to modeling and visualization.

## Recommended next steps

- Join our [Slack community](https://dagster.io/slack).
- Continue learning with [Dagster University](https://courses.dagster.io/) courses.
- Start a [free trial of Dagster+](https://dagster.cloud/signup) for your own project.