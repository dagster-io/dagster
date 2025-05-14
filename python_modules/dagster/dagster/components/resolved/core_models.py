from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Annotated, Any, Callable, Literal, Optional, Union

from dagster_shared.record import record
from typing_extensions import TypeAlias

import dagster._check as check
from dagster._annotations import preview, public
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_key import AssetKey, CoercibleToAssetKeyPrefix
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.definitions_class import Definitions
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
        description="A unique identifier for the asset.",
    ),
]


@record
class SharedAssetKwargs(Resolvable):
    deps: Annotated[
        Optional[Sequence[ResolvedAssetKey]],
        Resolver.default(
            description="The asset keys for the upstream assets that this asset depends on.",
            examples=[["my_database/my_schema/upstream_table"]],
        ),
    ] = None
    description: Annotated[
        Optional[str],
        Resolver.default(
            description="Human-readable description of the asset.",
            examples=["Refined sales data"],
        ),
    ] = None
    metadata: Annotated[
        Mapping[str, Any],
        Resolver.default(
            can_inject=True,
            description="Additional metadata for the asset.",
        ),
    ] = {}
    group_name: Annotated[
        Optional[str],
        Resolver.default(
            description="Used to organize assets into groups, defaults to 'default'.",
            examples=["staging"],
        ),
    ] = None
    skippable: Annotated[
        Optional[bool],
        Resolver.default(
            description="Whether this asset can be omitted during materialization, causing downstream dependencies to skip.",
        ),
    ] = None
    code_version: Annotated[
        Optional[str],
        Resolver.default(
            description="A version representing the code that produced the asset. Increment this value when the code changes.",
            examples=["3"],
        ),
    ] = None
    owners: Annotated[
        Optional[Sequence[str]],
        Resolver.default(
            description="A list of strings representing owners of the asset. Each string can be a user's email address, or a team name prefixed with `team:`, e.g. `team:finops`.",
            examples=[["team:analytics", "nelson@hooli.com"]],
        ),
    ] = None
    tags: Annotated[
        Mapping[str, str],
        Resolver.default(
            can_inject=True,
            description="Tags for filtering and organizing.",
            examples=[{"tier": "prod", "team": "analytics"}],
        ),
    ] = {}
    kinds: Annotated[
        Sequence[str],
        Resolver.default(
            description="A list of strings representing the kinds of the asset. These will be made visible in the Dagster UI.",
            examples=[["snowflake"]],
        ),
    ] = []
    automation_condition: Annotated[
        Optional[AutomationCondition],
        Resolver.default(
            model_field_type=Optional[str],
            description="The condition under which the asset will be automatically materialized.",
        ),
    ] = None


@record
class AssetSpecKwargs(SharedAssetKwargs):
    """Resolvable object representing the keyword args to AssetSpec."""

    key: ResolvedAssetKey


@record
class AssetsDefUpdateKwargs(SharedAssetKwargs):
    """The attributes of an AssetSpec that can be updated after the
    AssetsDefinition is created, done via map_asset_specs.
    """


@record
class AssetSpecUpdateKwargs(SharedAssetKwargs):
    """The attributes of an AssetSpec that can be changed before the
    AssetsDefinition is created. Typically used by components to allow
    overriding a default resolution of each AssetSpec.
    """

    key: Optional[ResolvedAssetKey] = None
    key_prefix: Annotated[
        Optional[CoercibleToAssetKeyPrefix],
        Resolver.default(description="Prefix the existing asset key with the provided value."),
    ] = None


def resolve_asset_spec(context: ResolutionContext, model):
    return AssetSpec(**resolve_fields(model, AssetSpecKwargs, context))


ResolvedAssetSpec: TypeAlias = Annotated[
    AssetSpec,
    Resolver(
        resolve_asset_spec,
        model_field_type=AssetSpecKwargs.model(),
    ),
]


@record
class AssetCheckSpecKwargs(Resolvable):
    name: str
    asset: ResolvedAssetKey
    additional_deps: Optional[Sequence[ResolvedAssetKey]] = None
    description: Optional[str] = None
    blocking: bool = False
    metadata: Injectable[Optional[Mapping[str, Any]]] = None
    automation_condition: Optional[Injected[AutomationCondition]] = None


def resolve_asset_check_spec(context: ResolutionContext, model):
    return AssetCheckSpec(
        **resolve_fields(model=model, resolved_cls=AssetCheckSpecKwargs, context=context)
    )


ResolvedAssetCheckSpec: TypeAlias = Annotated[
    AssetCheckSpec,
    Resolver(
        resolve_asset_check_spec,
        model_field_type=AssetCheckSpecKwargs.model(),
    ),
]


def _resolve_update_kwargs_to_mapping(
    context: ResolutionContext,
    model,
    kwargs_class,
):
    # only include fields that are explicitly set
    set_fields = model.model_dump(exclude_unset=True).keys()
    resolved_fields = resolve_fields(model, kwargs_class, context)
    return {k: v for k, v in resolved_fields.items() if k in set_fields}


def resolve_asset_spec_update_kwargs_to_mapping(
    context: ResolutionContext,
    model,
) -> Mapping[str, Any]:
    return _resolve_update_kwargs_to_mapping(context, model, AssetSpecUpdateKwargs)


def resolve_assets_def_update_kwargs_to_mapping(
    context: ResolutionContext,
    model,
) -> Mapping[str, Any]:
    return _resolve_update_kwargs_to_mapping(context, model, AssetsDefUpdateKwargs)


AssetAttributesModel = AssetSpecUpdateKwargs.model()

ResolvedAssetAttributes: TypeAlias = Annotated[
    Mapping[str, Any],
    Resolver(
        resolve_assets_def_update_kwargs_to_mapping,
        model_field_type=AssetsDefUpdateKwargs.model(),
    ),
]


@public
@preview(emit_runtime_warning=False)
class AssetPostProcessorModel(Resolvable, Model):
    """An object that defines asset transforms to be done via Definitions.map_asset_specs."""

    target: str = "*"
    operation: Literal["merge", "replace"] = "merge"
    attributes: ResolvedAssetAttributes


def apply_post_processor_to_spec(
    model,
    spec: AssetSpec,
    context: ResolutionContext,
) -> AssetSpec:
    check.inst(model, AssetPostProcessorModel.model())

    attributes = dict(
        resolve_assets_def_update_kwargs_to_mapping(
            context.with_scope(asset=spec).at_path("attributes"),
            model.attributes,
        )
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
    model,
    defs: Definitions,
    context: ResolutionContext,
) -> Definitions:
    check.inst(model, AssetPostProcessorModel.model())

    return defs.map_asset_specs(
        selection=model.target,
        func=lambda spec: apply_post_processor_to_spec(model, spec, context),
    )


def resolve_schema_to_post_processor(
    context: ResolutionContext,
    model,
) -> Callable[[Definitions], Definitions]:
    check.inst(model, AssetPostProcessorModel.model())

    return lambda defs: apply_post_processor_to_defs(model, defs, context)


AssetPostProcessor: TypeAlias = Annotated[
    PostProcessorFn,
    Resolver(
        resolve_schema_to_post_processor,
        model_field_type=AssetPostProcessorModel.model(),
    ),
]
