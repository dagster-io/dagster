import json

from dagster import AssetOut, AssetSpec, Output, asset, multi_asset


# start_single_asset
@asset(code_version="1")
def asset_with_version():
    with open("data/asset_with_version.json", "w") as f:
        json.dump(100, f)


# end_single_asset


# start_multi_asset
@multi_asset(
    specs=[AssetSpec(key="a", code_version="1"), AssetSpec(key="b", code_version="2")]
)
def multi_asset_with_versions():
    with open("data/a.json", "w") as f:
        json.dump(100, f)
    with open("data/b.json", "w") as f:
        json.dump(200, f)


# end_multi_asset
