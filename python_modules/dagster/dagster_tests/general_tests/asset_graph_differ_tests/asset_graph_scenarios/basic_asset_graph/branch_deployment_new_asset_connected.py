from dagster import Definitions, asset


@asset
def new_asset():
    return 1


@asset
def upstream():
    return 1


@asset
def downstream(upstream, new_asset):
    return upstream + new_asset


defs = Definitions(assets=[new_asset, upstream, downstream])
