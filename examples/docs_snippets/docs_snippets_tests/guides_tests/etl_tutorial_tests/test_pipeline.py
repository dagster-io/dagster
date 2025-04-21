import dagster as dg
import docs_snippets.guides.tutorials.etl_tutorial.defs.assets as assets
from docs_snippets.guides.tutorials.etl_tutorial.definitions import defs
from docs_snippets.guides.tutorials.etl_tutorial.defs.resources import database_resource


def test_etl_assets_monthly_partition():
    result = dg.materialize(
        assets=[
            assets.products,
            assets.sales_reps,
            assets.sales_data,
            assets.joined_data,
            assets.monthly_sales_performance,
        ],
        resources={
            "database": database_resource,
        },
        partition_key="2024-01-01",
    )
    assert result.success


def test_etl_assets_static_partition():
    result = dg.materialize(
        assets=[
            assets.products,
            assets.sales_reps,
            assets.sales_data,
            assets.joined_data,
            assets.product_performance,
        ],
        resources={
            "database": database_resource,
        },
        partition_key="Books",
    )
    assert result.success


def test_etl_assets_ad_hoc():
    result = dg.materialize(
        assets=[
            assets.products,
            assets.sales_reps,
            assets.sales_data,
            assets.joined_data,
            assets.adhoc_request,
        ],
        resources={
            "database": database_resource,
        },
        run_config=assets.AdhocRequestConfig(
            department="South",
            product="Driftwood Denim Jacket",
            start_date="2024-01-01",
            end_date="2024-06-05",
        ),
    )
    assert result.success


def test_def():
    assert defs
    assert defs.get_schedule_def("analysis_update_job")
    assert defs.get_sensor_def("adhoc_request_sensor")
