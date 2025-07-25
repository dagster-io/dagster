import os
from contextlib import ExitStack
from typing import Any

import pytest
from dagster import AssetExecutionContext, asset, materialize
from dagster._core.errors import DagsterPipesExecutionError
from dagster_databricks._test_utils import (
    databricks_client,  # noqa: F401
    databricks_notebook_folder_path, # noqa: F401
    temp_notebook_script,
)
from dagster_databricks.pipes import PipesDatabricksServerlessClient
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import jobs

IS_BUILDKITE = os.getenv("BUILDKITE") is not None
IS_WORKSPACE = os.getenv("DATABRICKS_HOST") is not None

TEST_VOLUME_PATH = "/Volumes/workspace/default/databricks_serverless_pipes_test"

def script_fn():
    import sys

    from dagster_pipes import (
        PipesDatabricksNotebookWidgetsParamsLoader,
        PipesUnityCatalogVolumesContextLoader,
        PipesUnityCatalogVolumesMessageWriter,
        open_dagster_pipes,
    )

    mock_widgets = {}

    with open_dagster_pipes(
        params_loader=PipesDatabricksNotebookWidgetsParamsLoader(mock_widgets),
        context_loader=PipesUnityCatalogVolumesContextLoader(),
        message_writer=PipesUnityCatalogVolumesMessageWriter(),
    ) as context:
        multiplier = context.get_extra("multiplier")
        value = 2 * multiplier
        print("hello from databricks stdout")  # noqa: T201
        print("hello from databricks stderr", file=sys.stderr)  # noqa: T201
        context.log.info(f"{context.asset_key}: {2} * {multiplier} = {value}")
        context.report_asset_materialization(
            metadata={"value": value},
        )


TASK_KEY = "DAGSTER_SERVERLESS_PIPES_TASK"


def make_submit_task_dict(
    notebook_path: str,
) -> dict[str, Any]:
    submit_spec = {
        "task_key": TASK_KEY,
        "notebook_task": {
            "notebook_path": notebook_path,
            "source": jobs.Source.WORKSPACE,
        },
    }
    return submit_spec


def make_submit_task(
    notebook_path: str,
) -> jobs.SubmitTask:
    return jobs.SubmitTask.from_dict(
        make_submit_task_dict(
            notebook_path=notebook_path,
        )
    )


@pytest.mark.skipif(IS_BUILDKITE, reason="Not configured to run on BK yet.")
@pytest.mark.skipif(not IS_WORKSPACE, reason="No DB workspace credentials found.")
def test_pipes_client(
    databricks_client: WorkspaceClient,  # noqa: F811
    databricks_notebook_folder_path: str,  # noqa: F811
):
    @asset
    def number_x(context: AssetExecutionContext, pipes_client: PipesDatabricksServerlessClient):
        with ExitStack() as stack:
            script_path = stack.enter_context(
                temp_notebook_script(databricks_client, databricks_notebook_folder_path, script_fn=script_fn)
            )
            task = make_submit_task(script_path)
            return pipes_client.run(
                task=task,
                context=context,
                extras={"multiplier": 2, "storage_root": "fake"},
            ).get_results()

    result = materialize(
        [number_x],
        resources={
            "pipes_client": PipesDatabricksServerlessClient(
                client=databricks_client, volume_path=TEST_VOLUME_PATH
            )
        },
        raise_on_error=False,
    )
    assert result.success
    mats = result.asset_materializations_for_node(number_x.op.name)
    assert mats[0].metadata["value"].value == 4

    # check Databricks metadata automatically added to materialization
    assert "Databricks Job Run ID" in mats[0].metadata
    assert "Databricks Job Run URL" in mats[0].metadata


@pytest.mark.skipif(IS_BUILDKITE, reason="Not configured to run on BK yet.")
@pytest.mark.skipif(not IS_WORKSPACE, reason="No DB workspace credentials found.")
def test_nonexistent_entry_point(databricks_client: WorkspaceClient):  # noqa: F811
    @asset
    def fake(context: AssetExecutionContext, pipes_client: PipesDatabricksServerlessClient):
        task = make_submit_task("/fake/fake")
        return pipes_client.run(task=task, context=context).get_results()

    with pytest.raises(DagsterPipesExecutionError, match=r"Unable to access the notebook"):
        materialize(
            [fake],
            resources={
                "pipes_client": PipesDatabricksServerlessClient(
                    client=databricks_client, volume_path=TEST_VOLUME_PATH
                )
            },
        )
