# pylint: disable=redefined-outer-name
# start_marker
from dagster import asset, define_asset_job, repository


@asset
def asset1():
    return [1, 2, 3]


@asset
def asset2(asset1):
    return asset1 + [4]


all_assets_job = define_asset_job(name="all_assets_job")
asset1_job = define_asset_job(name="asset1_job", selection="asset1")


@repository
def repo():
    return [asset1, asset2, all_assets_job, asset1_job]


# end_marker
