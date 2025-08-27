import dagster as dg

patsy_cline = dg.SourceAsset(key=dg.AssetKey("patsy_cline"))


@dg.asset
def miles_davis():
    pass
