import time

import dagster as dg


@dg.asset(op_tags={"database": "warehouse"})
def warehouse_sync(context: dg.AssetExecutionContext):
    """Tagged asset for tag-based concurrency control."""
    context.log.info("Syncing to warehouse...")
    time.sleep(10)


@dg.asset(op_tags={"database": "warehouse"})
def warehouse_aggregate(context: dg.AssetExecutionContext):
    """Another asset with same tag for concurrency grouping."""
    context.log.info("Aggregating warehouse data...")
    time.sleep(10)


# Job with tag concurrency limits
warehouse_job = dg.define_asset_job(
    name="warehouse_job",
    selection=[warehouse_sync, warehouse_aggregate],
    executor_def=dg.multiprocess_executor.configured(
        {
            "max_concurrent": 4,
            "tag_concurrency_limits": [{"key": "database", "value": "warehouse", "limit": 1}],
        }
    ),
)
