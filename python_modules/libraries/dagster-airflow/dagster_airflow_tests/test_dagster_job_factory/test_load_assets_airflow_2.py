import os
import tempfile

import pytest
from airflow import __version__ as airflow_version
from airflow.models import DagBag
from dagster import AssetKey, asset, materialize
from dagster_airflow import (
    load_assets_from_airflow_dag,
)

from dagster_airflow_tests.marks import requires_airflow_db

ASSET_DAG = """
from airflow import models

from airflow.operators.bash import BashOperator

import datetime

default_args = {"start_date": datetime.datetime(2023, 2, 1)}

with models.DAG(
    dag_id="asset_dag", default_args=default_args, schedule='0 0 * * *', tags=['example'],
) as asset_dag:
    foo = BashOperator(
        task_id="foo", bash_command="echo foo"
    )

    bar = BashOperator(
        task_id="bar", bash_command="echo bar"
    )

    biz = BashOperator(
        task_id="biz", bash_command="echo biz"
    )

    baz = BashOperator(
        task_id="baz", bash_command="echo baz"
    )
"""


@pytest.mark.skipif(airflow_version < "2.0.0", reason="requires airflow 2")
@requires_airflow_db
def test_load_assets_from_airflow_dag():
    with tempfile.TemporaryDirectory(suffix="assets") as tmpdir_path:
        with open(os.path.join(tmpdir_path, "dag.py"), "wb") as f:
            f.write(bytes(ASSET_DAG.encode("utf-8")))

        dag_bag = DagBag(dag_folder=tmpdir_path)
        asset_dag = dag_bag.get_dag(dag_id="asset_dag")

        @asset
        def new_upstream_asset():
            return 1

        assets = load_assets_from_airflow_dag(
            dag=asset_dag,
            task_ids_by_asset_key={
                AssetKey("foo_asset"): {"foo", "bar"},
                AssetKey("biz_asset"): {"biz", "baz"},
            },
            upstream_dependencies_by_asset_key={
                AssetKey("foo_asset"): {
                    AssetKey("new_upstream_asset"),
                },
            },
        )

        result = materialize(
            [*assets, new_upstream_asset],
            partition_key="2023-02-01T00:00:00",
        )
        assert result.success
