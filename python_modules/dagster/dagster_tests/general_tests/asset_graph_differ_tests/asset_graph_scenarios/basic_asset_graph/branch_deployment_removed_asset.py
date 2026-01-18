import dagster as dg


@dg.asset
def upstream():
    return 1


defs = dg.Definitions(assets=[upstream])
