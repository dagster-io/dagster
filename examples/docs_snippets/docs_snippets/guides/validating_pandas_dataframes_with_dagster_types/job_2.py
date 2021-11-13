import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pandera as pa
from dagster import AssetMaterialization, In, Out, job, op

from .factory import pandera_schema_to_dagster_type

MIN_DATE = pd.Timestamp("2021-10-01")

schema = pa.DataFrameSchema(
    columns={
        "bike_id": pa.Column(int, checks=pa.Check.ge(0)),  # ge: greater than or equal to
        "start_time": pa.Column(pd.Timestamp, checks=pa.Check.ge(MIN_DATE)),
        "end_time": pa.Column(pd.Timestamp, checks=pa.Check.ge(MIN_DATE)),
    },
)

# This is a Dagster type that wraps the schema
TripsDataFrame = pandera_schema_to_dagster_type(
    schema, "TripsDataFrame", "DataFrame type for e-bike trips."
)


# We've added a Dagster type for this op's output
@op(out=Out(TripsDataFrame), config_schema={"clean": bool})
def load_trips(context):
    df = pd.read_csv(
        "./ebike_trips.csv",
        parse_dates=["start_time", "end_time"],
    )
    if context.op_config["clean"]:
        df = df[pd.notna(df.end_time)]
    return df


# We've added a Dagster type for this op's input
@op(ins={"trips": In(TripsDataFrame)})
def generate_plots(trips):
    minute_lengths = [x.total_seconds() / 60 for x in trips.end_time - trips.start_time]
    bin_edges = np.histogram_bin_edges(minute_lengths, 15)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set(title="Trip lengths", xlabel="Minutes", ylabel="Count")
    ax.hist(minute_lengths, bins=bin_edges)
    fig.savefig("trip_lengths.png")
    yield AssetMaterialization(
        asset_key="trip_dist_plot", description="Distribution of trip lengths."
    )
    yield Output(None)


@job
def generate_trip_plots():
    generate_plots(load_trips())


# execution_1

generate_trip_plots.execute_in_process()
# => ...
# => dagster.core.errors.DagsterTypeCheckDidNotPass: Type check failed for step output "result" - expected type "TripsDataFrame".
# => ...

# execution_2

generate_trip_plots.execute_in_process(
    run_config={"ops": {"load_trips": {"config": {"clean": True}}}}
)
# => ...
# => 2021-11-11 19:54:26 - dagster - DEBUG - generate_trip_plots - 3e00e9e3-27f3-490e-b1bd-ec17b92e5599 - 28168 - RUN_SUCCESS - Finished execution of run for "generate_trip_plots".
