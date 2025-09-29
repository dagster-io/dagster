import os
from typing import Any, Callable

import pytest
from dagster import AssetExecutionContext, asset, materialize
from dagster._core.errors import DagsterPipesExecutionError
from dagster_databricks._test_utils import (  # noqa: F401
    databricks_client,
    get_databricks_notebook_path,
    get_databricks_python_file_path,
)
from dagster_databricks.pipes import PipesDatabricksServerlessClient
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import jobs

IS_BUILDKITE = os.getenv("BUILDKITE") is not None
IS_WORKSPACE = os.getenv("DATABRICKS_HOST") is not None

TEST_VOLUME_PATH = "/Volumes/workspace/default/databricks_serverless_pipes_test"


def script_fn():
    # The content of this script must be manually added to a Databricks notebook
    # for which dagster-pipes has been added as a dependency.
    # The path to the notebook must be set as the `DATABRICKS_NOTEBOOK_PATH` env var when running tests in this module.
    import sys

    from dagster_pipes import (
        PipesDatabricksNotebookWidgetsParamsLoader,
        PipesUnityCatalogVolumesContextLoader,
        PipesUnityCatalogVolumesMessageWriter,
        open_dagster_pipes,
    )

    with open_dagster_pipes(
        context_loader=PipesUnityCatalogVolumesContextLoader(),
        message_writer=PipesUnityCatalogVolumesMessageWriter(),
        params_loader=PipesDatabricksNotebookWidgetsParamsLoader(dbutils.widgets),  # noqa  # pyright: ignore
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
    file_path: str,
    task_type: str,
    file_path_key: str,
) -> dict[str, Any]:
    submit_spec = {
        "task_key": TASK_KEY,
        task_type: {
            file_path_key: file_path,
            "source": jobs.Source.WORKSPACE,
        },
    }
    return submit_spec


def make_notebook_task(notebook_path: str):
    return jobs.SubmitTask.from_dict(
        make_submit_task_dict(
            file_path=notebook_path, task_type="notebook_task", file_path_key="notebook_path"
        )
    )


def make_spark_python_task(python_file_path: str):
    return jobs.SubmitTask.from_dict(
        {
            **make_submit_task_dict(
                file_path=python_file_path,
                task_type="spark_python_task",
                file_path_key="python_file",
            ),
            "environment_key": "dagster_pipes_env",
        }
    )


@pytest.mark.skipif(IS_BUILDKITE, reason="Not configured to run on BK yet.")
@pytest.mark.skipif(not IS_WORKSPACE, reason="No DB workspace credentials found.")
@pytest.mark.parametrize(
    "file_path_fn, make_task_fn",
    [
        (get_databricks_notebook_path, make_notebook_task),
        (get_databricks_python_file_path, make_spark_python_task),
    ],
    ids=[
        "notebook_task",
        "spark_python_task",
    ],
)
def test_pipes_client(
    databricks_client: WorkspaceClient,  # noqa: F811
    file_path_fn: Callable,
    make_task_fn: Callable,
):
    @asset
    def number_x(context: AssetExecutionContext, pipes_client: PipesDatabricksServerlessClient):
        task = make_task_fn(file_path_fn())
        return pipes_client.run(
            task=task,
            context=context,
            extras={"multiplier": 2, "storage_root": "fake"},
            submit_args={
                "environments": [
                    jobs.JobEnvironment.from_dict(
                        {
                            "environment_key": "dagster_pipes_env",
                            "spec": {"environment_version": 2, "dependencies": ["dagster_pipes"]},
                        }
                    )
                ]
            },
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
        task = make_notebook_task("/fake/fake")
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
