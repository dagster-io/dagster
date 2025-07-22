import dagster as dg


@dg.asset
def upstream():
    return 1


@dg.asset
def downstream(upstream):
    return upstream + 1


@dg.asset
def new_asset():
    return 1


defs = dg.Definitions(assets=[upstream, downstream, new_asset])
