import imp

import pytest
from airflow import __version__ as airflow_version
from dagster import AssetKey, asset, materialize
from dagster_airflow import (
    load_assets_from_airflow_dag,
)
from dagster_airflow_tests.marks import requires_airflow_db

from ..airflow_utils import COMPLEX_DAG_FILE_CONTENTS_AIRFLOW_2


@pytest.mark.skipif(airflow_version < "2.0.0", reason="requires airflow 2")
@requires_airflow_db
def test_load_assets_from_airflow_dag():
    dag_module = imp.new_module("dag_module")
    exec(COMPLEX_DAG_FILE_CONTENTS_AIRFLOW_2, dag_module.__dict__)

    @asset
    def new_upstream_asset():
        return 1

    assets = load_assets_from_airflow_dag(
        dag=dag_module.complex_dag,
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
        [*assets, new_upstream_asset], tags={"airflow_execution_date": "2021-01-01T00:00:00+00:00"}
    )
    assert result.success
