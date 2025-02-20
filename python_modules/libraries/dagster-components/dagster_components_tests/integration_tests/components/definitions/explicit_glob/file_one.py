from dagster import asset


@asset
def file_one_asset() -> None: ...
