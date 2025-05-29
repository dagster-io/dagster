import pytest
from dagster_duckdb import DuckDBResource

import dagster as dg
import docs_snippets.guides.tutorials.etl_tutorial.defs.assets as assets
from docs_snippets.guides.tutorials.etl_tutorial.defs.resources import database_resource


@pytest.fixture()
def duckdb_resource():
    return DuckDBResource(
        database="docs_snippets/guides/tutorials/etl_tutorial/data/mydb.duckdb"
    )


def test_etl_assets_monthly_partition(duckdb_resource):
    result = dg.materialize(
        assets=[
            assets.products,
            assets.sales_reps,
            assets.sales_data,
            assets.joined_data,
            assets.monthly_sales_performance,
        ],
        resources={
            "duckdb": duckdb_resource,
        },
        partition_key="2024-01-01",
    )
    assert result.success


def test_etl_assets_static_partition(duckdb_resource):
    result = dg.materialize(
        assets=[
            assets.products,
            assets.sales_reps,
            assets.sales_data,
            assets.joined_data,
            assets.product_performance,
        ],
        resources={
            "duckdb": duckdb_resource,
        },
        partition_key="Books",
    )
    assert result.success


def test_etl_assets_ad_hoc(duckdb_resource):
    result = dg.materialize(
        assets=[
            assets.products,
            assets.sales_reps,
            assets.sales_data,
            assets.joined_data,
            assets.adhoc_request,
        ],
        resources={
            "duckdb": duckdb_resource,
        },
        run_config=dg.RunConfig(
            {
                "adhoc_request": assets.AdhocRequestConfig(
                    department="South",
                    product="Driftwood Denim Jacket",
                    start_date="2024-01-01",
                    end_date="2024-06-05",
                ),
            }
        ),
    )
    assert result.success
