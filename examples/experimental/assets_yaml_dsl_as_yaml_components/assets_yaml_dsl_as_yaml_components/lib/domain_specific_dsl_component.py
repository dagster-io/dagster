import shutil

from dagster import Definitions
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster_components import Component, ComponentLoadContext, ResolvableModel

from dagster import AssetKey, AssetsDefinition, asset, file_relative_path, multi_asset
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.pipes.subprocess import PipesSubprocessClient


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


class DomainSpecificDslComponent(Component, ResolvableModel):
    stock_infos: list[StockInfo]
    index_strategy: IndexStrategy
    forecast: Forecast

    def build_defs(self, load_context: ComponentLoadContext) -> Definitions:
        # Add definition construction logic here.
        return Definitions(
            assets=self.build_assets_defs(),
            resources=dict(pipes_subprocess_client=PipesSubprocessClient()),
        )

    def build_assets_defs(self) -> list[AssetsDefinition]:
        group_name = "stocks"

        def spec_for_stock_info(stock_info: StockInfo) -> AssetSpec:
            ticker = stock_info.ticker
            return AssetSpec(
                key=AssetKey(ticker),
                group_name=group_name,
                description=f"Fetch {ticker} from internal service",
            )

        tickers = [stock_info.ticker for stock_info in self.stock_infos]
        ticker_specs = [spec_for_stock_info(stock_info) for stock_info in self.stock_infos]

        @multi_asset(specs=ticker_specs)
        def fetch_the_tickers(
            context: AssetExecutionContext, pipes_subprocess_client: PipesSubprocessClient
        ):
            python_executable = shutil.which("python")
            assert python_executable is not None
            script_path = file_relative_path(__file__, "user_scripts/fetch_the_tickers.py")
            return pipes_subprocess_client.run(
                command=[python_executable, script_path],
                context=context,
                extras={"tickers": tickers},
            ).get_results()

        @asset(deps=fetch_the_tickers.keys, group_name=group_name)
        def index_strategy() -> None:
            stored_ticker_data = {}
            for ticker in tickers:
                stored_ticker_data[ticker] = fetch_data_for_ticker(ticker)

            # do someting with stored_ticker_data

        @asset(deps=fetch_the_tickers.keys, group_name=group_name)
        def forecast() -> None:
            # do some forecast thing
            pass

        return [fetch_the_tickers, index_strategy, forecast]
