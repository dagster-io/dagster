from dagster import Definitions, asset


@asset
def in_defs_asset() -> str:
    return "in_defs_asset"


defs = Definitions(
    assets=[in_defs_asset],
)
