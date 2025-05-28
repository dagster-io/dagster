---
title: Setup and peer
description: Setup requirements for using Dagster Airlift.
sidebar_position: 100
---

import AirliftPreview from '@site/docs/partials/\_AirliftPreview.md';

<AirliftPreview />

## 1. Create a components-ready Dagster project

To create a components-ready Dagster project, see "[Creating a project with dg](https://docs.dagster.io/guides/labs/dg/creating-a-project)".


### 2. Add the Airlift component to your environment

```
uv add dagster-airlift[core]
```

### 3. Scaffold the Airlift component

:::note

Currently `dagster-airlift` only supports basic authentication against an Airflow instance.

:::

To scaffold a new component in your project, use the `dg scaffold defs` command:

<CliInvocationExample path="docs_snippets/docs_snippets/integrations/airlift_v2/setup/basic_auth/1-scaffold.txt" />

This will create a component definition file called `component.yaml` in your project under the `defs/airflow` directory.

<CliInvocationExample path="docs_snippets/docs_snippets/integrations/airlift_v2/setup/basic_auth/2-tree.txt" />

### 4. Update `component.yaml` with Airflow configuration

By default, the Airlift component reads values from the environment variables `AIRFLOW_WEBSERVER_URL`, `AIRFLOW_USERNAME`, and `AIRFLOW_PASSWORD`. While you should never include your password directly in this file, you can update `component.yaml` to add the webserver URL and username:

<CliInvocationExample path="docs_snippets/docs_snippets/integrations/airlift_v2/setup/basic_auth/3-cat.txt" />

Once you have added these values, the following will happen:

1. Dagster will create a sensor called `your_airlift_instance__airflow_monitoring_job_sensor` that is responsible for detecting runs in your Airflow instance and pulling them into Dagster.
2. Your Airflow DAGs will be represented in Dagster in the "Jobs" page, and any jobs pulled from Airflow will be marked with an Airflow icon.
3. Airflow datasets will be represented in Dagster as assets.
4. When an Airflow DAG executes, that run will be represented in Dagster.
