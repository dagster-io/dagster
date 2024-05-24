from dagster import Definitions, asset


@asset
def upstream():
    return 1


@asset
def downstream(upstream):
    return upstream + 1


@asset
def new_asset():
    return 1


defs = Definitions(assets=[upstream, downstream, new_asset])
