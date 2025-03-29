from dagster import asset


@asset
def an_asset() -> None: ...
