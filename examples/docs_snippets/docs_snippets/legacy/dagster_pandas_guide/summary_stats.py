from datetime import datetime

from dagster_pandas import create_dagster_pandas_dataframe_type
from pandas import DataFrame, read_csv

from dagster import Out, job, op
from dagster._utils import script_relative_path


# start_summary
def compute_trip_dataframe_summary_statistics(dataframe):
    return {
        "min_start_time": min(dataframe["start_time"]).strftime("%Y-%m-%d"),
        "max_end_time": max(dataframe["end_time"]).strftime("%Y-%m-%d"),
        "num_unique_bikes": str(dataframe["bike_id"].nunique()),
        "n_rows": len(dataframe),
        "columns": str(dataframe.columns),
    }


SummaryStatsTripDataFrame = create_dagster_pandas_dataframe_type(
    name="SummaryStatsTripDataFrame",
    event_metadata_fn=compute_trip_dataframe_summary_statistics,
)
# end_summary


@op(out=Out(SummaryStatsTripDataFrame))
def load_summary_stats_trip_dataframe() -> DataFrame:
    return read_csv(
        script_relative_path("./ebike_trips.csv"),
        parse_dates=["start_time", "end_time"],
        date_parser=lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S.%f"),
        dtype={"color": "category"},
    )


@job
def summary_stats_trip():
    load_summary_stats_trip_dataframe()
