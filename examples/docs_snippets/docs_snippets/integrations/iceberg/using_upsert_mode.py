import pyarrow as pa
from dagster_iceberg.config import IcebergCatalogConfig, UpsertOptions
from dagster_iceberg.io_manager.arrow import PyArrowIcebergIOManager

from dagster import AssetExecutionContext, Definitions, asset

CATALOG_URI = "sqlite:////home/vscode/workspace/.tmp/examples/catalog.db"
CATALOG_WAREHOUSE = "file:///home/vscode/workspace/.tmp/examples/warehouse"

resources = {
    "io_manager": PyArrowIcebergIOManager(
        name="test",
        config=IcebergCatalogConfig(
            properties={"uri": CATALOG_URI, "warehouse": CATALOG_WAREHOUSE}
        ),
        namespace="dagster",
    )
}


# start_basic_upsert


@asset(
    metadata={
        "write_mode": "upsert",
        "upsert_options": {
            "join_cols": ["id"],  # Columns to join on for matching
            "when_matched_update_all": True,  # Update all columns when matched
            "when_not_matched_insert_all": True,  # Insert all columns when not matched
        },
    }
)
def user_profiles(context: AssetExecutionContext) -> pa.Table:
    # Returns a table with user profiles
    # Rows with matching 'id' will be updated
    # Rows with new 'id' values will be inserted
    return pa.table(
        {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "updated_at": ["2024-01-01", "2024-01-02", "2024-01-03"],
        }
    )


# end_basic_upsert


# start_dynamic_upsert


@asset(
    metadata={
        "write_mode": "upsert",
        "upsert_options": {
            "join_cols": ["id"],
            "when_matched_update_all": True,
            "when_not_matched_insert_all": True,
        },
    }
)
def user_profiles_dynamic(context: AssetExecutionContext) -> pa.Table:
    # Override upsert options at runtime based on business logic
    if context.run.tags.get("update_mode") == "id_and_timestamp":
        context.add_output_metadata(
            {
                "upsert_options": {
                    "join_cols": ["id", "timestamp"],  # Join on multiple columns
                    "when_matched_update_all": False,
                    "when_not_matched_insert_all": False,
                }
            }
        )

    return pa.table(
        {
            "id": [1, 2, 3],
            "timestamp": ["2024-01-01", "2024-01-01", "2024-01-01"],
            "name": ["Alice", "Bob", "Charlie"],
        }
    )


# end_dynamic_upsert


# start_typed_upsert


@asset(
    metadata={
        "write_mode": "upsert",
        "upsert_options": UpsertOptions(
            join_cols=["id", "timestamp"],
            when_matched_update_all=True,
            when_not_matched_insert_all=True,
        ),
    }
)
def my_table_typed_upsert(context: AssetExecutionContext, my_table: pa.Table):
    context.add_output_metadata(
        {
            "upsert_options": UpsertOptions(
                join_cols=["id", "timestamp"],
                when_matched_update_all=True,
                when_not_matched_insert_all=False,
            )
        }
    )


# end_typed_upsert


defs = Definitions(
    assets=[user_profiles, user_profiles_dynamic, my_table_typed_upsert],
    resources=resources,
)

