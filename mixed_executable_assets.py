from dagster import Definitions, asset
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.observable_asset import create_unexecutable_observable_assets_def

upstream_asset =  create_unexecutable_observable_assets_def([AssetSpec("upstream_asset")])

@asset(deps=[upstream_asset])
def downstream_asset() -> int:
    return 1

defs = Definitions([upstream_asset, downstream_asset])