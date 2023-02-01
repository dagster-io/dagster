import tempfile
import os
import pytest
from airflow import __version__ as airflow_version
from airflow.models import DagBag
from dagster import AssetKey, asset, materialize
from dagster_airflow import (
    load_assets_from_airflow_dag,
)
from dagster_airflow_tests.marks import requires_airflow_db

from ..airflow_utils import COMPLEX_DAG_FILE_CONTENTS_AIRFLOW_2


@pytest.mark.skipif(airflow_version < "2.0.0", reason="requires airflow 2")
@requires_airflow_db
def test_load_assets_from_airflow_dag():
    with tempfile.TemporaryDirectory(suffix="assets") as tmpdir_path:
        with open(os.path.join(tmpdir_path, "dag.py"), "wb") as f:
            f.write(bytes(COMPLEX_DAG_FILE_CONTENTS_AIRFLOW_2.encode("utf-8")))

        dag_bag = DagBag(dag_folder=tmpdir_path)
        complex_dag = dag_bag.get_dag(dag_id="example_complex")

        @asset
        def new_upstream_asset():
            return 1

        assets = load_assets_from_airflow_dag(
            dag=complex_dag,
            task_ids_by_asset_key={
                AssetKey("foo_asset"): {"create_entry_group_result", "create_entry_group_result2"},
                AssetKey("bar_asset"): {"create_entry_gcs_result", "create_entry_gcs_result2"},
            },
            upstream_dependencies_by_asset_key={
                AssetKey("foo_asset"): {
                    AssetKey("new_upstream_asset"),
                },
            },
        )

        result = materialize(
            [*assets, new_upstream_asset],
            partition_key="2023-02-01",
        )
        assert result.success
