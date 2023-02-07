from dagster import (
    AssetSelection,
    Definitions,
    asset,
    build_asset_reconciliation_sensor,
)


@asset
def asset1():
    pass


@asset
def asset2():
    pass


@asset
def asset3():
    pass


@asset
def asset4():
    pass


# start_asset_reconciliation_sensor


defs = Definitions(
    assets=[asset1, asset2, asset3, asset4],
    sensors=[
        build_asset_reconciliation_sensor(
            asset_selection=AssetSelection.assets(asset1, asset3, asset4),
            name="asset_reconciliation_sensor",
        ),
    ],
)


# end_asset_reconciliation_sensor
