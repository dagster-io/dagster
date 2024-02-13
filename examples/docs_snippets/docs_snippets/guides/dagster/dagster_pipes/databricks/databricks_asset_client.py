# start_databricks_asset
### dagster_databricks_pipes.py

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

    print("This will be forwarded back to Dagster stdout")  # noqa: T201
    print("This will be forwarded back to Dagster stderr", file=sys.stderr)  # noqa: T201

    extras = {"some_parameter": 100}

    return pipes_databricks.run(
        task=task,
        context=context,
        extras=extras,
    ).get_materialize_result()


# end_databricks_asset

# start_definitions

pipes_databricks_resource = PipesDatabricksClient(
    client=WorkspaceClient(
        host=os.getenv("DATABRICKS_HOST"),
        token=os.getenv("DATABRICKS_TOKEN"),
    )
)

defs = Definitions(
    assets=[databricks_asset], resources={"pipes_databricks": pipes_databricks_resource}
)
# end_definitions
