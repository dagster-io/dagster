import pyarrow as pa
from dagster import AssetExecutionContext, asset


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
