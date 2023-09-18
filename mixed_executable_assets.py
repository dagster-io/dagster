from dagster import asset, Definitions
from dagster._core.definitions.asset_spec import ObservableAssetSpec
from dagster._core.definitions.observable_asset import create_unexecutable_observable_assets_def

upstream_asset =  create_unexecutable_observable_assets_def([ObservableAssetSpec("upstream_asset")])

@asset(deps=[upstream_asset])
def downstream_asset():
    return 1

defs = Definitions([upstream_asset, downstream_asset])