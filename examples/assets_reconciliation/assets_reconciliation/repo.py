import datetime

from dagster import AssetIn, Field, asset, input_manager, repository, source_asset, with_resources

# from .lib import (
#     BollingerBandsDgType,
#     StockPricesDgType,
#     compute_anomalous_events,
#     compute_bollinger_bands_multi,
#     load_dummy_source,
# )


@source_asset
def dummy_source(_context):
    for _ in range(10):
        print("RUNNING SOURCE ASSET VERSION FN")
    return str(datetime.datetime.now())


@input_manager
def source_asset_input_manager():
    return 100


@asset(
    # dagster_type=BollingerBandsDgType,
    ins={"dummy_source": AssetIn(input_manager_key="source_asset_input_manager")},
    # config_schema={
    #     "rate": Field(int, default_value=30, description="Size of sliding window in days"),
    #     "sigma": Field(
    #         float, default_value=2.0, description="Width of envelope in standard deviations"
    #     ),
    # },
    # metadata={"owner": "alice@example.com"},
    versioned=True,
)
def dummy_asset(context, dummy_source):
    """Bollinger bands for the S&amp;P 500 stock prices."""
    print("RUNNING $$$DUMMY ASSET$$$")
    return dummy_source + 100


@repository
def repo():
    return [
        # dummy_source,
        # dummy_asset,
        *with_resources(
            [dummy_source, dummy_asset],
            {"source_asset_input_manager": source_asset_input_manager},
        )
    ]
