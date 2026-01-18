import dagster as dg


def create_large_asset_graph():
    NUM_ASSETS = 1000

    all_assets = []
    for i in range(NUM_ASSETS):
        dep_start = i - 50 if i - 50 > 0 else 0

        @dg.asset(key=f"asset_{i}", deps=[f"asset_{j}" for j in range(dep_start, i, 5)])
        def the_asset():
            return

        all_assets.append(the_asset)

    return all_assets


defs = dg.Definitions(create_large_asset_graph())
