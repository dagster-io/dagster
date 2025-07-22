import dagster as dg


@dg.asset
def new_asset():
    return 1


@dg.asset
def upstream():
    return 1


@dg.asset
def downstream(upstream, new_asset):
    return upstream + new_asset


defs = dg.Definitions(assets=[new_asset, upstream, downstream])
