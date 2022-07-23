from datetime import datetime

from dagster_pandas import PandasColumn, create_dagster_pandas_dataframe_type
from pandas import DataFrame, read_csv

from dagster import Out, job, op
from dagster._utils import script_relative_path

# start_core_trip_marker_0
TripDataFrame = create_dagster_pandas_dataframe_type(
    name="TripDataFrame",
    columns=[
        PandasColumn.integer_column("bike_id", min_value=0),
        PandasColumn.categorical_column("color", categories={"red", "green", "blue"}),
        PandasColumn.datetime_column(
            "start_time", min_datetime=datetime(year=2020, month=2, day=10)
        ),
        PandasColumn.datetime_column(
            "end_time", min_datetime=datetime(year=2020, month=2, day=10)
        ),
        PandasColumn.string_column("station"),
        PandasColumn.exists("amount_paid"),
        PandasColumn.boolean_column("was_member"),
    ],
)
# end_core_trip_marker_0

# start_core_trip_marker_1
@op(out=Out(TripDataFrame))
def load_trip_dataframe() -> DataFrame:
    return read_csv(
        script_relative_path("./ebike_trips.csv"),
        parse_dates=["start_time", "end_time"],
        date_parser=lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S.%f"),
        dtype={"color": "category"},
    )


# end_core_trip_marker_1


@job
def core_trip():
    load_trip_dataframe()
