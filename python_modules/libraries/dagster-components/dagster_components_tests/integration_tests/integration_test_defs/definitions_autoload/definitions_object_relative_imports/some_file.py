from dagster import asset


@asset
def asset_in_some_file() -> None: ...


@asset
def asset_that_isnt_included() -> None: ...
