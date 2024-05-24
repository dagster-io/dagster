from dagster import asset_check


@asset_check(asset="asset_1")
def submodule_check():
    pass
