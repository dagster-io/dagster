# start_marker
from dagster import IOManager


class MyIOManager(IOManager):
    def load_input(self, context):
        start_datetime, end_datetime = context.asset_partitions_time_window
        return read_data_in_datetime_range(start_datetime, end_datetime)

    def handle_output(self, context, obj):
        start_datetime, end_datetime = context.asset_partitions_time_window
        return overwrite_data_in_datetime_range(start_datetime, end_datetime, obj)


# end_marker


def read_data_in_datetime_range(*args):
    ...


def overwrite_data_in_datetime_range(*args):
    ...
