import dagster as dg


@dg.asset(code_version="1")
def upstream():
    return 1


@dg.asset(code_version="1")
def downstream(upstream):
    return upstream + 1


defs = dg.Definitions(assets=[upstream, downstream])
