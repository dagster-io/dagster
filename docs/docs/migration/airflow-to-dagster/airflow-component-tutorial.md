---
title: Using Dagster and Airflow together
sidebar_position: 20
description: The dagster-airlift library provides an AirflowInstanceComponent, which you can use to peer a Dagster project with an Airflow instance.
---

import DgComponentsRc from '@site/docs/partials/\_DgComponentsRc.md';

<DgComponentsRc />

The [dagster-airlift](/integrations/libraries/airlift) library provides an `AirflowInstanceComponent` which can be used to represent Airflow DAGs in Dagster, allowing easy interoperability between Airflow and Dagster.

## Setup and peering

### 1. Prepare a Dagster project

To begin, you'll need a Dagster project. You can use an [existing components-ready project](/guides/build/projects/moving-to-components/migrating-project) or create a new one:

uvx create-dagster@latest project my-project && cd my-project

Activate the project virtual environment:

```
source .venv/bin/activate
```

Finally, add the `dagster-airlift` library to the project:

```
uv add 'dagster-airlift[core]'
```

### 2. Scaffold an AirflowInstanceComponent

:::note

Currently `dagster-airlift` only supports basic authentication against an Airflow instance.

:::

To scaffold a new component in your project, use the `dg scaffold defs` command:

<CliInvocationExample path="docs_snippets/docs_snippets/integrations/airlift_v2/setup/basic_auth/1-scaffold.txt" />

This will create a component definition file called `defs.yaml` in your project under the `src/my_project/defs/airflow` directory.

<CliInvocationExample path="docs_snippets/docs_snippets/integrations/airlift_v2/setup/basic_auth/2-tree.txt" />

### 4. Update `defs.yaml` with Airflow configuration

By default, the Airlift component reads values from the environment variables `AIRFLOW_WEBSERVER_URL`, `AIRFLOW_USERNAME`, and `AIRFLOW_PASSWORD`. While you should never include your password directly in this file, you can update `defs.yaml` to add the webserver URL and username:

<CliInvocationExample path="docs_snippets/docs_snippets/integrations/airlift_v2/setup/basic_auth/3-cat.txt" />

Once you have added these values, the following will happen:

1. Dagster will create a sensor called `your_airlift_instance__airflow_monitoring_job_sensor` that is responsible for detecting runs in your Airflow instance and pulling them into Dagster.
2. Your Airflow DAGs will be represented in Dagster in the "Jobs" page, and any jobs pulled from Airflow will be marked with an Airflow icon.
3. Airflow datasets will be represented in Dagster as assets.
4. When an Airflow DAG executes, that run will be represented in Dagster.

## Mapping Dagster assets to Airflow tasks

Once you have represented your Airflow instance in Dagster using the Airflow instance component, you may want to represent the graph of asset dependencies produced by that DAG as well, which you can do in `defs.yaml`.

### DAG-level mapping

You can manually define which assets are produced by a given Airflow DAG by editing `mappings` in `defs.yaml`:

<CodeExample path="docs_snippets/docs_snippets/integrations/airlift_v2/represent_airflow_dags_in_dagster/component_dag_mappings.yaml" />

### Task-level mapping

If you have a more specific mapping from a task within the dag to a set of assets, you can also set these mappings at the task level:

<CodeExample path="docs_snippets/docs_snippets/integrations/airlift_v2/represent_airflow_dags_in_dagster/component_task_mappings.yaml" />
