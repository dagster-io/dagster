# start_marker
from dagster import (
    AssetExecutionContext,
    AssetKey,
    BackfillPolicy,
    DailyPartitionsDefinition,
    asset,
)


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"),
    backfill_policy=BackfillPolicy.single_run(),
    deps=[AssetKey("raw_events")],
)
def events(context: AssetExecutionContext):
    start_datetime, end_datetime = context.partition_time_window

    input_data = read_data_in_datetime_range(start_datetime, end_datetime)
    output_data = compute_events_from_raw_events(input_data)

    overwrite_data_in_datetime_range(start_datetime, end_datetime, output_data)


# end_marker


def compute_events_from_raw_events(*args):
    ...


def read_data_in_datetime_range(*args):
    ...


def overwrite_data_in_datetime_range(*args):
    ...
