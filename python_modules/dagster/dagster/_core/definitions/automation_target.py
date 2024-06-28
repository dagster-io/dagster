from typing import Any, NamedTuple, Sequence, Union

from typing_extensions import TypeAlias

import dagster._check as check
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_selection import AssetSelection, CoercibleToAssetSelection
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.source_asset import SourceAsset

from .target import ExecutableDefinition
from .unresolved_asset_job_definition import define_asset_job

CoercibleToAutomationTarget: TypeAlias = Union[
    CoercibleToAssetSelection, AssetsDefinition, ExecutableDefinition
]


class AutomationTarget(NamedTuple):
    target_executable: ExecutableDefinition
    passed_assets_defs: Sequence[AssetsDefinition]


def ensure_compatible_sequence(
    potential_target: Sequence[Any],
) -> Sequence[Union[str, AssetKey, AssetsDefinition, SourceAsset]]:
    return check.is_list(
        list(potential_target),
        of_type=(str, AssetKey, AssetsDefinition, SourceAsset),
        additional_message=(
            "If you pass a sequence to a schedule, it must be a sequence of strings, "
            "AssetKeys, AssetsDefinitions, or SourceAssets"
        ),
    )


def is_coercible_to_asset_selection(target: Any) -> bool:
    if isinstance(target, (str, AssetSelection)):
        return True

    if isinstance(target, Sequence):
        ensure_compatible_sequence(target)
        return True

    return False


def resolve_automation_target(
    automation_name: str,
    target: CoercibleToAutomationTarget,
) -> AutomationTarget:
    from dagster._core.definitions.assets import AssetsDefinition
    from dagster._core.definitions.source_asset import SourceAsset

    passed_assets_defs = []

    if isinstance(target, Sequence):
        ensure_compatible_sequence(target)

    if isinstance(target, AssetsDefinition):
        asset_selection = AssetSelection.assets(target)
        passed_assets_defs = [target]
    elif is_coercible_to_asset_selection(target):
        if isinstance(target, Sequence):
            for individual_target in target:
                if isinstance(individual_target, (AssetsDefinition, SourceAsset)):
                    passed_assets_defs.append(individual_target)

        asset_selection = AssetSelection.from_coercible(target)  # type: ignore
    elif isinstance(target, ExecutableDefinition):
        return AutomationTarget(target, passed_assets_defs=[])
    else:
        check.failed(f"Invalid target passed to schedule: {target}")

    return AutomationTarget(
        target_executable=define_asset_job(
            name=make_synthetic_job_name(automation_name), selection=asset_selection
        ),
        passed_assets_defs=passed_assets_defs,
    )


def make_synthetic_job_name(automation_name: str) -> str:
    return f"__synthetic_asset_job_{automation_name}"
