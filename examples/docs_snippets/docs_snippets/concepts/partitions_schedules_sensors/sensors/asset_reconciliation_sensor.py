from dagster import AssetSelection, build_asset_reconciliation_sensor, repository

asset1 = None

asset2 = None

asset3 = None

asset4 = None

# start_asset_reconciliation_sensor


@repository
def repository_1():
    return [
        asset1,
        asset2,
        asset3,
        asset4,
        build_asset_reconciliation_sensor(
            asset_selection=AssetSelection.assets(asset1, asset3, asset4),
            name="asset_reconciliation_sensor",
        ),
    ]


# end_asset_reconciliation_sensor
