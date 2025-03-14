import dagster as dg


@dg.asset
def a2() -> None: ...


defs = dg.Definitions(assets=[a2])
