import dagster as dg


@dg.asset
def innerest_defs() -> None: ...


defs = dg.Definitions(assets=[innerest_defs])
