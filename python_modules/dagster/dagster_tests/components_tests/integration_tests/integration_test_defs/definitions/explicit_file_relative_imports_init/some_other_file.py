import dagster as dg


@dg.asset
def asset_in_some_other_file() -> None: ...
