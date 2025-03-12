import dagster as dg


@dg.asset
def a1() -> None: ...


defs = dg.Definitions(assets=[a1])
