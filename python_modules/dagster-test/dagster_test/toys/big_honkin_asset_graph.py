import random
from typing import List

from dagster import AssetKey, AssetsDefinition, asset

N_ASSETS = 1000


def generate_big_honkin_assets() -> list[AssetsDefinition]:
    random.seed(5438790)
    assets = []

    for i in range(N_ASSETS):
        non_argument_deps = [
            AssetKey(f"asset_{j}") for j in random.sample(range(i), min(i, random.randint(0, 3)))
        ]

        @asset(
            name=f"asset_{i}",
            deps=non_argument_deps,
            tags={
                "test": "hi",
                "a-super-super-duper-super-longkey": "A-SUPER-DUPER-DUPER-DUPER-DUPER-LONG-VALUE",
            },
        )
        def some_asset():
            pass

        assets.append(some_asset)

    return assets


assets = generate_big_honkin_assets()
