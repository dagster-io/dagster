import dagster as dg


@dg.asset
def b() -> None: ...


defs = dg.Definitions(assets=[b])
