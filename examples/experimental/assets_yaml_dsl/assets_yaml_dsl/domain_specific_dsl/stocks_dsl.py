import os
import shutil
from typing import Any, Dict, Iterable, List, NamedTuple

import yaml
from dagster import _check as check
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.pipes.client import PipesClient
from dagster._core.pipes.context import PipesExecutionResult
from examples.experimental.assets_yaml_dsl.assets_yaml_dsl.asset_graph_execution_node import (
    AssetGraphExecutionNode,
)

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from dagster import AssetKey, AssetsDefinition, asset, file_relative_path
from dagster._core.definitions.asset_spec import AssetSpec


def load_yaml(relative_path: str) -> Dict[str, Any]:
    path = os.path.join(os.path.dirname(__file__), relative_path)
    with open(path, "r", encoding="utf8") as ff:
        return yaml.load(ff, Loader=Loader)


def get_ticker_data(ticker: str) -> str:
    # imagine instead of returning a string, this function fetches data from an external service
    return f"{ticker}-data"


def enrich_and_insert_data(ticker_data) -> None:
    # imagine this modifies the data and inserts it into ouj database
    pass


def fetch_data_for_ticker(ticker: str) -> str:
    # imagine this fetches data from our database
    return f"{ticker}-data-enriched"


class StockInfo(NamedTuple):
    ticker: str


class IndexStrategy(NamedTuple):
    type: str


class Forecast(NamedTuple):
    days: int


class StockAssets(NamedTuple):
    stock_infos: List[StockInfo]
    index_strategy: IndexStrategy
    forecast: Forecast


def build_stock_assets_object(stocks_dsl_document: Dict[str, Dict]) -> StockAssets:
    return StockAssets(
        stock_infos=[
            StockInfo(ticker=stock_block["ticker"])
            for stock_block in stocks_dsl_document["stocks_to_index"]
        ],
        index_strategy=IndexStrategy(type=stocks_dsl_document["index_strategy"]["type"]),
        forecast=Forecast(int(stocks_dsl_document["forecast"]["days"])),
    )


def get_stocks_dsl_example_defs() -> List[AssetsDefinition]:
    stocks_dsl_document = load_yaml("stocks.yaml")
    stock_assets = build_stock_assets_object(stocks_dsl_document)
    return assets_defs_from_stock_assets(stock_assets)


class TickerFetcher(AssetGraphExecutionNode):
    # resource_keys = {"pipes_subprocess_client"}

    def __init__(self, *, asset_specs: List[AssetSpec], tickers: List[str]) -> None:
        self.tickers = tickers
        super().__init__(
            asset_specs, resource_keys={"pipes_subprocess_client"}, op_name="fetch_tickers"
        )

    # TODO generalize to all execution results
    def execute(self, context: AssetExecutionContext) -> Iterable[PipesExecutionResult]:
        # TODO grab this from someplace
        pipes_subprocess_client = check.inst(context.resources.pipes_subprocess_client, PipesClient)
        python_executable = shutil.which("python")
        assert python_executable is not None
        script_path = file_relative_path(__file__, "user_scripts/fetch_the_tickers.py")
        return pipes_subprocess_client.run(
            command=[python_executable, script_path],
            context=context,
            extras={"tickers": self.tickers},
        ).get_results()


class IndexStrategyExecutionNode(AssetGraphExecutionNode):
    def __init__(self, asset_spec: AssetSpec, tickers: List[str]) -> None:
        self.tickers = tickers
        super().__init__([asset_spec], op_name="index_strategy")

    def execute(self, context: AssetExecutionContext) -> None:
        stored_ticker_data = {}
        for ticker in self.tickers:
            stored_ticker_data[ticker] = fetch_data_for_ticker(ticker)


def assets_defs_from_stock_assets(stock_assets: StockAssets) -> List[AssetsDefinition]:
    group_name = "stocks"

    def spec_for_stock_info(stock_info: StockInfo) -> AssetSpec:
        ticker = stock_info.ticker
        return AssetSpec(
            key=AssetKey(ticker),
            group_name=group_name,
            description=f"Fetch {ticker} from internal service",
            metadata={"ticker": ticker},
        )

    tickers = [stock_info.ticker for stock_info in stock_assets.stock_infos]
    ticker_specs = [spec_for_stock_info(stock_info) for stock_info in stock_assets.stock_infos]

    fetch_the_tickers = TickerFetcher(asset_specs=ticker_specs, tickers=tickers).build_assets_def()
    index_strategy = IndexStrategyExecutionNode(
        asset_spec=AssetSpec(
            key="index_strategy",
            group_name=group_name,
            deps=fetch_the_tickers.keys,
        ),
        tickers=tickers,
    ).build_assets_def()

    # @asset(deps=fetch_the_tickers.keys, group_name=group_name)
    # def index_strategy() -> None:
    #     stored_ticker_data = {}
    #     for ticker in tickers:
    #         stored_ticker_data[ticker] = fetch_data_for_ticker(ticker)

    #     # do someting with stored_ticker_data

    @asset(deps=fetch_the_tickers.keys, group_name=group_name)
    def forecast() -> None:
        # do some forecast thing
        pass

    return [fetch_the_tickers, index_strategy, forecast]
