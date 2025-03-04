from dagster import asset


@asset
def asset_in_other_file() -> None: ...
