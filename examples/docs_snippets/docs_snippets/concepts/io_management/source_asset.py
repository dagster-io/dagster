from dagster import AssetKey, AssetSpec, Definitions, asset

my_source_asset = AssetSpec(key=AssetKey("my_source_asset")).with_io_manager_key(
    "s3_io_manager"
)


@asset
def my_derived_asset(my_source_asset):
    return my_source_asset + [4]


defs = Definitions(assets=[my_source_asset, my_derived_asset])
