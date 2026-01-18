import dagster as dg


@dg.asset_check(asset="asset_1")  # pyright: ignore[reportArgumentType]
def submodule_check():
    pass
