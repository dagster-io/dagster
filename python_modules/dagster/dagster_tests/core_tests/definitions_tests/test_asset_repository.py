from dagster.core.asset_defs import asset
from dagster import repository


@asset
def the_asset_1():
    pass


@asset
def the_asset_2():
    pass
