from dagster import AssetSelection, build_asset_reconciliation_sensor, repository

asset_a = None

asset_b = None

asset_c = None

# start_asset_reconciliation_sensor


@repository
def repository_1():
    return [
        asset_a,
        asset_b,
        asset_c,
        build_asset_reconciliation_sensor(
            asset_selection=AssetSelection.assets(asset_b, asset_c),
            name="asset_reconciliation_sensor",
        ),
    ]


# end_asset_reconciliation_sensor
