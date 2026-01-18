import pandas as pd

import dagster as dg


@dg.asset
def raw_sales_data() -> pd.DataFrame:
    return pd.read_csv("https://docs.dagster.io/assets/raw_sales_data.csv")


@dg.asset
def clean_sales_data(raw_sales_data: pd.DataFrame) -> pd.DataFrame:
    return raw_sales_data.fillna({"amount": 0.0})


@dg.asset
def sales_summary(clean_sales_data: pd.DataFrame) -> pd.DataFrame:
    return clean_sales_data.groupby(["owner"])["amount"].sum().reset_index()
