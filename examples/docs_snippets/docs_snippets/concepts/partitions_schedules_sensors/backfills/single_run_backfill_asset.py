# start_marker
from dagster import AssetKey, DailyPartitionsDefinition, asset


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"),
    deps=[AssetKey("raw_events")],
)
def events(context):
    (
        input_start_datetime,
        input_end_datetime,
    ) = context.asset_partitions_time_window_for_input("raw_events")
    input_data = read_data_in_datetime_range(input_start_datetime, input_end_datetime)
    output_data = compute_events_from_raw_events(input_data)

    (
        output_start_datetime,
        output_end_datetime,
    ) = context.asset_partitions_time_window_for_output()
    return overwrite_data_in_datetime_range(
        output_start_datetime,
        output_end_datetime,
        output_data,
    )


# end_marker


def compute_events_from_raw_events(*args):
    ...


def read_data_in_datetime_range(*args):
    ...


def overwrite_data_in_datetime_range(*args):
    ...
