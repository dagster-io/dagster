import base64
import inspect
import os
import re
import subprocess
import textwrap
from contextlib import contextmanager
from typing import Any, Callable, Iterator

import pytest
from dagster import AssetExecutionContext, asset, materialize
from dagster._core.errors import DagsterPipesExecutionError
from dagster_databricks.pipes import (
    PipesDatabricksClient,
    dbfs_tempdir,
)
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import files, jobs

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


@contextmanager
def temp_script(script_fn: Callable[[], Any], client: WorkspaceClient) -> Iterator[str]:
    # drop the signature line
    source = textwrap.dedent(inspect.getsource(script_fn).split("\n", 1)[1])
    dbfs_client = files.DbfsAPI(client.api_client)
    with dbfs_tempdir(dbfs_client) as tempdir:
        script_path = os.path.join(tempdir, "script.py")
        contents = base64.b64encode(source.encode("utf-8")).decode("utf-8")
        dbfs_client.put(script_path, contents=contents, overwrite=True)
        yield script_path


@pytest.fixture
def client() -> WorkspaceClient:
    return WorkspaceClient(
        host=os.environ["DATABRICKS_HOST"],
        token=os.environ["DATABRICKS_TOKEN"],
    )


CLUSTER_DEFAULTS = {
    "spark_version": "12.2.x-scala2.12",
    "node_type_id": "i3.xlarge",
    "num_workers": 0,
}

TASK_KEY = "DAGSTER_PIPES_TASK"

DAGSTER_PIPES_WHL_FILENAME = "dagster_pipes-1!0+dev-py3-none-any.whl"

# This has been manually uploaded to a test DBFS workspace.
DAGSTER_PIPES_WHL_PATH = f"dbfs:/FileStore/jars/{DAGSTER_PIPES_WHL_FILENAME}"


def get_repo_root() -> str:
    path = os.path.dirname(__file__)
    while not os.path.exists(os.path.join(path, ".git")):
        path = os.path.dirname(path)
    return path


# Upload the Dagster Pipes wheel to DBFS. Use this fixture to avoid needing to manually reupload
# dagster-pipes if it has changed between test runs.
@contextmanager
def upload_dagster_pipes_whl(client: WorkspaceClient) -> Iterator[None]:
    repo_root = get_repo_root()
    orig_wd = os.getcwd()
    dagster_pipes_root = os.path.join(repo_root, "python_modules", "dagster-pipes")
    os.chdir(dagster_pipes_root)
    subprocess.check_call(["python", "setup.py", "bdist_wheel"])
    subprocess.check_call(
        ["dbfs", "cp", "--overwrite", f"dist/{DAGSTER_PIPES_WHL_FILENAME}", DAGSTER_PIPES_WHL_PATH]
    )
    os.chdir(orig_wd)
    yield


def _make_submit_task(path: str, forward_logs: bool) -> jobs.SubmitTask:
    cluster_settings = CLUSTER_DEFAULTS.copy()
    if forward_logs:
        cluster_settings["cluster_log_conf"] = {
            "dbfs": {"destination": "dbfs:/cluster-logs"},
        }
    return jobs.SubmitTask.from_dict(
        {
            "new_cluster": cluster_settings,
            "libraries": [
                {"whl": DAGSTER_PIPES_WHL_PATH},
            ],
            "task_key": TASK_KEY,
            "spark_python_task": {
                "python_file": f"dbfs:{path}",
                "source": jobs.Source.WORKSPACE,
            },
        }
    )


# Test both with and without log forwarding. This is important because the PipesClient spins up log
# readers before it knows the task specification


@pytest.mark.skipif(IS_BUILDKITE, reason="Not configured to run on BK yet.")
@pytest.mark.parametrize("forward_logs", [True, False])
def test_pipes_client(capsys, client: WorkspaceClient, forward_logs: bool):
    @asset
    def number_x(context: AssetExecutionContext, pipes_client: PipesDatabricksClient):
        with upload_dagster_pipes_whl(client):
            with temp_script(script_fn, client) as script_path:
                task = _make_submit_task(script_path, forward_logs)
                return pipes_client.run(
                    task=task,
                    context=context,
                    extras={"multiplier": 2, "storage_root": "fake"},
                ).get_results()

    result = materialize(
        [number_x],
        resources={
            "pipes_client": PipesDatabricksClient(
                client,
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
def test_nonexistent_entry_point(client: WorkspaceClient):
    @asset
    def fake(context: AssetExecutionContext, pipes_client: PipesDatabricksClient):
        task = _make_submit_task("/fake/fake", forward_logs=False)
        return pipes_client.run(task=task, context=context).get_results()

    with pytest.raises(DagsterPipesExecutionError, match=r"Cannot read the python file"):
        materialize(
            [fake],
            resources={"pipes_client": PipesDatabricksClient(client)},
        )
