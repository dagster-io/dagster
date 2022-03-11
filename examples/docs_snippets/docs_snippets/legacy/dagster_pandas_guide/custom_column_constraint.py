from datetime import datetime

from dagster_pandas import PandasColumn, create_dagster_pandas_dataframe_type
from dagster_pandas.constraints import (
    ColumnConstraint,
    ColumnConstraintViolationException,
    ColumnDTypeInSetConstraint,
)
from pandas import DataFrame, read_csv

from dagster import Out, job, op
from dagster._utils import script_relative_path


# start_custom_col
class DivisibleByFiveConstraint(ColumnConstraint):
    def __init__(self):
        message = "Value must be divisible by 5"
        super(DivisibleByFiveConstraint, self).__init__(
            error_description=message, markdown_description=message
        )

    def validate(self, dataframe, column_name):
        rows_with_unexpected_buckets = dataframe[
            dataframe[column_name].apply(lambda x: x % 5 != 0)
        ]
        if not rows_with_unexpected_buckets.empty:
            raise ColumnConstraintViolationException(
                constraint_name=self.name,
                constraint_description=self.error_description,
                column_name=column_name,
                offending_rows=rows_with_unexpected_buckets,
            )


CustomTripDataFrame = create_dagster_pandas_dataframe_type(
    name="CustomTripDataFrame",
    columns=[
        PandasColumn(
            "amount_paid",
            constraints=[
                ColumnDTypeInSetConstraint({"int64"}),
                DivisibleByFiveConstraint(),
            ],
        )
    ],
)
# end_custom_col


@op(out=Out(CustomTripDataFrame))
def load_custom_trip_dataframe() -> DataFrame:
    return read_csv(
        script_relative_path("./ebike_trips.csv"),
        parse_dates=["start_time", "end_time"],
        date_parser=lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S.%f"),
        dtype={"color": "category"},
    )


@job
def custom_column_constraint_trip():
    load_custom_trip_dataframe()
