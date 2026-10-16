import copy

import duckdb
from dagster_duckdb import DuckDBResource

import dagster as dg
from dagster.components.testing.utils import create_defs_folder_sandbox
from docs_snippets.dagster_basics_tutorial.src.dagster_tutorial.components.tutorial import (
    Tutorial,
)
from docs_snippets.dagster_basics_tutorial.src.dagster_tutorial.defs.assets import (
    customers,
    orders,
    orders_aggregation,
    payments,
)

yaml_config = {
    "type": "docs_snippets.dagster_basics_tutorial.src.dagster_tutorial.components.tutorial.Tutorial",
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


def test_pipeline(tmp_path):
    """Ensure pipeline works with asset version of assets."""
    db_path = str(tmp_path / "jaffle_platform.duckdb")
    result = dg.materialize(
        assets=[
            customers,
            orders,
            payments,
            orders_aggregation,
        ],
        resources={
            "duckdb": DuckDBResource(database=db_path),
        },
    )
    assert result.success

    with duckdb.connect(db_path) as conn:
        for table_name in [
            "customers",
            "orders",
            "payments",
            "orders_aggregation",
        ]:
            row_count = conn.execute(f"select count(*) from {table_name}").fetchone()[0]
            assert row_count > 0


def test_pipeline_components(tmp_path):
    """Ensure pipeline works with component version of assets."""
    db_path = str(tmp_path / "jaffle_platform.duckdb")
    test_yaml_config = copy.deepcopy(yaml_config)
    test_yaml_config["attributes"]["duckdb_database"] = db_path

    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(component_cls=Tutorial)
        sandbox.scaffold_component(
            component_cls=Tutorial,
            defs_path=defs_path,
            defs_yaml_contents=test_yaml_config,
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
                    "duckdb": DuckDBResource(database=db_path),
                },
            )
            assert result.success

            with duckdb.connect(db_path) as conn:
                for table_name in [
                    "customers",
                    "orders",
                    "payments",
                    "orders_aggregation",
                ]:
                    row_count = conn.execute(
                        f"select count(*) from {table_name}"
                    ).fetchone()[0]
                    assert row_count > 0
