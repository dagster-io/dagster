import dagster as dg


@dg.asset
def asset_in_some_file() -> None: ...


@dg.asset
def asset_that_isnt_included() -> None: ...
