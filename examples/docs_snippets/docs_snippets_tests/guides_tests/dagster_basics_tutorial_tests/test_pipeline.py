import dagster as dg
from dagster.components.testing.utils import create_defs_folder_sandbox
from docs_snippets.guides.tutorials.dagster_tutorial.src.dagster_tutorial.components.tutorial import (
    Tutorial,
)
from docs_snippets.guides.tutorials.dagster_tutorial.src.dagster_tutorial.defs.assets import (
    customers,
    orders,
    orders_aggregation,
    payments,
)
from docs_snippets.guides.tutorials.dagster_tutorial.src.dagster_tutorial.defs.resources import (
    database_resource,
)

yaml_config = {
    "type": "docs_snippets.guides.tutorials.dagster_tutorial.src.dagster_tutorial.components.tutorial.Tutorial",
    "attributes": {
        "duckdb_database": "/tmp/jaffle_platform.duckdb",
        "etl_steps": [
            {
                "url_path": "https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_customers.csv",
                "table": "customers",
            },
            {
                "url_path": "https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_orders.csv",
                "table": "orders",
            },
            {
                "url_path": "https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_payments.csv",
                "table": "payments",
            },
        ],
    },
}


def test_pipeline():
    """Ensure pipeline works with asset version of assets."""
    result = dg.materialize(
        assets=[
            customers,
            orders,
            payments,
            orders_aggregation,
        ],
        resources={
            "duckdb": database_resource,
        },
    )
    assert result.success


def test_pipeline_components():
    """Ensure pipeline works with component version of assets."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(component_cls=Tutorial)
        sandbox.scaffold_component(
            component_cls=Tutorial, defs_path=defs_path, defs_yaml_contents=yaml_config
        )

        # Check that all assets are created
        with sandbox.build_all_defs() as sandbox_defs:
            assert sandbox_defs.resolve_asset_graph().get_all_asset_keys() == {
                dg.AssetKey(["customers"]),
                dg.AssetKey(["orders"]),
                dg.AssetKey(["payments"]),
            }

            result = dg.materialize(
                assets=[
                    sandbox_defs.get_assets_def(dg.AssetKey(["customers"])),
                    sandbox_defs.get_assets_def(dg.AssetKey(["orders"])),
                    sandbox_defs.get_assets_def(dg.AssetKey(["payments"])),
                    orders_aggregation,
                ],
                resources={
                    "duckdb": database_resource,
                },
            )
            assert result.success
