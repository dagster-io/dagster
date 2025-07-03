import dagster as dg


@dg.asset(code_version="1")
def upstream():
    return 1


@dg.asset(code_version="2")
def downstream():
    return 2


defs = dg.Definitions(assets=[upstream, downstream])
