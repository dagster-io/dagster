from dagster import (asset, Definitions, SourceAsset, AssetKey)

config_data = SourceAsset(key=AssetKey("config_data"))

@asset
def file2_asset1(config_data):
    return config_data + 1

@asset
def file2_asset2(config_data):
    return config_data + 2

defs = Definitions(assets=[config_data, file2_asset1, file2_asset2])r
