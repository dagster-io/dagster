from dagster import AssetIn, asset


@asset(namespace=["one", "two", "three"])
def upstream_asset():
    return [1, 2, 3]


@asset(ins={"upstream": AssetIn("upstream_asset")})
def downstream_asset(upstream):
    return upstream + [4]
