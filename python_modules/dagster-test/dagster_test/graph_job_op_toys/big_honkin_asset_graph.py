import random
from typing import List

from dagster import AssetGroup, AssetKey, asset
from dagster.core.asset_defs.assets import AssetsDefinition

N_ASSETS = 1000


def generate_big_honkin_assets() -> List[AssetsDefinition]:
    random.seed(5438790)
    assets = []

    for i in range(N_ASSETS):
        non_argument_deps = {
            AssetKey(f"asset_{j}") for j in random.sample(range(i), min(i, random.randint(0, 3)))
        }

        # pylint: disable=cell-var-from-loop; (false positive)
        @asset(name=f"asset_{i}", non_argument_deps=non_argument_deps)
        def some_asset():
            pass

        assets.append(some_asset)

    return assets


big_honkin_asset_group = AssetGroup(generate_big_honkin_assets())
