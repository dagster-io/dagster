import dagster as dg


@dg.asset
def a() -> None: ...


defs = dg.Definitions(assets=[a])
