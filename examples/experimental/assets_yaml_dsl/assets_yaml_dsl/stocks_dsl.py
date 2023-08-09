from typing import Any, Dict, List
import os
import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from dagster import AssetKey, asset, AssetsDefinition


def load_yaml() -> Dict[str, Any]:
    path = os.path.join(os.path.dirname(__file__), "assets.yaml")
    with open(path, "r", encoding="utf8") as ff:
        return yaml.load(ff, Loader=Loader)


stocks_dsl_document = load_yaml()


def assets_defs_from_stocks_dsl_document(
    stocks_dsl_document: Dict[Any, str]
) -> List[AssetsDefinition]:
    stocks_dsl_document["stocks_to_index"]
    ...


stocks_dsl_document = load_yaml()


def get_ticker_data(ticker: str) -> str:
    return f"Data from api about {ticker}"


def assets_defs_from_stocks_dsl_document(
    stocks_dsl_document: Dict[Any, Dict]
) -> List[AssetsDefinition]:
    outs = {}
    tickers = []
    for stock_block in stocks_dsl_document["stocks_to_index"]:
        ticker = stock_block["ticker"]
        outs[ticker] = AssetOut(key=AssetKey(ticker), description=f"Stock {ticker}")
        tickers.append(ticker)

    @multi_asset(outs=outs)
    def fetch_the_tickers():
        for ticker in tickers:
            get_ticker_data(ticker)

    return [fetch_the_tickers]
