import dagster as dg


@dg.asset
def inner() -> None: ...
