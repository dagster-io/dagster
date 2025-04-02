from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Annotated, Any, Callable, Literal, Optional, Union

from dagster_shared.record import record
from typing_extensions import TypeAlias

import dagster._check as check
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.asset_spec import AssetSpec, map_asset_specs
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._record import replace
from dagster.components.resolved.base import Resolvable, resolve_fields
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.model import Injectable, Injected, Model, Resolver


def _resolve_asset_key(context: ResolutionContext, key: str) -> AssetKey:
    resolved_val = context.resolve_value(key, as_type=AssetKey)
    return (
        AssetKey.from_user_string(resolved_val) if isinstance(resolved_val, str) else resolved_val
    )


PostProcessorFn: TypeAlias = Callable[[Definitions], Definitions]


class SingleRunBackfillPolicyModel(Resolvable, Model):
    type: Literal["single_run"] = "single_run"


class MultiRunBackfillPolicyModel(Resolvable, Model):
    type: Literal["multi_run"] = "multi_run"
    max_partitions_per_run: int = 1


def resolve_backfill_policy(
    context: ResolutionContext,
    backfill_policy,
) -> Optional[BackfillPolicy]:
    if backfill_policy is None:
        return None

    if backfill_policy.type == "single_run":
        return BackfillPolicy.single_run()
    elif backfill_policy.type == "multi_run":
        return BackfillPolicy.multi_run(
            max_partitions_per_run=backfill_policy.max_partitions_per_run
        )

    raise ValueError(f"Invalid backfill policy: {backfill_policy}")


@dataclass
class OpSpec(Resolvable):
    name: Optional[str] = None
    tags: Optional[dict[str, str]] = None
    backfill_policy: Annotated[
        Optional[BackfillPolicy],
        Resolver(
            resolve_backfill_policy,
            model_field_type=Union[SingleRunBackfillPolicyModel, MultiRunBackfillPolicyModel],
        ),
    ] = None


def _expect_injected(context, val):
    return check.opt_inst_param(val, "val", AutomationCondition)


ResolvedAssetKey = Annotated[
    AssetKey,
    Resolver(
        _resolve_asset_key,
        model_field_type=str,
    ),
]


@record
class SharedAssetKwargs(Resolvable):
    deps: Optional[Sequence[ResolvedAssetKey]] = None
    description: Optional[str] = None
    metadata: Injectable[Mapping[str, Any]] = {}
    group_name: Optional[str] = None
    skippable: Optional[bool] = None
    code_version: Optional[str] = None
    owners: Optional[Sequence[str]] = None
    tags: Injectable[Mapping[str, str]] = {}
    kinds: Sequence[str] = []
    automation_condition: Optional[Injected[AutomationCondition]] = None


@record
class AssetSpecKwargs(SharedAssetKwargs):
    key: ResolvedAssetKey


@record
class AssetAttributesKwargs(SharedAssetKwargs):
    key: Optional[ResolvedAssetKey] = None


def resolve_asset_spec(context: ResolutionContext, model):
    return AssetSpec(**resolve_fields(model, AssetSpecKwargs, context))


ResolvedAssetSpec: TypeAlias = Annotated[
    AssetSpec,
    Resolver(
        resolve_asset_spec,
        model_field_type=AssetSpecKwargs.model(),
    ),
]


def resolve_asset_attributes_to_mapping(
    context: ResolutionContext,
    model,
) -> Mapping[str, Any]:
    # only include fields that are explcitly set
    set_fields = model.model_dump(exclude_unset=True).keys()
    resolved_fields = resolve_fields(model, AssetAttributesKwargs, context)
    return {k: v for k, v in resolved_fields.items() if k in set_fields}


AssetAttributesModel = AssetAttributesKwargs.model()

ResolvedAssetAttributes: TypeAlias = Annotated[
    Mapping[str, Any],
    Resolver(
        resolve_asset_attributes_to_mapping,
        model_field_type=AssetAttributesKwargs.model(),
    ),
]


class AssetPostProcessorModel(Resolvable, Model):
    target: str = "*"
    operation: Literal["merge", "replace"] = "merge"
    attributes: ResolvedAssetAttributes


def apply_post_processor_to_spec(
    model: AssetPostProcessorModel, spec: AssetSpec, context: ResolutionContext
) -> AssetSpec:
    attributes = (
        context.with_scope(asset=spec).at_path("attributes").resolve_value(model.attributes)
    )
    if model.operation == "merge":
        mergeable_attributes = {"metadata", "tags"}
        merge_attributes = {k: v for k, v in attributes.items() if k in mergeable_attributes}
        replace_attributes = {k: v for k, v in attributes.items() if k not in mergeable_attributes}
        return spec.merge_attributes(**merge_attributes).replace_attributes(**replace_attributes)
    elif model.operation == "replace":
        return spec.replace_attributes(**attributes)
    else:
        check.failed(f"Unsupported operation: {model.operation}")


def apply_post_processor_to_defs(
    model: AssetPostProcessorModel, defs: Definitions, context: ResolutionContext
) -> Definitions:
    target_selection = AssetSelection.from_string(model.target, include_sources=True)
    target_keys = target_selection.resolve(defs.get_asset_graph())

    mappable = [d for d in defs.assets or [] if isinstance(d, (AssetsDefinition, AssetSpec))]
    mapped_assets = map_asset_specs(
        lambda spec: apply_post_processor_to_spec(model, spec, context)
        if spec.key in target_keys
        else spec,
        mappable,
    )

    assets = [
        *mapped_assets,
        *[d for d in defs.assets or [] if not isinstance(d, (AssetsDefinition, AssetSpec))],
    ]
    return replace(defs, assets=assets)


def resolve_schema_to_post_processor(
    context, model: AssetPostProcessorModel
) -> Callable[[Definitions], Definitions]:
    return lambda defs: apply_post_processor_to_defs(model, defs, context)


AssetPostProcessor: TypeAlias = Annotated[
    PostProcessorFn,
    Resolver(
        resolve_schema_to_post_processor,
        model_field_type=AssetPostProcessorModel,
    ),
]
