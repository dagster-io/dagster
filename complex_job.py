import dagster as dg


@dg.asset(kinds={"ducklake"})
def asset():
    pass


defs = dg.Definitions(assets=[asset])
