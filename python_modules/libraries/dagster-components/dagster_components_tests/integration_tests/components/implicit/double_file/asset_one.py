from dagster import asset


@asset
def asset_one() -> str:
    return "asset_one"
