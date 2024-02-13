from datetime import datetime

from dagster_pandas import RowCountConstraint, create_dagster_pandas_dataframe_type
from pandas import DataFrame, read_csv

from dagster import Out, file_relative_path, job, op

# start_create_type
ShapeConstrainedTripDataFrame = create_dagster_pandas_dataframe_type(
    name="ShapeConstrainedTripDataFrame", dataframe_constraints=[RowCountConstraint(4)]
)
# end_create_type


@op(out=Out(ShapeConstrainedTripDataFrame))
def load_shape_constrained_trip_dataframe() -> DataFrame:
    return read_csv(  # type: ignore  # (bad stubs)
        file_relative_path(__file__, "./ebike_trips.csv"),
        parse_dates=["start_time", "end_time"],
        date_parser=lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S.%f"),
        dtype={"color": "category"},
    )


@job
def shape_constrained_trip():
    load_shape_constrained_trip_dataframe()
