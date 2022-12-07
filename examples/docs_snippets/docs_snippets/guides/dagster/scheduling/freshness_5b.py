from dagster import AssetSelection, asset, build_asset_reconciliation_sensor, repository


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


@repository
def my_repo():
    return [[a, b, c], [update_sensor]]
