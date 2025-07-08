import dagster as dg


@dg.asset
def a() -> None: ...


@dg.asset
def b() -> None: ...


defs1 = dg.Definitions(assets=[a])
defs2 = dg.Definitions(assets=[b])
