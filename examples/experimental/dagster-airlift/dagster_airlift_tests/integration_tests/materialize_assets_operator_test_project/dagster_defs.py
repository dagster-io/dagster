from dagster import Definitions, asset


@asset
def some_asset():
    return "asset_value"


@asset
def other_asset():
    return "other_asset_value"


@asset(key=["nested", "asset"])
def nested_asset():
    return "nested_asset_value"


defs = Definitions(assets=[some_asset, other_asset, nested_asset])
