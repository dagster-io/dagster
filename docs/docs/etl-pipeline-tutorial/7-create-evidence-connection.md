---
title: Create Evidence connection
description: Connect to Evidence to visualize data
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
│   └── __init__.py
├── transform
└── uv.lock
```

## 2. Define the Evidence Component

Let's add the Dagster's Evidence integration:

```bash
uv pip install dagster-sling
```

Now we can scaffold Evidence with `dg`:

```bash
dg scaffold defs dagster_evidence.EvidenceProject dashboard
```

This will add the directory `dashboard` to the `etl_tutorial` module:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/tree/evidence.txt" />

## 3. Configure the Evidence component

Unlike our other components which generated individual assets for each model in our project. The Evidence component will register a single asset for the entire Evidence deployment.

However we can still configure our Evidence component to be dependent on multiple upstream assets.

<CodeExample
    path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/src/etl_tutorial/defs/dashboard/defs.yaml"
    language="yaml"
    title="src/etl_tutorial/defs/dashboard/defs.yaml"
/>

## Summary

## Recommended next steps

- Join our [Slack community](https://dagster.io/slack).
- Continue learning with [Dagster University](https://courses.dagster.io/) courses.
- Start a [free trial of Dagster+](https://dagster.cloud/signup) for your own project.