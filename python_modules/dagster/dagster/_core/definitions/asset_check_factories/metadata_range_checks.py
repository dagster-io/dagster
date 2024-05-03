from typing import Optional, Sequence, Tuple, Union, cast

import dagster._check as check
from dagster._annotations import experimental
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.instance import DagsterInstance

from ..asset_check_result import AssetCheckResult
from ..asset_check_spec import AssetCheckKey, AssetCheckSeverity, AssetCheckSpec
from ..asset_checks import AssetChecksDefinition
from ..asset_key import AssetKey, CoercibleToAssetKey
from ..assets import AssetsDefinition, SourceAsset
from ..decorators.asset_check_decorator import multi_asset_check
from .utils import unique_id_from_asset_keys


@experimental
def build_metadata_range_checks(
    *,
    assets: Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]],
    severity: AssetCheckSeverity = AssetCheckSeverity.WARN,
    metadata_key: str,
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    strict_min: bool = False,
    strict_max: bool = False,
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
        strict_min (bool): If True, the check will fail if the metadata value is equal to `min_value`.
            Defaults to False.
        strict_max (bool): If True, the check will fail if the metadata value is equal to `max_value`.
            Defaults to False.

    Returns:
        Sequence[AssetsChecksDefinition]
    """
    check.sequence_param(assets, "assets", of_type=(AssetKey, str, AssetsDefinition, SourceAsset))
    check.inst_param(severity, "severity", AssetCheckSeverity)
    check.str_param(metadata_key, "metadata_key")
    check.opt_numeric_param(min_value, "min_value")
    check.opt_numeric_param(max_value, "max_value")
    check.bool_param(strict_min, "strict_min")
    check.bool_param(strict_max, "strict_max")

    if min_value is None and max_value is None:
        raise DagsterInvalidDefinitionError(
            "At least one of `min_value` or `max_value` must be set"
        )

    if min_value is not None and max_value is not None and min_value > max_value:
        raise DagsterInvalidDefinitionError("`min_value` may not be greater than `max_value`")

    asset_keys = set()
    for el in assets:
        if isinstance(el, AssetsDefinition):
            asset_keys |= el.keys
        elif isinstance(el, SourceAsset):
            asset_keys.add(el.key)
        else:
            asset_keys.add(AssetKey.from_coercible(el))

    description = f"Checks that the latest materialization has metadata value `{metadata_key}` is"
    if min_value is not None:
        description += f" greater than {'or equal to ' if not strict_min else ''}{min_value}"
    if max_value is not None:
        description += f" {'and ' if min_value is not None else ''}less than {'or equal to ' if not strict_max else ''}{max_value}"

    def _result_for_check_key(
        instance: DagsterInstance, asset_check_key: AssetCheckKey
    ) -> Tuple[bool, str]:
        event = instance.get_latest_materialization_event(asset_check_key.asset_key)
        if not event:
            return False, "Asset has not been materialized"

        metadata = cast(AssetMaterialization, event.asset_materialization).metadata
        if metadata_key not in metadata:
            return False, f"Metadata key `{metadata_key}` not found"

        value = metadata[metadata_key].value
        if not isinstance(value, (int, float)):
            return False, f"Value `{value}` is not a number"

        if min_value is not None and (value <= min_value if strict_min else value < min_value):
            return (
                False,
                f"Value `{value}` is less than {'or equal to ' if strict_min else ''}{min_value}",
            )
        if max_value is not None and (value >= max_value if strict_max else value > max_value):
            return (
                False,
                f"Value `{value}` is greater than {'or equal to ' if strict_max else ''}{max_value}",
            )
        return True, f"Value `{value}` is within range"

    @multi_asset_check(
        specs=[
            AssetCheckSpec(
                f"{metadata_key.replace(' ','_')}_range_check",
                asset=asset_key,
                description=description,
            )
            for asset_key in asset_keys
        ],
        can_subset=True,
        name=unique_id_from_asset_keys(list(asset_keys)),
    )
    def _checks(context):
        for asset_check_key in context.selected_asset_check_keys:
            passed, description = _result_for_check_key(context.instance, asset_check_key)
            yield AssetCheckResult(
                passed=passed,
                description=description,
                severity=severity,
                check_name=asset_check_key.name,
                asset_key=asset_check_key.asset_key,
            )

    return [_checks]
