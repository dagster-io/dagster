from dagster import Definitions, asset, defs_loader


@defs_loader
def defs():
    @asset
    def asset1(): ...

    return Definitions(assets=[asset1])
