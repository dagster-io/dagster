import shutil
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from dagster import AssetKey, file_relative_path
from dagster._core.definitions.asset_dep import AssetDep
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.pipes.subprocess import PipesSubprocessClient
from dagster_components import Component, ComponentLoadContext, ResolvableModel

from .utils import AssetsDefinitionComponent, AssetStepComponent, CompositeComponent, OpSpec


class StockInfo(ResolvableModel):
    ticker: str


class IndexStrategy(ResolvableModel):
    type: str


class Forecast(ResolvableModel):
    days: int


def get_ticker_data(ticker: str) -> str:
    # imagine instead of returning a string, this function fetches data from an external service
    return f"{ticker}-data"


def enrich_and_insert_data(ticker_data) -> None:
    # imagine this modifies the data and inserts it into ouj database
    pass


def fetch_data_for_ticker(ticker: str) -> str:
    # imagine this fetches data from our database
    return f"{ticker}-data-enriched"


class DomainSpecificDslComponent(CompositeComponent, ResolvableModel):
    stock_infos: list[StockInfo]
    index_strategy: IndexStrategy
    forecast: Forecast

    def build_components(self, load_context: ComponentLoadContext) -> Iterable[Component]:
        def spec_for_stock_info(stock_info: StockInfo) -> AssetSpec:
            ticker = stock_info.ticker
            return AssetSpec(
                key=AssetKey(ticker),
                group_name="stocks",
                description=f"Fetch {ticker} from internal service",
            )

        tickers = [stock_info.ticker for stock_info in self.stock_infos]
        ticker_specs = [spec_for_stock_info(stock_info) for stock_info in self.stock_infos]

        return [
            FetchTheTickers(
                op_spec=OpSpec(name="fetch_the_tickers"),
                specs=ticker_specs,
                tickers=tickers,
            ),
            IndexStrategyAsset(
                name="index_strategy", key="index_strategy", group_name="stocks", tickers=tickers
            ),
            ForecastAsset(
                name="forecast",
                key="forecast",
                group_name="stocks",
                deps=AssetDep.from_coercibles(tickers),
            ),
        ]


@dataclass
class FetchTheTickers(AssetsDefinitionComponent):
    tickers: list[str] = field(default_factory=list)

    def execute(self, context: AssetExecutionContext) -> Any:
        python_executable = shutil.which("python")
        assert python_executable is not None
        script_path = file_relative_path(__file__, "user_scripts/fetch_the_tickers.py")
        return (
            PipesSubprocessClient()
            .run(
                command=[python_executable, script_path],
                context=context,
                extras={"tickers": self.tickers},
            )
            .get_results()
        )


@dataclass
class IndexStrategyAsset(AssetStepComponent):
    tickers: list[str] = field(default_factory=list)

    def execute(self, context: AssetExecutionContext):
        stored_ticker_data = {}
        for ticker in self.tickers:
            stored_ticker_data[ticker] = fetch_data_for_ticker(ticker)


class ForecastAsset(AssetStepComponent):
    def execute(self, context: AssetExecutionContext):
        # do some forecast thing
        pass
