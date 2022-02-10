import os

import pandas as pd
from bollinger.lib import SP500_CSV_URL, download_file, normalize_path, compute_bollinger_bands
from bollinger.resources.csv_io_manager import local_csv_io_manager
from dagster.core.asset_defs import asset, build_assets_job


@asset
def sp500_prices():
    path = normalize_path("all_stocks_5yr.csv")
    if not os.path.exists(path):
        download_file(SP500_CSV_URL, path)
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.rename(columns={"Name": "name"})
    df = df.dropna()
    return df


@asset
def sp500_bollinger_bands(sp500_prices):
    odf = sp500_prices.groupby("name").apply(lambda idf: compute_bollinger_bands(idf, dropna=False))
    return odf.dropna().reset_index()


@asset
def sp500_anomalous_events(sp500_prices, sp500_bollinger_bands):
    df = pd.concat([sp500_prices, sp500_bollinger_bands.add_prefix("bol_")], axis=1)
    df["event"] = pd.Series(
        pd.NA, index=df.index, dtype=pd.CategoricalDtype(categories=["high", "low"])
    )
    df["event"][df["close"] > df["bol_upper"]] = "high"
    df["event"][df["close"] < df["bol_lower"]] = "low"
    return df[df["event"].notna()][["name", "date", "event"]].reset_index()


# NOTE: The CSV IO manager assumes the presence of schema metadata and therefore does not work with
# this.
bollinger_sda_inline_basic = build_assets_job(
    "bollinger_sda",
    assets=[sp500_anomalous_events, sp500_bollinger_bands, sp500_prices],
)
