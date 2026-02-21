import dagster as dg

daily_partitions = dg.DailyPartitionsDefinition(start_date="2024-01-01")


@dg.asset(partitions_def=daily_partitions)
def daily_events(context: dg.AssetExecutionContext):
    """Process events for a single day. Each partition runs separately."""
    partition_date = context.partition_key
    context.log.info(f"Processing events for {partition_date}")

    # Process data for this single partition
    events = fetch_events_for_date(partition_date)
    processed = transform_events(events)

    context.log.info(f"Processed {len(processed)} events for {partition_date}")
    return processed


def fetch_events_for_date(date: str) -> list:
    # Simulate fetching events for a specific date
    return [{"date": date, "event_id": i} for i in range(100)]


def transform_events(events: list) -> list:
    # Simulate transformation
    return [{"processed": True, **e} for e in events]
