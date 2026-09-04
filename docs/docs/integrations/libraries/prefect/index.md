---
title: Dagster & Prefect
sidebar_label: Prefect
sidebar_position: 1
description: Launch Prefect deployments and background tasks from the Dagster asset graph, with Dagster scheduling, partitioning, and lineage.
tags: [dagster-supported, compute]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-prefect
pypi: https://pypi.org/project/dagster-prefect
sidebar_custom_props:
  logo: images/integrations/prefect.svg
partnerlink: https://www.prefect.io/
canonicalUrl: '/integrations/libraries/prefect'
slug: '/integrations/libraries/prefect'
---

import Preview from '@site/docs/partials/\_Preview.md';

<Preview />

The `dagster-prefect` library uses [Dagster Pipes](/integrations/external-pipelines) to launch work on Prefect from a Dagster asset. Dagster stays the control plane, handling scheduling, partitioning, lineage, and retries, while the work itself runs on Prefect's infrastructure and reports back.

This is useful when a workflow already runs on Prefect and you would rather orchestrate it than rewrite it, and when a step needs the durability of a workflow engine but should still be a node in the asset graph.

## Two ways to launch

| Client                         | Launches                                                            | Executed by                                                                              |
| ------------------------------ | ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `PipesPrefectDeploymentClient` | a [deployment](https://docs.prefect.io/v3/concepts/deployments) run | a worker on the deployment's work pool, a push work pool, or a Prefect Managed work pool |
| `PipesPrefectTaskClient`       | a [background task](https://docs.prefect.io/v3/concepts/tasks) run  | a task worker (`prefect task serve`)                                                     |

Prefer deployments. A deployment run receives the Pipes payload as environment variables, so your flow's signature stays exactly as it is, and it is the only option that can run on Prefect-managed infrastructure. Background tasks have no environment channel, so the payload has to travel as a task argument.

## Installation

<Tabs>
  <TabItem value="uv" label="uv">

```shell
uv add dagster-prefect
```

  </TabItem>
  <TabItem value="pip" label="pip">

```shell
pip install dagster-prefect
```

  </TabItem>
</Tabs>

:::warning

`dagster-prefect` cannot be installed alongside `dagster-airflow` or `dagster-airlift` when those are pinned to Airflow 2.x. Prefect 3 requires `sqlalchemy>=2`, and Airflow 2.x requires `sqlalchemy<2`. Use separate environments for Prefect and Airflow 2.x integrations.

:::

## Launching a deployment

Add one line to the flow you already have. `open_dagster_pipes()` needs no configuration, because the deployment run receives everything it needs as environment variables:

```python
from dagster_pipes import open_dagster_pipes
from prefect import flow, task


@task(retries=2)
def extract(as_of: str) -> list[dict]: ...


@flow
def refresh_orders(as_of: str = "latest") -> None:
    rows = extract(as_of)
    with open_dagster_pipes() as pipes:
        pipes.report_asset_materialization(metadata={"rows": len(rows)})
```

That line is safe outside Dagster. Run the flow on its own and `open_dagster_pipes()` warns and returns a no-op context, so existing Prefect runs keep working.

On the Dagster side, configure the resource and launch the deployment by its `flow-name/deployment-name`:

```python
import dagster as dg
from dagster_prefect import PipesPrefectDeploymentClient, PrefectResource


@dg.asset(kinds={"prefect"})
def orders_summary(
    context: dg.AssetExecutionContext, prefect_deployments: PipesPrefectDeploymentClient
):
    return prefect_deployments.run(
        context=context,
        deployment="refresh-orders/production",
        parameters={"as_of": "latest"},
    ).get_materialize_result()


defs = dg.Definitions(
    assets=[orders_summary],
    resources={
        "prefect_deployments": PipesPrefectDeploymentClient(
            prefect=PrefectResource(
                api_url=dg.EnvVar("PREFECT_API_URL"),
                api_key=dg.EnvVar("PREFECT_API_KEY"),
            )
        )
    },
)
```

The Dagster step blocks until the flow run reaches a terminal state. Anything the flow reports through Pipes lands on the materialization, along with a `Prefect Run URL` linking to the run in Prefect.

`api_url` is the Prefect API, for example `http://127.0.0.1:4200/api` for an open source server. Set `ui_url` as well on Prefect Cloud, whose UI is served from a different host than its API.

## Partitioning

Dagster can tell the flow which slice of data to compute, instead of the flow working it out at runtime. Set `partition_parameter` to the name of the flow parameter that should receive the partition key:

```python
@dg.asset(
    partitions_def=dg.DailyPartitionsDefinition(start_date="2026-01-01"),
    kinds={"prefect"},
)
def daily_report(
    context: dg.AssetExecutionContext, prefect_deployments: PipesPrefectDeploymentClient
):
    return prefect_deployments.run(
        context=context,
        deployment="daily-report/production",
        partition_parameter="day",
    ).get_materialize_result()
```

Each partition becomes one Prefect flow run with `day` set to that partition's key, so filling in a range of dates is an ordinary Dagster backfill rather than a script that iterates flow runs and works out which ones are missing. Use `partition_window_parameters=("start", "end")` to pass a time-partitioned window instead; both are sent as ISO 8601 strings, since Prefect parameters must be JSON-serializable.

A Pipes-aware flow can also read `pipes.partition_key`, `pipes.partition_key_range`, and `pipes.partition_time_window` off the Pipes context without any of this.

Multi-dimensional partitions are not supported by `partition_parameter`, because their keys are composite. Pass the dimensions you want as ordinary `parameters`.

## Launching a background task

A background task has no environment channel, so it takes the Pipes payload as an argument and loads it explicitly:

```python
from dagster_pipes import PipesMappingParamsLoader, open_dagster_pipes
from prefect import task


@task
def summarize(as_of: str, dagster_pipes_params: dict[str, str] | None = None) -> None:
    with open_dagster_pipes(
        params_loader=PipesMappingParamsLoader(dagster_pipes_params or {})
    ) as pipes:
        pipes.report_asset_materialization(metadata={"rows": 100})
```

```python
@dg.asset(kinds={"prefect"})
def orders_summary(context: dg.AssetExecutionContext, prefect_tasks: PipesPrefectTaskClient):
    return prefect_tasks.run(
        context=context, task=summarize, parameters={"as_of": "latest"}
    ).get_materialize_result()
```

A task worker must be serving the task, otherwise the task run is created and never picked up.

## Cancellation

Terminating the Dagster run cancels the Prefect flow run it was waiting on. Set `forward_termination=False` on the client to leave the Prefect run alone.

Background tasks are the exception: Prefect's task worker runs a task to completion regardless of a cancellation request, so terminating the Dagster run logs a warning and the task keeps running.

A Prefect run cancelled from Prefect's side fails the Dagster step with a message naming the cancellation.

## Reporting messages back

Both clients default to a temporary-file message reader, which requires the process running your flow or task to share a filesystem with the Dagster step. That holds for a worker on the same host, and does not for a worker in a container, on another machine, or on Prefect-managed infrastructure. Pass a blob store message reader for those, for example:

```python
import boto3
from dagster_aws.pipes import PipesS3MessageReader

PipesPrefectDeploymentClient(
    prefect=PrefectResource(api_url=dg.EnvVar("PREFECT_API_URL")),
    message_reader=PipesS3MessageReader(bucket="my-bucket", client=boto3.client("s3")),
)
```

Without a reader the flow can reach, Dagster still materializes the asset when the Prefect run succeeds, but without the metadata, logs, or asset checks the flow reported.
