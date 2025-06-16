# pyright: reportMissingImports=none

import dagster as dg

from .resources import MyAssetConfig


@dg.asset
def greeting(config: MyAssetConfig) -> str:
    return f"hello {config.person_name}"


asset_result = dg.materialize(
    [greeting],
    run_config=dg.RunConfig({"greeting": MyAssetConfig(non_existent_config_value=1)}),
)
