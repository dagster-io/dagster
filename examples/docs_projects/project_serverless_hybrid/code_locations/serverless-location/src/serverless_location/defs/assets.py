import dagster as dg


@dg.asset(
    kinds={"duckdb", "api"},
    description="Fetches raw user events from an API endpoint and stores in DuckDB",
)
def raw_user_events(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    """Ingest raw user event data from API."""
    context.log.info("Ingesting raw user events on Dagster+ Serverless...")
    return dg.MaterializeResult(metadata={"num_events": 1500})


@dg.asset(
    kinds={"duckdb", "python"},
    description="Cleans and normalizes raw user events",
    deps=[raw_user_events],
)
def cleaned_user_events(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    """Clean and normalize user event data."""
    context.log.info("Cleaning user events...")
    return dg.MaterializeResult(metadata={"num_cleaned": 1400})


@dg.asset(
    kinds={"duckdb", "analytics"},
    description="Aggregates user events into daily metrics",
    deps=[cleaned_user_events],
)
def daily_user_metrics(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    """Aggregate cleaned events into daily metrics."""
    context.log.info("Computing daily metrics...")
    return dg.MaterializeResult(metadata={"num_days": 30})


@dg.asset(
    kinds={"duckdb", "analytics"},
    description="Creates user engagement scores based on activity metrics",
    deps=[daily_user_metrics],
)
def user_engagement_scores(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    """Calculate user engagement scores from daily metrics."""
    context.log.info("Computing engagement scores...")
    return dg.MaterializeResult(metadata={"num_users": 350})
