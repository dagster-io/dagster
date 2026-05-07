import random

from dagster import AssetSpec, MaterializeResult, asset, multi_asset


@multi_asset(
    specs=[AssetSpec("asset1", skippable=True), AssetSpec("asset2", skippable=True)]
)
def assets_1_and_2():
    if random.randint(1, 10) < 5:
        yield MaterializeResult(asset_key="asset1")

    if random.randint(1, 10) < 5:
        yield MaterializeResult(asset_key="asset2")


@asset(deps=["asset1"])
def downstream1():
    """Will not run when assets_1_and_2 doesn't materialize asset1."""


@asset(deps=["asset2"])
def downstream2():
    """Will not run when assets_1_and_2 doesn't materialize asset2."""
