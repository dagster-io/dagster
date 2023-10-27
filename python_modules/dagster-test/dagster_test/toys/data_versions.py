import datetime

from dagster import (
    AssetOut,
    DataVersion,
    Output,
    SourceAsset,
    asset,
    multi_asset,
    observable_source_asset,
)


@observable_source_asset
def observable_different_version():
    return DataVersion(str(datetime.datetime.now()))


@observable_source_asset
def observable_same_version():
    return DataVersion("5")


non_observable_source = SourceAsset("non_observable_source")


@asset(code_version="1", deps=[observable_different_version])
def has_code_version1(context):
    ...


@asset(code_version="1", deps=[observable_same_version])
def has_code_version2():
    ...


@asset(
    deps=[
        observable_different_version,
        observable_same_version,
        non_observable_source,
    ],
    code_version="1",
)
def has_code_version_multiple_deps():
    ...


@asset(code_version="1", deps=[has_code_version1])
def downstream_of_code_versioned():
    ...


@asset
def root_asset_no_code_version(context):
    return 100


@asset(deps=[root_asset_no_code_version])
def downstream_of_no_code_version():
    ...


@multi_asset(
    outs={
        "code_versioned_multi_asset1": AssetOut(code_version="1"),
        "code_versioned_multi_asset2": AssetOut(code_version="3"),
    },
    deps=[downstream_of_no_code_version],
)
def code_versioned_multi_asset():
    yield Output(None, "code_versioned_multi_asset1")
    yield Output(None, "code_versioned_multi_asset2")


@asset(deps=["code_versioned_multi_asset2"])
def downstream_of_code_versioned_multi_asset():
    ...
