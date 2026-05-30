import dagster as dg


@dg.asset_check(asset="asset_1")
def submodule_check():
    pass
