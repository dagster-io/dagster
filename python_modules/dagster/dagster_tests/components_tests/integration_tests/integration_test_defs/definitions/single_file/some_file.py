import dagster as dg


@dg.asset
def an_asset() -> None: ...
