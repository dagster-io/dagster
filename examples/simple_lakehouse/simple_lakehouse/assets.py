"""Asset definitions for the simple_lakehouse example."""
import pandas as pd
from lakehouse import Column, computed_table, source_table
from pyarrow import date32, float64, string

sfo_q2_weather_sample_table = source_table(
    path="data",
    columns=[Column("tmpf", float64()), Column("valid_date", string())],
)


@computed_table(
    input_assets=[sfo_q2_weather_sample_table],
    columns=[Column("valid_date", date32()), Column("max_tmpf", float64())],
)
def daily_temperature_highs_table(sfo_q2_weather_sample: pd.DataFrame) -> pd.DataFrame:
    """Computes the temperature high for each day"""
    sfo_q2_weather_sample["valid_date"] = pd.to_datetime(sfo_q2_weather_sample["valid"])
    return sfo_q2_weather_sample.groupby("valid_date").max().rename(columns={"tmpf": "max_tmpf"})
