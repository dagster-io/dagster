import dagster as dg

daily_partitions = dg.DailyPartitionsDefinition(start_date="2024-01-01")


@dg.asset(
    partitions_def=daily_partitions,
    backfill_policy=dg.BackfillPolicy.multi_run(max_partitions_per_run=10),
)
def daily_events(context: dg.AssetExecutionContext):
    """Process events for a batch of days in each run."""
    partition_keys = context.partition_keys
    context.log.info(f"Processing {len(partition_keys)} partitions in this run")

    # Process data for all partitions in this batch
    all_events = []
    for partition_key in partition_keys:
        events = fetch_events_for_date(partition_key)
        all_events.extend(events)

    processed = transform_events(all_events)
    context.log.info(f"Processed {len(processed)} total events across {len(partition_keys)} days")
    return processed


def fetch_events_for_date(date: str) -> list:
    # Simulate fetching events for a specific date
    return [{"date": date, "event_id": i} for i in range(100)]


def transform_events(events: list) -> list:
    # Simulate transformation
    return [{"processed": True, **e} for e in events]
