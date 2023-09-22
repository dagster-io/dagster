import base64
import inspect
import os
import textwrap
from contextlib import contextmanager
from typing import Any, Callable, Iterator

import pytest
from dagster import AssetExecutionContext, asset, materialize
from dagster._core.errors import DagsterExternalExecutionError
from dagster_databricks import ExtDatabricks, dbfs_tempdir
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import files, jobs

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


def script_fn():
    from dagster_ext import ExtDbfsContextLoader, ExtDbfsMessageWriter, init_dagster_ext

    context = init_dagster_ext(
        context_loader=ExtDbfsContextLoader(), message_writer=ExtDbfsMessageWriter()
    )

    multiplier = context.get_extra("multiplier")
    value = 2 * multiplier

    context.log(f"{context.asset_key}: {2} * {multiplier} = {value}")
    context.report_asset_materialization(
        metadata={"value": value},
        data_version="alpha",
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

TASK_KEY = "DAGSTER_EXT_TASK"

# This has been manually uploaded to a test DBFS workspace.
DAGSTER_EXTERNALS_WHL_PATH = "dbfs:/FileStore/jars/dagster_ext-1!0+dev-py3-none-any.whl"


def _make_submit_task(path: str) -> jobs.SubmitTask:
    return jobs.SubmitTask.from_dict(
        {
            "new_cluster": CLUSTER_DEFAULTS,
            "libraries": [
                {"whl": DAGSTER_EXTERNALS_WHL_PATH},
            ],
            "task_key": TASK_KEY,
            "spark_python_task": {
                "python_file": f"dbfs:{path}",
                "source": jobs.Source.WORKSPACE,
            },
        }
    )


@pytest.mark.skipif(IS_BUILDKITE, reason="Not configured to run on BK yet.")
def test_basic(client: WorkspaceClient):
    @asset
    def number_x(context: AssetExecutionContext, ext_databricks: ExtDatabricks):
        with temp_script(script_fn, client) as script_path:
            task = _make_submit_task(script_path)
            ext_databricks.run(
                task=task,
                context=context,
                extras={"multiplier": 2, "storage_root": "fake"},
            )

    result = materialize(
        [number_x],
        resources={"ext_databricks": ExtDatabricks(client)},
        raise_on_error=False,
    )
    assert result.success
    mats = result.asset_materializations_for_node(number_x.op.name)
    assert mats[0].metadata["path"]


@pytest.mark.skipif(IS_BUILDKITE, reason="Not configured to run on BK yet.")
def test_nonexistent_entry_point(client: WorkspaceClient):
    @asset
    def fake(context: AssetExecutionContext, ext_databricks: ExtDatabricks):
        task = _make_submit_task("/fake/fake")
        ext_databricks.run(task=task, context=context)

    with pytest.raises(DagsterExternalExecutionError, match=r"Cannot read the python file"):
        materialize(
            [fake],
            resources={"ext_databricks": ExtDatabricks(client)},
        )
