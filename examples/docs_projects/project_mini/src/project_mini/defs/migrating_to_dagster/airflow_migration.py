"""Migration of an Airflow DAG to Dagster assets.

Before (Airflow simple_sequential_pipeline):

    from airflow.decorators import dag, task

    @task
    def fetch_data(source: str = "api") -> dict: ...

    @task
    def process_data(data: dict) -> dict: ...

    @task
    def save_results(processed: dict) -> str: ...

    @dag(schedule="0 9 * * *", tags=["example", "sequential"])
    def simple_sequential_pipeline():
        data = fetch_data()
        processed = process_data(data)
        save_results(processed)

Each Airflow @task becomes a @dg.asset.  Dependencies are expressed via the
`deps=` argument instead of XCom return values.  The DAG schedule becomes a
@dg.schedule wrapping a define_asset_job.
"""

import dagster as dg


@dg.asset(group_name="airflow_migration", tags={"example": "", "sequential": ""})
def fetch_data(context: dg.AssetExecutionContext):
    """Fetch data from a source. Mirrors Airflow @task fetch_data."""
    source = "api"
    context.log.info(f"Fetching data from {source}")
    return {"source": source, "data": [1, 2, 3, 4, 5]}


@dg.asset(
    deps=[fetch_data],
    group_name="airflow_migration",
    tags={"example": "", "sequential": ""},
)
def process_data(context: dg.AssetExecutionContext):
    """Process fetched data. Mirrors Airflow @task process_data."""
    context.log.info("Processing data from fetch_data")
    return {"source": "api", "processed": [x * 2 for x in [1, 2, 3, 4, 5]]}


@dg.asset(
    deps=[process_data],
    group_name="airflow_migration",
    tags={"example": "", "sequential": ""},
    retry_policy=dg.RetryPolicy(max_retries=3, delay=300),
)
def save_results(context: dg.AssetExecutionContext):
    """Save processed results. Mirrors Airflow @task save_results.

    retry_policy replaces Airflow's default_args retries/retry_delay.
    """
    context.log.info("Saving 5 processed items from api")
    return "Saved 5 items from api"


_sequential_job = dg.define_asset_job(
    "sequential_pipeline_job",
    selection=[fetch_data, process_data, save_results],
)


@dg.schedule(cron_schedule="0 9 * * *", job=_sequential_job)
def daily_9am_schedule():
    """Run the sequential pipeline daily at 9am. Mirrors Airflow schedule='0 9 * * *'."""
    yield dg.RunRequest()
