from dagster import Definitions
from dagster._core.definitions.asset_spec import (
    AssetSpec,
    ObservableAssetSpec,
)
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.observable_asset import (
    create_observable_assets_def,
)

assets_def = create_observable_assets_def(
    specs=[
        ObservableAssetSpec(
            key="observable_asset_one",
        )
    ]
)
@multi_asset(
    specs=[AssetSpec(
        key="observable_asset_one",
        # metadata={ SYSTEM_METADATA_KEY_EXECUTABLE: False },
        metadata={ "foo": "bar"},
    )]
)
def _todo():
    raise NotImplementedError

defs = Definitions(
    assets=[_todo]
)
