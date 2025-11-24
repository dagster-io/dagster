import pyarrow as pa

from dagster import AssetExecutionContext, asset


@asset(metadata={"write_mode": "overwrite"})
def user_profiles(context: AssetExecutionContext) -> pa.Table:
    context.add_output_metadata({"write_mode": "append"})
    return pa.table(
        {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "updated_at": ["2024-01-01", "2024-01-02", "2024-01-03"],
        }
    )
