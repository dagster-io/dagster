from dagster import AssetIn, AssetKey, asset


# start_string_example
@asset
def upstream_asset():
    return [1, 2, 3]


@asset(ins={"upstream": AssetIn("upstream_asset")})
def downstream_asset(upstream):
    return upstream + [4]


# end_string_example


# start_explicit_asset_key_example

# One way of providing explicit asset keys:


@asset(ins={"upstream": AssetIn(asset_key="upstream_asset")})
def downstream_asset(upstream):
    return upstream + [4]


# Another way:


@asset(ins={"upstream": AssetIn(asset_key=AssetKey("upstream_asset"))})
def another_downstream_asset(upstream):
    return upstream + [10]


# end_explicit_asset_key_example
