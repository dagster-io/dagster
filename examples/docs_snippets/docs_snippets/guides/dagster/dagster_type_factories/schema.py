import pandas as pd
import pandera as pa

MIN_DATE = pd.Timestamp("2021-10-01")

df = pd.read_csv(
    "./ebike_trips.csv",
    parse_dates=["start_time", "end_time"],
)

trips_schema = pa.DataFrameSchema(
    columns={
        "bike_id": pa.Column(
            int, checks=pa.Check.ge(0)
        ),  # ge: greater than or equal to
        "start_time": pa.Column(pd.Timestamp, checks=pa.Check.ge(MIN_DATE)),
        "end_time": pa.Column(pd.Timestamp, checks=pa.Check.ge(MIN_DATE)),
    },
)
