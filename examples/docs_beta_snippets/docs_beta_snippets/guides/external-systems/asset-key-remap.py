import dagster as dg


# Upstream asset has multiple parts in asset key
@dg.asset(key=dg.AssetKey(["my_asset", "part1", "part2"]))
def compute_upstream(): ...


# When loading as an input, we map the asset key to a specific input name
@dg.asset(deps=[compute_upstream], ins={"inpt": dg.AssetIn(key=compute_upstream.key)})
def compute_downstream(inpt): ...
