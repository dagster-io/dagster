from datetime import datetime

from dagster_pandas import create_dagster_pandas_dataframe_type
from pandas import DataFrame, read_csv

from dagster import EventMetadataEntry, OutputDefinition, pipeline, solid
from dagster.utils import script_relative_path


# start_summary
def compute_trip_dataframe_summary_statistics(dataframe):
    return [
        EventMetadataEntry.text(
            min(dataframe["start_time"]).strftime("%Y-%m-%d"),
            "min_start_time",
            "Date data collection started",
        ),
        EventMetadataEntry.text(
            max(dataframe["end_time"]).strftime("%Y-%m-%d"),
            "max_end_time",
            "Date data collection ended",
        ),
        EventMetadataEntry.text(
            str(dataframe["bike_id"].nunique()),
            "num_unique_bikes",
            "Number of unique bikes that took trips",
        ),
        EventMetadataEntry.text(
            str(len(dataframe)), "n_rows", "Number of rows seen in the dataframe"
        ),
        EventMetadataEntry.text(
            str(dataframe.columns), "columns", "Keys of columns seen in the dataframe"
        ),
    ]


SummaryStatsTripDataFrame = create_dagster_pandas_dataframe_type(
    name="SummaryStatsTripDataFrame", event_metadata_fn=compute_trip_dataframe_summary_statistics
)
# end_summary


@solid(
    output_defs=[
        OutputDefinition(
            name="summary_stats_trip_dataframe", dagster_type=SummaryStatsTripDataFrame
        )
    ]
)
def load_summary_stats_trip_dataframe(_) -> DataFrame:
    return read_csv(
        script_relative_path("./ebike_trips.csv"),
        parse_dates=["start_time", "end_time"],
        date_parser=lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S.%f"),
    )


@pipeline
def summary_stats_pipeline():
    load_summary_stats_trip_dataframe()
