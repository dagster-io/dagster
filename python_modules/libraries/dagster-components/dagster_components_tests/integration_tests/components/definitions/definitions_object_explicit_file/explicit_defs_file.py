from dagster import Definitions, asset


@asset
def explicit_defs_asset() -> None: ...


defs = Definitions([explicit_defs_asset])
