from dagster import AssetSelection, asset, define_asset_job


@asset(group_name="basic_assets")
def basic_asset_1():
    ...


@asset(group_name="basic_assets")
def basic_asset_2(basic_asset_1):
    ...


@asset(group_name="basic_assets")
def basic_asset_3(basic_asset_1):
    ...


@asset(group_name="basic_assets")
def basic_asset_4(basic_asset_2, basic_asset_3):
    ...


basic_assets_job = define_asset_job(
    "basic_assets_job", selection=AssetSelection.groups("basic_assets")
)
