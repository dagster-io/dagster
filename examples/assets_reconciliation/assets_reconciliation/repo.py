import datetime

from dagster import AssetIn, asset, input_manager, repository, source_asset, with_resources
from dagster._core.definitions.logical_version import LogicalVersion
from dagster._core.definitions.source_asset import SourceAsset


@source_asset
def foo(_context):
    return LogicalVersion(str(datetime.datetime.now()))


@source_asset
def bar(_context):
    return LogicalVersion(str(datetime.datetime.now()))


baz = SourceAsset("baz")


@input_manager
def source_asset_input_manager():
    return 100


@asset(
    ins={"foo": AssetIn(input_manager_key="source_asset_input_manager")},
    version="1",
)
def alpha(context, foo):
    return foo + 100


@asset(
    ins={"bar": AssetIn(input_manager_key="source_asset_input_manager")},
    version=True,
)
def beta(context, bar):
    return bar + 100


@asset(
    ins={
        "foo": AssetIn(input_manager_key="source_asset_input_manager"),
        "bar": AssetIn(input_manager_key="source_asset_input_manager"),
        "baz": AssetIn(input_manager_key="source_asset_input_manager"),
    },
    version=True,
)
def delta(context, foo, bar, baz):
    return foo + bar + baz + 100


@asset(
    version=True,
)
def epsilon(context, alpha):
    return alpha + 100


@repository
def repo():
    return [
        *with_resources(
            [foo, bar, baz, alpha, beta, delta, epsilon],
            {"source_asset_input_manager": source_asset_input_manager},
        )
    ]
