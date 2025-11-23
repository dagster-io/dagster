import pyarrow as pa
from dagster import AssetExecutionContext, asset
from dagster_iceberg.config import UpsertOptions


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
def my_table_typed_upsert(context: AssetExecutionContext):
    context.add_output_metadata({
        "upsert_options": UpsertOptions(
            join_cols=["id", "timestamp"],
            when_matched_update_all=True,
            when_not_matched_insert_all=False,
        )
    })
    ... # return the table to be upserted

