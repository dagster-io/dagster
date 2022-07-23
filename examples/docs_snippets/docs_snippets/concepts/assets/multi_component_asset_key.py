# pylint: disable=redefined-outer-name
# start_marker
from dagster import AssetIn, asset


@asset(key_prefix=["one", "two", "three"])
def upstream_asset():
    return [1, 2, 3]


@asset(ins={"upstream_asset": AssetIn(key_prefix="one/two/three")})
def downstream_asset(upstream_asset):
    return upstream_asset + [4]


# end_marker
