from dagster import AssetIn, AssetKey, asset

# One way of providing explicit asset keys:


@asset(ins={"upstream": AssetIn(asset_key="upstream_asset")})
def downstream_asset(upstream):
    return upstream + [4]


# Another way:


@asset(ins={"upstream": AssetIn(asset_key=AssetKey("upstream_asset"))})
def another_downstream_asset(upstream):
    return upstream + [10]
