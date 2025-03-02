from dagster import asset


@asset
def side_asset() -> str:
    return "side_asset"
