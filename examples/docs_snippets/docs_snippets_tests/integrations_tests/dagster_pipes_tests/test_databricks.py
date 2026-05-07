import importlib.util
import os
import re

import pytest
from dagster_databricks._test_utils import temp_dbfs_script
from databricks.sdk import WorkspaceClient

import dagster as dg
from dagster._core.test_utils import environ

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


def _get_databricks_script_path():
    db_script_spec = importlib.util.find_spec(
        "docs_snippets.integrations.external_pipelines.dagster_pipes.databricks.databricks_script"
    )
    assert db_script_spec and db_script_spec.origin
    return db_script_spec.origin


@pytest.mark.skipif(
    not IS_BUILDKITE
    or not os.getenv("DATABRICKS_HOST")
    or not os.getenv("DATABRICKS_TOKEN"),
    reason="Requires real Databricks DBFS connectivity (DATABRICKS_HOST/DATABRICKS_TOKEN)",
)
def test_databricks_asset(capsys):
    with environ(
        {
            "DATABRICKS_HOST": os.environ["DATABRICKS_HOST"],
            "DATABRICKS_TOKEN": os.environ["DATABRICKS_TOKEN"],
        }
    ):
        client = WorkspaceClient(
            host=os.environ["DATABRICKS_HOST"],
            token=os.environ["DATABRICKS_TOKEN"],
        )

        from dagster._core.definitions.events import AssetKey
        from docs_snippets.integrations.external_pipelines.dagster_pipes.databricks.databricks_asset_client import (
            databricks_asset,
        )

        databricks_asset_defs = dg.Definitions(assets=[databricks_asset])

        script_file = _get_databricks_script_path()
        # with upload_dagster_pipes_whl(client) as dagster_pipes_whl_path:
        with temp_dbfs_script(
            client,
            script_file=script_file,
            dbfs_path="dbfs:/my_python_script.py",
        ) as script_file:
            job_def = databricks_asset_defs.get_implicit_job_def_for_assets(
                [AssetKey("databricks_asset")],
            )
            assert job_def
            result = job_def.execute_in_process()
            assert result.success

        mats = result.asset_materializations_for_node(databricks_asset.op.name)
        assert mats[0].metadata["some_metric"].value == 101
        captured = capsys.readouterr()
        assert re.search(
            r"This will be forwarded back to Dagster stdout\n",
            captured.out,
            re.MULTILINE,
        )
        assert re.search(
            r"This will be forwarded back to Dagster stderr\n",
            captured.err,
            re.MULTILINE,
        )
