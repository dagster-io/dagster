import dagster as dg

daily_partitions = dg.DailyPartitionsDefinition(start_date="2024-01-01")


@dg.asset(
    partitions_def=daily_partitions,
    backfill_policy=dg.BackfillPolicy.single_run(),
)
def daily_events(context: dg.AssetExecutionContext):
    """Process events for multiple days in a single run."""
    start_datetime, end_datetime = context.partition_time_window
    context.log.info(f"Processing events from {start_datetime} to {end_datetime}")

    # Process data for the entire partition range at once
    events = fetch_events_for_range(start_datetime, end_datetime)
    processed = transform_events(events)

    context.log.info(f"Processed {len(processed)} events in single run")
    return processed


def fetch_events_for_range(start, end) -> list:
    # Simulate fetching events for a date range (e.g., SQL WHERE clause)
    return [{"start": str(start), "end": str(end), "event_id": i} for i in range(1000)]


def transform_events(events: list) -> list:
    # Simulate transformation
    return [{"processed": True, **e} for e in events]
