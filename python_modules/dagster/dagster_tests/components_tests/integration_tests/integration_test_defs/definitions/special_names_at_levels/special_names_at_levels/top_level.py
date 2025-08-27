import dagster as dg


@dg.asset
def top_level() -> None: ...
