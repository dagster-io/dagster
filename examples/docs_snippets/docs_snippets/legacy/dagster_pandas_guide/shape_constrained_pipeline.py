from datetime import datetime

from dagster_pandas import RowCountConstraint, create_dagster_pandas_dataframe_type
from pandas import DataFrame, read_csv

from dagster import OutputDefinition, pipeline, solid
from dagster.utils import script_relative_path

# start_create_type
ShapeConstrainedTripDataFrame = create_dagster_pandas_dataframe_type(
    name="ShapeConstrainedTripDataFrame", dataframe_constraints=[RowCountConstraint(4)]
)
# end_create_type


@solid(
    output_defs=[
        OutputDefinition(
            name="shape_constrained_trip_dataframe", dagster_type=ShapeConstrainedTripDataFrame
        )
    ]
)
def load_shape_constrained_trip_dataframe(_) -> DataFrame:
    return read_csv(
        script_relative_path("./ebike_trips.csv"),
        parse_dates=["start_time", "end_time"],
        date_parser=lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S.%f"),
    )


@pipeline
def shape_constrained_pipeline():
    load_shape_constrained_trip_dataframe()
