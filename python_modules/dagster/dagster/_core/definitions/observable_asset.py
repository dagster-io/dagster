from typing import Sequence

from dagster import _check as check
from dagster._core.definitions.asset_spec import (
    SYSTEM_METADATA_KEY_ASSET_VARIETAL,
    AssetSpec,
    AssetVarietal,
)
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.errors import DagsterInvariantViolationError


def create_unexecutable_observable_assets_def(specs: Sequence[AssetSpec]):
    new_specs = []
    for spec in specs:
        check.invariant(
            spec.auto_materialize_policy is None,
            "auto_materialize_policy must be None since it is ignored",
        )
        check.invariant(spec.code_version is None, "code_version must be None since it is ignored")
        check.invariant(
            spec.freshness_policy is None, "freshness_policy must be None since it is ignored"
        )
        check.invariant(
            spec.skippable is False,
            "skippable must be False since it is ignored and False is the default",
        )

        new_specs.append(
            AssetSpec(
                key=spec.key,
                description=spec.description,
                group_name=spec.group_name,
                metadata={
                    **(spec.metadata or {}),
                    **{SYSTEM_METADATA_KEY_ASSET_VARIETAL: AssetVarietal.UNEXECUTABLE.value},
                },
                deps=spec.deps,
            )
        )

    @multi_asset(specs=new_specs)
    def an_asset() -> None:
        keys = [spec.key for spec in specs]
        raise DagsterInvariantViolationError(
            f"Asset {keys} is not executable. This is an internal framework error and should have"
            " been caught earlier."
        )

    return an_asset
