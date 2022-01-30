import pandas as pd
from bollinger.lib import compute_bollinger
from bollinger.resources.csv_io_manager import local_csv_io_manager
from dagster.core.asset_defs import asset, build_assets_job


@asset
def sp500_prices():
    path = "examples/bollinger/data/all_stocks_5yr.csv"
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.rename(columns={"Name": "name"})
    df = df.dropna()
    return df


@asset
def bollinger(sp500_prices):
    odf = sp500_prices.groupby("name").apply(lambda idf: compute_bollinger(idf, dropna=False))
    return odf.dropna().reset_index()


@asset
def anomalous_events(bollinger):
    idf = bollinger[
        (bollinger.price > bollinger.upper) | (bollinger.price < bollinger.lower)
    ].reset_index()
    idf["type"] = (
        (idf.price > idf.upper)
        .astype("category")
        .cat.rename_categories({True: "high", False: "low"})
    )
    return idf[["date", "name", "type"]]


bollinger_sda_basic = build_assets_job(
    "bollinger_sda_basic",
    assets=[anomalous_events, bollinger, sp500_prices],
    resource_defs={"io_manager": local_csv_io_manager},
)
