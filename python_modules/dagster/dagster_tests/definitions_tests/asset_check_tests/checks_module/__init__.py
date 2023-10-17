from dagster import asset, asset_check


@asset
def asset_1():
    pass


@asset_check(asset=asset_1)
def asset_check_1():
    pass
