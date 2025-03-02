from dagster import asset


@asset
def asset_two() -> str:
    return "asset_one"
