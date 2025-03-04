from dagster import asset


@asset
def asset_in_some_file() -> None: ...
