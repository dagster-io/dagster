import pytest
from dagster_duckdb import DuckDBResource

import dagster as dg
import docs_snippets.guides.tutorials.etl_tutorial.src.etl_tutorial.defs
from docs_snippets.guides.tutorials.etl_tutorial.src.etl_tutorial.defs import assets


@pytest.fixture()
def defs():
    return dg.Definitions.merge(
        dg.components.load_defs(
            docs_snippets.guides.tutorials.etl_tutorial.src.etl_tutorial.defs
        )
    )


@pytest.fixture()
def duckdb_resource():
    return DuckDBResource(database="/tmp/jaffle_platform.duckdb")


def test_defs(defs):
    assert defs
    assert len(defs.assets) == 7
    assert len(defs.asset_checks) == 1
    assert defs.resources["duckdb"] is not None
    assert len(defs.sensors) == 1


def test_materialize_partition(defs, duckdb_resource):
    result = dg.materialize(
        assets=[
            defs.get_assets_def(dg.AssetKey(["target", "main", "raw_customers"])),
            defs.get_assets_def(dg.AssetKey(["target", "main", "raw_orders"])),
            defs.get_assets_def(dg.AssetKey(["target", "main", "raw_payments"])),
            defs.get_assets_def(dg.AssetKey(["target", "main", "stg_customers"])),
            defs.get_assets_def(dg.AssetKey(["target", "main", "stg_orders"])),
            defs.get_assets_def(dg.AssetKey(["target", "main", "stg_payments"])),
            defs.get_assets_def("monthly_orders"),
        ],
        resources={
            "duckdb": duckdb_resource,
        },
        partition_key="2024-01-01",
    )
    assert result.success
