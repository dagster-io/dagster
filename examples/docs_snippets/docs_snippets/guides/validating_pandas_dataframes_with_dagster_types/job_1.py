from dagster import AssetMaterialization, job, op
import numpy as np
import pandas as pd
import holoviews as hv

@op
def load_trips():
    return pd.read_csv(
        "./2021-10_ebike_trips.csv",
        parse_dates=["start_time", "end_time"],
    )

@op
def generate_plots(trips):
    minute_lengths = [ x.total_seconds() / 60 for x in trips.end_time - trips.start_time ]
    edges, freqs = np.histogram(minute_lengths, 15)
    hist = hv.Histogram((freqs, edges)).opts(width=600, xlabel='Minutes')
    hv.save(hist, 'trip_length_hist.png', fmt='png')
    yield AssetMaterialization(
        asset_key="trip_dist_plot",
        description="Distribution of trip lengths."
    )
    yield Output(None)

@job
def generate_trip_plots():
    generate_plots(load_trips)
