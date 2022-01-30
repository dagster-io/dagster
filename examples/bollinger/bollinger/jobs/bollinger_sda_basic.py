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
def sp500_bollinger_bands(sp500_prices):
    odf = sp500_prices.groupby("name").apply(lambda idf: compute_bollinger(idf, dropna=False))
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


bollinger_sda_basic = build_assets_job(
    "bollinger_sda_basic",
    assets=[sp500_anomalous_events, sp500_bollinger_bands, sp500_prices],
    resource_defs={"io_manager": local_csv_io_manager},
)
