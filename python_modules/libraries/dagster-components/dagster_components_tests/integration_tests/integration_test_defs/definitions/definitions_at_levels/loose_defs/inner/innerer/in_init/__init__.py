import dagster as dg


@dg.asset
def in_init() -> None: ...
