from dagster import asset


@asset
def some_asset() -> None: ...
