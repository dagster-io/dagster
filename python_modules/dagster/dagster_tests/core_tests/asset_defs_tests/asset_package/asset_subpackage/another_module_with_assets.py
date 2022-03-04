from dagster import AssetKey, SourceAsset, asset

elvis_presley = SourceAsset(key=AssetKey("patsy_cline"))


@asset
def miles_davis():
    pass
