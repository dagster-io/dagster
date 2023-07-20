from dagster import (
    AssetSelection,
    Definitions,
    asset,
    load_assets_from_current_module,
)
from dagster._core.definitions.asset_reconciliation_sensor import build_asset_reconciliation_sensor


@asset
def root1():
    ...


@asset
def root2():
    ...


@asset
def diamond_left(root1):
    ...


@asset
def diamond_right(root1):
    ...


@asset
def diamond_sink(diamond_left, diamond_right):
    ...


@asset
def after_both_roots(root1, root2):
    ...


defs = Definitions(
    assets=load_assets_from_current_module(
        group_name="eager_reconciliation", key_prefix="eager_reconciliation"
    ),
    sensors=[build_asset_reconciliation_sensor(AssetSelection.groups("eager_reconciliation"))],
)
