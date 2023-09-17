from typing import Sequence

from dagster import multi_asset
from dagster._core.definitions.asset_spec import (
    SYSTEM_METADATA_KEY_EXECUTABLE,
    AssetSpec,
    ObservableAssetSpec,
)


def create_observable_assets_def(specs: Sequence[ObservableAssetSpec]):
    @multi_asset(
        specs=[
            AssetSpec(
                key=spec.key,
                description=spec.description,
                group_name=spec.group_name,
                metadata={
                    **(spec.metadata or {}),
                    **{SYSTEM_METADATA_KEY_EXECUTABLE: False},
                },
                deps=[dep.asset_key for dep in spec.deps],
            )
            for spec in specs
        ]
    )
    def an_asset() -> None:
        raise NotImplementedError()

    return an_asset
