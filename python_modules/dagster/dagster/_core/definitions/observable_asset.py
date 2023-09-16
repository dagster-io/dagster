from typing import Sequence

from dagster._core.definitions.asset_spec import (
    SYSTEM_METADATA_KEY_ASSET_VARIETAL,
    AssetSpec,
    AssetVarietal,
)
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.errors import DagsterInvariantViolationError


def create_unexecutable_observable_assets_def(specs: Sequence[AssetSpec]):
    @multi_asset(
        specs=[
            AssetSpec(
                key=spec.key,
                description=spec.description,
                group_name=spec.group_name,
                metadata={
                    **(spec.metadata or {}),
                    **{SYSTEM_METADATA_KEY_ASSET_VARIETAL: AssetVarietal.UNEXECUTABLE.value},
                },
                deps=[dep.asset_key for dep in spec.deps],
            )
            for spec in specs
        ]
    )
    def an_asset() -> None:
        raise DagsterInvariantViolationError(
            f"You have attempted to execute an unexecutable asset {[spec.key for spec in specs]}"
        )

    return an_asset
