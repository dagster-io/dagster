import importlib.util
import os
import re

import pytest
from dagster_databricks._test_utils import (
    databricks_client,
    temp_dbfs_script,
    upload_dagster_pipes_whl,
)

IS_BUILDKITE = os.getenv("BUILDKITE") is not None

# If we even try to import the sample code in an environment without Databricks credentials (BK),
# we'll get an error.
if not IS_BUILDKITE:
    from dagster._core.definitions.events import AssetKey
    from docs_snippets.guides.dagster.dagster_pipes.databricks.databricks_asset_client import (
        databricks_asset,
        defs as databricks_asset_defs,
    )

    def _get_databricks_script_path():
        db_script_spec = importlib.util.find_spec(
            "docs_snippets.guides.dagster.dagster_pipes.databricks.databricks_script"
        )
        assert db_script_spec and db_script_spec.origin
        return db_script_spec.origin

    def test_databricks_asset(databricks_client, capsys):
        script_file = _get_databricks_script_path()
        # with upload_dagster_pipes_whl(databricks_client) as dagster_pipes_whl_path:
        with temp_dbfs_script(
            databricks_client,
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
