from dagster import asset


@asset
def an_implicit_asset() -> None: ...
