# start_marker
import dagster as dg


class MyIOManager(dg.IOManager):
    def load_input(self, context: dg.InputContext):
        start_datetime, end_datetime = context.asset_partitions_time_window
        return read_data_in_datetime_range(start_datetime, end_datetime)

    def handle_output(self, context: dg.OutputContext, obj):
        start_datetime, end_datetime = context.asset_partitions_time_window
        return overwrite_data_in_datetime_range(start_datetime, end_datetime, obj)


daily_partition = dg.DailyPartitionsDefinition(start_date="2020-01-01")

raw_events = dg.AssetSpec("raw_events", partitions_def=daily_partition)


@dg.asset(
    partitions_def=daily_partition,
    backfill_policy=dg.BackfillPolicy.single_run(),
)
def events(context: dg.AssetExecutionContext, raw_events):
    output_data = compute_events_from_raw_events(raw_events)
    return output_data


# end_marker


def compute_events_from_raw_events(*args): ...


def read_data_in_datetime_range(*args): ...


def overwrite_data_in_datetime_range(*args): ...
