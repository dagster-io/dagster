import random
from typing import Sequence

from dagster.core.asset_defs import AssetIn, asset, build_assets_job

N_ASSETS = 1000


def generate_big_honkin_assets() -> Sequence:
    random.seed(5438790)
    assets = []

    for i in range(N_ASSETS):
        ins = {
            f"asset_{j}": AssetIn(managed=False)
            for j in random.sample(range(i), min(i, random.randint(0, 3)))
        }

        @asset(name=f"asset_{i}", ins=ins)
        def some_asset():
            pass

        assets.append(some_asset)

    return assets


big_honkin_assets_job = build_assets_job("big_honkin_assets_job", generate_big_honkin_assets())
