import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from dagster import AssetMaterialization, job, op


@op
def load_trips():
    return pd.read_csv(
        "./ebike_trips.csv",
        parse_dates=["start_time", "end_time"],
    )


@op
def generate_plot(context, trips):
    minute_lengths = [x.total_seconds() / 60 for x in trips.end_time - trips.start_time]
    bin_edges = np.histogram_bin_edges(minute_lengths, 15)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set(title="Trip lengths", xlabel="Minutes", ylabel="Count")
    ax.hist(minute_lengths, bins=bin_edges)
    fig.savefig("trip_lengths.png")
    context.log_event(
        AssetMaterialization(
            asset_key="trip_dist_plot", description="Distribution of trip lengths."
        )
    )


@job
def generate_trip_distribution_plot():
    generate_plot(load_trips())
