import re
from collections.abc import Sequence
from typing import Optional, Union, cast

import dagster._check as check
from dagster._annotations import beta
from dagster._core.definitions.asset_check_factories.utils import (
    assets_to_keys,
    build_multi_asset_check,
)
from dagster._core.definitions.asset_check_spec import (
    AssetCheckKey,
    AssetCheckSeverity,
    AssetCheckSpec,
)
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.asset_key import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.assets import AssetsDefinition, SourceAsset
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.utils import INVALID_NAME_CHARS
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.instance import DagsterInstance


@beta
def build_metadata_bounds_checks(
    *,
    assets: Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]],
    severity: AssetCheckSeverity = AssetCheckSeverity.WARN,
    metadata_key: str,
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    exclusive_min: bool = False,
    exclusive_max: bool = False,
) -> Sequence[AssetChecksDefinition]:
    """Returns asset checks that pass if the metadata value of the asset's latest materialization
    is within the specified range.

    Args:
        assets (Sequence[Union[AssetKey, str, AssetsDefinition, SourceAsset]]): The assets to create
            asset checks for.
        severity (AssetCheckSeverity): The severity if the check fails. Defaults to WARN.
        metadata_key (str): The metadata key to check.
        min_value (Optional[Union[int, float]]): The minimum value to check for. If None, no minimum
            value check is performed.
        max_value (Optional[Union[int, float]]): The maximum value to check for. If None, no maximum
            value check is performed.
        exclusive_min (bool): If True, the check will fail if the metadata value is equal to `min_value`.
            Defaults to False.
        exclusive_max (bool): If True, the check will fail if the metadata value is equal to `max_value`.
            Defaults to False.

    Returns:
        Sequence[AssetsChecksDefinition]
    """
    check.sequence_param(assets, "assets", of_type=(AssetKey, str, AssetsDefinition, SourceAsset))
    check.inst_param(severity, "severity", AssetCheckSeverity)
    check.str_param(metadata_key, "metadata_key")
    check.opt_numeric_param(min_value, "min_value")
    check.opt_numeric_param(max_value, "max_value")
    check.bool_param(exclusive_min, "exclusive_min")
    check.bool_param(exclusive_max, "exclusive_max")

    if min_value is None and max_value is None:
        raise DagsterInvalidDefinitionError(
            "At least one of `min_value` or `max_value` must be set"
        )

    if min_value is not None and max_value is not None and min_value > max_value:
        raise DagsterInvalidDefinitionError("`min_value` may not be greater than `max_value`")

    asset_keys = assets_to_keys(assets)

    description = f"Checks that the latest materialization has metadata value `{metadata_key}`"
    if min_value is not None:
        description += f" greater than {'or equal to ' if not exclusive_min else ''}{min_value}"
    if max_value is not None:
        description += f" {'and ' if min_value is not None else ''}less than {'or equal to ' if not exclusive_max else ''}{max_value}"

    def _result_for_check_key(
        instance: DagsterInstance, asset_check_key: AssetCheckKey
    ) -> tuple[bool, str]:
        event = instance.get_latest_materialization_event(asset_check_key.asset_key)
        if not event:
            return False, "Asset has not been materialized"

        metadata = cast(AssetMaterialization, event.asset_materialization).metadata
        if metadata_key not in metadata:
            return False, f"Metadata key `{metadata_key}` not found"

        value = metadata[metadata_key].value
        if not isinstance(value, (int, float)):
            return False, f"Value `{value}` is not a number"

        if min_value is not None and (value <= min_value if exclusive_min else value < min_value):
            return (
                False,
                f"Value `{value}` is less than {'or equal to ' if exclusive_min else ''}{min_value}",
            )
        if max_value is not None and (value >= max_value if exclusive_max else value > max_value):
            return (
                False,
                f"Value `{value}` is greater than {'or equal to ' if exclusive_max else ''}{max_value}",
            )
        return True, f"Value `{value}` is within range"

    return build_multi_asset_check(
        check_specs=[
            AssetCheckSpec(
                f"{re.sub(INVALID_NAME_CHARS, '_', metadata_key)}_bounds_check",
                asset=asset_key,
                description=description,
            )
            for asset_key in asset_keys
        ],
        check_fn=_result_for_check_key,
        severity=severity,
    )
