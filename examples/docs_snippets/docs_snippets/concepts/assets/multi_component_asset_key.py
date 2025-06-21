# start_marker
import dagster as dg


@dg.asset(key_prefix=["one", "two", "three"])
def upstream_asset():
    return [1, 2, 3]


@dg.asset(ins={"upstream_asset": dg.AssetIn(key_prefix=["one", "two", "three"])})
def downstream_asset(upstream_asset):
    return upstream_asset + [4]


# end_marker
