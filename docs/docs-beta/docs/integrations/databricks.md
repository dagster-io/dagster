---
layout: Integration
status: published
name: Databricks
title: Dagster & Databricks
sidebar_label: Databricks
excerpt: The Databricks integration enables you to initiate Databricks jobs directly from Dagster, seamlessly pass parameters to your code, and stream logs and structured messages back into Dagster.
date: 2024-08-20
apireflink: https://docs.dagster.io/concepts/dagster-pipes/databricks
docslink: 
partnerlink: https://databricks.com/
logo: /integrations/databricks.svg
categories:
  - Compute
enabledBy:
enables:
---

### About this integration

The `dagster-databricks` integration library provides the `PipesDatabricksClient` resource, enabling you to launch Databricks jobs directly from Dagster assets and ops. This integration allows you to pass parameters to Databricks code while Dagster receives real-time events, such as logs, asset checks, and asset materializations, from the initiated jobs. With minimal code changes required on the job side, this integration is both efficient and easy to implement.

### Installation

```bash
pip install dagster-databricks
```

### Example

#### Dagster code

```python
import os
import sys

from dagster_databricks import PipesDatabricksClient

from dagster import AssetExecutionContext, Definitions, EnvVar, asset
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import jobs


@asset
def databricks_asset(
    context: AssetExecutionContext, pipes_databricks: PipesDatabricksClient
):
    task = jobs.SubmitTask.from_dict(
        {
            # The cluster settings below are somewhat arbitrary. Dagster Pipes is
            # not dependent on a specific spark version, node type, or number of
            # workers.
            "new_cluster": {
                "spark_version": "12.2.x-scala2.12",
                "node_type_id": "i3.xlarge",
                "num_workers": 0,
                "cluster_log_conf": {
                    "dbfs": {"destination": "dbfs:/cluster-logs-dir-noexist"},
                },
            },
            "libraries": [
                # Include the latest published version of dagster-pipes on PyPI
                # in the task environment
                {"pypi": {"package": "dagster-pipes"}},
            ],
            "task_key": "some-key",
            "spark_python_task": {
                "python_file": "dbfs:/my_python_script.py",  # location of target code file
                "source": jobs.Source.WORKSPACE,
            },
        }
    )

    print("This will be forwarded back to Dagster stdout")
    print("This will be forwarded back to Dagster stderr", file=sys.stderr)

    extras = {"some_parameter": 100}

    return pipes_databricks.run(
        task=task,
        context=context,
        extras=extras,
    ).get_materialize_result()


pipes_databricks_resource = PipesDatabricksClient(
    client=WorkspaceClient(
        host=os.environ["DATABRICKS_HOST"],
        token=os.environ["DATABRICKS_TOKEN"],
    )
)

defs = Definitions(
    assets=[databricks_asset], resources={"pipes_databricks": pipes_databricks_resource}
)
```

#### Databricks code

```python
from dagster_pipes import (
    PipesDbfsContextLoader,
    PipesDbfsMessageWriter,
    open_dagster_pipes,
)

# Sets up communication channels and downloads the context data sent from Dagster.
# Note that while other `context_loader` and `message_writer` settings are
# possible, it is recommended to use `PipesDbfsContextLoader` and
# `PipesDbfsMessageWriter` for Databricks.
with open_dagster_pipes(
    context_loader=PipesDbfsContextLoader(),
    message_writer=PipesDbfsMessageWriter(),
) as pipes:
    # Access the `extras` dict passed when launching the job from Dagster.
    some_parameter_value = pipes.get_extra("some_parameter")

    # Stream log message back to Dagster
    pipes.log.info(f"Using some_parameter value: {some_parameter_value}")

    # ... your code that computes and persists the asset

    # Stream asset materialization metadata and data version back to Dagster.
    # This should be called after you've computed and stored the asset value. We
    # omit the asset key here because there is only one asset in scope, but for
    # multi-assets you can pass an `asset_key` parameter.
    pipes.report_asset_materialization(
        metadata={
            "some_metric": {"raw_value": some_parameter_value + 1, "type": "int"}
        },
        data_version="alpha",
    )

```

### About Databricks

**Databricks** is a unified data analytics platform that simplifies and accelerates the process of building big data and AI solutions. It integrates seamlessly with Apache Spark and offers support for various data sources and formats. Databricks provides powerful tools to create, run, and manage data pipelines, making it easier to handle complex data engineering tasks. Its collaborative and scalable environment is ideal for data engineers, scientists, and analysts who need to process and analyze large datasets efficiently.
