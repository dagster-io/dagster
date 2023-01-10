from dagster import (
    AssetSelection,
    Definitions,
    asset,
    build_asset_reconciliation_sensor,
)


@asset
def a():
    pass


# update code version
@asset(code_version="0.2")
def b(a):
    return "significant change"


@asset
def c(b):
    pass


update_sensor = build_asset_reconciliation_sensor(
    name="update_sensor", asset_selection=AssetSelection.all()
)

defs = Definitions(
    assets=[a, b, c],
    sensors=[update_sensor],
)
