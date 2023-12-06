import os
import re

import pytest
from dagster import AssetExecutionContext, asset, materialize
from dagster._core.errors import DagsterPipesExecutionError
from dagster_databricks._test_utils import (
    databricks_client,  # noqa: F401
    temp_dbfs_script,
    upload_dagster_pipes_whl,
)
from dagster_databricks.pipes import (
    PipesDatabricksClient,
)
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import jobs

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


def script_fn():
    import sys

    from dagster_pipes import (
        PipesDbfsContextLoader,
        PipesDbfsMessageWriter,
        open_dagster_pipes,
    )

    with open_dagster_pipes(
        context_loader=PipesDbfsContextLoader(),
        message_writer=PipesDbfsMessageWriter(),
    ) as context:
        multiplier = context.get_extra("multiplier")
        value = 2 * multiplier
        print("hello from databricks stdout")  # noqa: T201
        print("hello from databricks stderr", file=sys.stderr)  # noqa: T201
        context.log.info(f"{context.asset_key}: {2} * {multiplier} = {value}")
        context.report_asset_materialization(
            metadata={"value": value},
        )


CLUSTER_DEFAULTS = {
    "spark_version": "12.2.x-scala2.12",
    "node_type_id": "i3.xlarge",
    "num_workers": 0,
}

TASK_KEY = "DAGSTER_PIPES_TASK"


def _make_submit_task(
    script_path: str, dagster_pipes_whl_path: str, forward_logs: bool
) -> jobs.SubmitTask:
    cluster_settings = CLUSTER_DEFAULTS.copy()
    if forward_logs:
        cluster_settings["cluster_log_conf"] = {
            "dbfs": {"destination": "dbfs:/cluster-logs"},
        }
    return jobs.SubmitTask.from_dict(
        {
            "new_cluster": cluster_settings,
            "libraries": [
                # {"whl": DAGSTER_PIPES_WHL_PATH},
                {"whl": dagster_pipes_whl_path},
            ],
            "task_key": TASK_KEY,
            "spark_python_task": {
                "python_file": f"dbfs:{script_path}",
                "source": jobs.Source.WORKSPACE,
            },
        }
    )


# Test both with and without log forwarding. This is important because the PipesClient spins up log
# readers before it knows the task specification
@pytest.mark.skipif(IS_BUILDKITE, reason="Not configured to run on BK yet.")
@pytest.mark.parametrize("forward_logs", [True, False])
def test_pipes_client(capsys, databricks_client: WorkspaceClient, forward_logs: bool):  # noqa: F811
    @asset
    def number_x(context: AssetExecutionContext, pipes_client: PipesDatabricksClient):
        with upload_dagster_pipes_whl(databricks_client) as dagster_pipes_whl_path:
            with temp_dbfs_script(databricks_client, script_fn=script_fn) as script_path:
                task = _make_submit_task(script_path, dagster_pipes_whl_path, forward_logs)
                return pipes_client.run(
                    task=task,
                    context=context,
                    extras={"multiplier": 2, "storage_root": "fake"},
                ).get_results()

    result = materialize(
        [number_x],
        resources={
            "pipes_client": PipesDatabricksClient(
                databricks_client,
            )
        },
        raise_on_error=False,
    )
    assert result.success
    mats = result.asset_materializations_for_node(number_x.op.name)
    assert mats[0].metadata["value"].value == 4
    if forward_logs:
        captured = capsys.readouterr()
        assert re.search(r"hello from databricks stdout\n", captured.out, re.MULTILINE)
        assert re.search(r"hello from databricks stderr\n", captured.err, re.MULTILINE)


@pytest.mark.skipif(IS_BUILDKITE, reason="Not configured to run on BK yet.")
def test_nonexistent_entry_point(databricks_client: WorkspaceClient):  # noqa: F811
    @asset
    def fake(context: AssetExecutionContext, pipes_client: PipesDatabricksClient):
        task = _make_submit_task("/fake/fake", "/fake/fake", forward_logs=False)
        return pipes_client.run(task=task, context=context).get_results()

    with pytest.raises(DagsterPipesExecutionError, match=r"Cannot read the python file"):
        materialize(
            [fake],
            resources={"pipes_client": PipesDatabricksClient(databricks_client)},
        )
