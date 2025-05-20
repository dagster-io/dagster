---
title: Setup
description: Setup requirements for using Dagster Airlift.
sidebar_position: 100
---

import AirliftPreview from '@site/docs/partials/\_AirliftPreview.md';

<AirliftPreview />

## Install `dg`

To install `dg`, follow the [`dg` installation guide](https://docs.dagster.io/guides/labs/dg).

## Create a components-ready project

To create a components-ready project, follow the [project creation guide](https://docs.dagster.io/guides/labs/dg/creating-a-project).


### Add the Airlift component type to your environment

```
uv add dagster-airlift[core]
```


### Create a new instance of the Airlift component

Currently dagster-airlift only supports basic authentication against an Airflow instance. You can scaffold a new component into your project using the `dg scaffold` command:

<CliInvocationExample path="docs_snippets/docs_snippets/integrations/airlift_v2/setup/basic_auth/1-scaffold.txt" />

This will create a new component definition in your project under the `defs/airflow` directory.

<CliInvocationExample path="docs_snippets/docs_snippets/integrations/airlift_v2/setup/basic_auth/2-tree.txt" />

By default, the component pulls values from environment variables (`AIRFLOW_WEBSERVER_URL`, `AIRFLOW_USERNAME`, and `AIRFLOW_PASSWORD`). While you should never include your password directly in this file, you can update the generated file to hard code the values for the webserver url and username if desired.

<CliInvocationExample path="docs_snippets/docs_snippets/integrations/airlift_v2/setup/basic_auth/3-cat.txt" />

Once this is done, Dagster will do a few things:

1. All of your airflow dags will be automatically represented in dagster in the "jobs" page. Any jobs pulled from airflow will have an airflow icon to distinguish them
2. Any airflow datasets will be automatically represented in dagster as assets 
2. Any time an airflow dag executes, that run will be represented 


(maybe explain the fact that it creates a sensor called `your_airlift_instance__airflow_monitoring_job_sensor` that will be responsible for looking for runs in your airflow instance and pulling them in to dagster)