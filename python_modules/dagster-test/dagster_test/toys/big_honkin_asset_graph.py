import random
from typing import List

from dagster import AssetKey, AssetsDefinition, asset

N_ASSETS = 1000


def generate_big_honkin_assets() -> List[AssetsDefinition]:
    random.seed(5438790)
    assets = []

    for i in range(N_ASSETS):
        upstream_assets = {
            AssetKey(f"asset_{j}") for j in random.sample(range(i), min(i, random.randint(0, 3)))
        }

        @asset(name=f"asset_{i}", upstream_assets=upstream_assets)
        def some_asset():
            pass

        assets.append(some_asset)

    return assets


assets = generate_big_honkin_assets()
