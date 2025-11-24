import pyarrow as pa
from dagster import AssetExecutionContext, asset


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
    if context.run.tags.get("upsert_join_keys") == "id_and_timestamp":
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
