"""Migration of a Prefect flow to Dagster assets.

Before (Prefect data-processing-flow):

    from prefect import flow, task

    @task
    def fetch_data(): ...          # returns {"records": [...]}

    @task
    def process_data(data): ...    # returns {"total": ..., "count": ...}

    @task
    def save_results(results): ... # persists to storage

    @flow(name="data-processing-flow")
    def data_processing_flow():
        data = fetch_data()
        results = process_data(data)
        save_results(results)

Each Prefect @task becomes a @dg.asset.  The flow's implicit dependency chain
(fetch → process → save) is expressed via deps=.  Schedules are attached the
same way as any other Dagster job.
"""

import dagster as dg


@dg.asset(group_name="prefect_migration")
def extract_records(context: dg.AssetExecutionContext):
    """Fetch records from an API. Mirrors Prefect @task fetch_data."""
    context.log.info("Fetching data from API...")
    records = [{"id": i, "value": i * 10} for i in range(1, 6)]
    context.log.info(f"Fetched {len(records)} records")
    return {"records": records}


@dg.asset(deps=[extract_records], group_name="prefect_migration")
def transform_records(context: dg.AssetExecutionContext):
    """Process extracted records. Mirrors Prefect @task process_data."""
    # In production, load from storage or upstream asset output
    records = [{"id": i, "value": i * 10} for i in range(1, 6)]
    context.log.info(f"Processing {len(records)} records...")
    return {
        "total": sum(r["value"] for r in records),
        "count": len(records),
    }


@dg.asset(deps=[transform_records], group_name="prefect_migration")
def load_records(context: dg.AssetExecutionContext):
    """Persist transformed records. Mirrors Prefect @task save_results."""
    context.log.info("Saving results to storage...")
    # In production, write to your data store here
    return dg.MaterializeResult(
        metadata={
            "rows_written": 5,
        }
    )


_etl_job = dg.define_asset_job(
    "prefect_etl_job",
    selection=[extract_records, transform_records, load_records],
)


@dg.schedule(cron_schedule="0 9 * * *", job=_etl_job)
def prefect_etl_schedule():
    """Daily run replacing Prefect's deployment schedule."""
    yield dg.RunRequest()
