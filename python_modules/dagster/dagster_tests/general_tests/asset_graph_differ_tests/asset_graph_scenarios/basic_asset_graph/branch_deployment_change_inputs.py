import dagster as dg


@dg.asset
def upstream():
    return 1


@dg.asset
def downstream():
    return 2


defs = dg.Definitions(assets=[upstream, downstream])
