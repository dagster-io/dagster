import dagster as dg


@dg.asset
def innerer() -> None: ...
