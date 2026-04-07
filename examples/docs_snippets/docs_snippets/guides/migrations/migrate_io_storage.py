from dagster_aws.s3 import S3PickleIOManager, S3Resource

import dagster as dg

# start_migrate_io_storage

# Destination IO manager: the IO manager for your new Hybrid deployment.
destination_io_manager = S3PickleIOManager(
    s3_resource=S3Resource(region_name="us-west-2"),
    s3_bucket="my-hybrid-bucket",
    s3_prefix="dagster/storage",
)


@dg.asset
def my_asset(): ...


@dg.asset(partitions_def=dg.DailyPartitionsDefinition(start_date="2024-01-01"))
def my_daily_asset(): ...


@dg.op
def run_migration(context: dg.OpExecutionContext):
    result = dg.migrate_io_storage(
        context=context,
        destination_io_manager=destination_io_manager,
    )
    total_migrated = sum(s.size for s in result.migrated)
    total_failed = sum(s.size for s in result.failed)
    context.log.info(f"Migrated {total_migrated} assets, {total_failed} failed")


@dg.job
def migration_job():
    run_migration()


defs = dg.Definitions(assets=[my_asset, my_daily_asset], jobs=[migration_job])

# end_migrate_io_storage
