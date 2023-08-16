from functools import update_wrapper
from typing import Any, Callable, Mapping, Optional, Set, Union

from dagster import _check as check
from dagster._annotations import experimental
from dagster._config import UserConfigSchema
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.decorators.asset_decorator import (
    asset_key_from_coercible_or_definition,
    build_asset_ins,
)
from dagster._core.definitions.events import CoercibleToAssetKey
from dagster._core.definitions.output import Out
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.definitions.source_asset import SourceAsset

from .op_decorator import _Op

AssetCheckFunctionReturn = AssetCheckResult
AssetCheckFunction = Callable[..., AssetCheckFunctionReturn]


@experimental
def asset_check(
    *,
    asset: Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset],
    name: Optional[str] = None,
    description: Optional[str] = None,
    required_resource_keys: Optional[Set[str]] = None,
    resource_defs: Optional[Mapping[str, object]] = None,
    config_schema: Optional[UserConfigSchema] = None,
    compute_kind: Optional[str] = None,
    op_tags: Optional[Mapping[str, Any]] = None,
    output_required: bool = True,
    retry_policy: Optional[RetryPolicy] = None,
) -> Callable[[AssetCheckFunction], AssetChecksDefinition]:
    def inner(fn: AssetCheckFunction) -> AssetChecksDefinition:
        check.callable_param(fn, "fn")
        resolved_name = name or fn.__name__
        asset_key = asset_key_from_coercible_or_definition(asset)

        out = Out(dagster_type=None)
        asset_ins = build_asset_ins(fn, {}, {asset_key})
        op_def = _Op(
            name=f"{asset_key.to_python_identifier()}_{resolved_name}",
            ins=dict(asset_ins.values()),
            out=out,
            # Any resource requirements specified as arguments will be identified as
            # part of the Op definition instantiation
            required_resource_keys=required_resource_keys,
            tags={
                **({"kind": compute_kind} if compute_kind else {}),
                **(op_tags or {}),
            },
            config_schema=config_schema,
            retry_policy=retry_policy,
        )(fn)

        spec = AssetCheckSpec(
            name=resolved_name,
            description=description,
            asset_key=asset_key,
        )
        checks_def = AssetChecksDefinition(
            node_def=op_def,
            resource_defs={},
            asset_keys_by_input_name={
                input_name: asset_key for asset_key, (input_name, _) in asset_ins.items()
            },
            specs_by_output_name={op_def.output_defs[0].name: spec},
        )

        update_wrapper(checks_def, wrapped=fn)

        return checks_def

    return inner
