from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Annotated, Any, Callable, Literal, Optional, Union

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
from pydantic import BaseModel, Field
from typing_extensions import TypeAlias

from dagster_components.resolved.context import ResolutionContext
from dagster_components.resolved.model import (
    ResolvableModel,
    ResolvedFrom,
    ResolvedKwargs,
    Resolver,
    resolve_fields,
)


def _resolve_asset_key(key: str, context: ResolutionContext) -> AssetKey:
    resolved_val = context.resolve_value(key, as_type=AssetKey)
    return (
        AssetKey.from_user_string(resolved_val) if isinstance(resolved_val, str) else resolved_val
    )


PostProcessorFn: TypeAlias = Callable[[Definitions], Definitions]


class SingleRunBackfillPolicyModel(ResolvableModel):
    type: Literal["single_run"] = "single_run"


class MultiRunBackfillPolicyModel(ResolvableModel):
    type: Literal["multi_run"] = "multi_run"
    max_partitions_per_run: int = 1


def resolve_backfill_policy(
    context: ResolutionContext, model: "OpSpecModel"
) -> Optional[BackfillPolicy]:
    if model.backfill_policy is None:
        return None

    if model.backfill_policy.type == "single_run":
        return BackfillPolicy.single_run()
    elif model.backfill_policy.type == "multi_run":
        return BackfillPolicy.multi_run(
            max_partitions_per_run=model.backfill_policy.max_partitions_per_run
        )

    raise ValueError(f"Invalid backfill policy: {model.backfill_policy}")


@dataclass
class OpSpec(ResolvedFrom["OpSpecModel"]):
    name: Optional[str] = None
    tags: Optional[dict[str, str]] = None
    backfill_policy: Annotated[
        Optional[BackfillPolicy], Resolver.from_model(resolve_backfill_policy)
    ] = None


class OpSpecModel(ResolvableModel):
    name: Optional[str] = Field(default=None, description="The name of the op.")
    tags: Optional[dict[str, str]] = Field(
        default=None, description="Arbitrary metadata for the op."
    )
    backfill_policy: Optional[Union[SingleRunBackfillPolicyModel, MultiRunBackfillPolicyModel]] = (
        Field(default=None, description="The backfill policy to use for the assets.")
    )


class _ResolvableAssetAttributesMixin(BaseModel):
    deps: Sequence[str] = Field(
        default_factory=list,
        description="The asset keys for the upstream assets that this asset depends on.",
        examples=[["my_database/my_schema/upstream_table"]],
    )
    description: Optional[str] = Field(
        default=None,
        description="Human-readable description of the asset.",
        examples=["Refined sales data"],
    )
    metadata: Union[str, Mapping[str, Any]] = Field(
        default_factory=dict, description="Additional metadata for the asset."
    )
    group_name: Optional[str] = Field(
        default=None,
        description="Used to organize assets into groups, defaults to 'default'.",
        examples=["staging"],
    )
    skippable: bool = Field(
        default=False,
        description="Whether this asset can be omitted during materialization, causing downstream dependencies to skip.",
    )
    code_version: Optional[str] = Field(
        default=None,
        description="A version representing the code that produced the asset. Increment this value when the code changes.",
        examples=["3"],
    )
    owners: Sequence[str] = Field(
        default_factory=list,
        description="A list of strings representing owners of the asset. Each string can be a user's email address, or a team name prefixed with `team:`, e.g. `team:finops`.",
        examples=[["team:analytics", "nelson@hooli.com"]],
    )
    tags: Union[str, Mapping[str, str]] = Field(
        default_factory=dict,
        description="Tags for filtering and organizing.",
        examples=[{"tier": "prod", "team": "analytics"}],
    )
    kinds: Optional[Sequence[str]] = Field(
        default=None,
        description="A list of strings representing the kinds of the asset. These will be made visible in the Dagster UI.",
        examples=[["snowflake"]],
    )
    automation_condition: Optional[str] = Field(
        default=None,
        description="The condition under which the asset will be automatically materialized.",
    )


class AssetSpecModel(_ResolvableAssetAttributesMixin, ResolvableModel):
    key: str = Field(..., description="A unique identifier for the asset.")


class AssetAttributesModel(_ResolvableAssetAttributesMixin, ResolvableModel):
    """Resolves into a dictionary of asset attributes. This is similar to AssetSpecSchema, but
    does not require a key. This is useful in contexts where you want to modify attributes of
    an existing AssetSpec.
    """

    key: Optional[str] = Field(default=None, description="A unique identifier for the asset.")


class SharedAssetKwargs(ResolvedKwargs[AssetAttributesModel, AssetSpec]):
    deps: Sequence[str]
    description: Optional[str]
    metadata: Mapping[str, Any]
    group_name: Optional[str]
    skippable: bool
    code_version: Optional[str]
    owners: Sequence[str]
    tags: Mapping[str, str]
    kinds: Optional[Sequence[str]]
    automation_condition: Annotated[
        Optional[AutomationCondition], Resolver.from_template_injection()
    ]


class AssetSpecKwargs(SharedAssetKwargs):
    key: Annotated[
        AssetKey,
        Resolver.from_model(lambda context, schema: _resolve_asset_key(schema.key, context)),
    ]
    deps: Annotated[  # pyright: ignore[reportIncompatibleVariableOverride]
        Sequence[AssetKey],
        Resolver.from_model(
            lambda context, schema: [_resolve_asset_key(dep, context) for dep in schema.deps]
        ),
    ]


ResolvedAssetSpec: TypeAlias = Annotated[AssetSpec, Resolver.from_resolved_kwargs(AssetSpecKwargs)]


class AssetAttributesKwargs(SharedAssetKwargs):
    key: Annotated[
        Optional[AssetKey],
        Resolver.from_model(
            lambda context, schema: _resolve_asset_key(schema.key, context) if schema.key else None
        ),
    ] = None


def resolve_asset_attributes_to_mapping(
    context: ResolutionContext,
    model: AssetAttributesModel,
) -> Mapping[str, Any]:
    # only include fields that are explcitly set
    set_fields = model.model_dump(exclude_unset=True).keys()
    resolved_fields = resolve_fields(model, AssetAttributesKwargs, context)
    return {k: v for k, v in resolved_fields.items() if k in set_fields}


ResolvedAssetAttributes: TypeAlias = Annotated[
    Mapping[str, Any], Resolver(resolve_asset_attributes_to_mapping)
]


class AssetPostProcessorModel(ResolvableModel):
    target: str = "*"
    operation: Literal["merge", "replace"] = "merge"
    attributes: AssetAttributesModel


def apply_post_processor_to_spec(
    model: AssetPostProcessorModel, spec: AssetSpec, context: ResolutionContext
) -> AssetSpec:
    # add the original spec to the context and resolve values
    attributes = resolve_asset_attributes_to_mapping(
        context=context.with_scope(asset=spec), model=model.attributes
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


@dataclass
class AssetPostProcessor(ResolvedFrom[AssetPostProcessorModel]):
    fn: Annotated[PostProcessorFn, Resolver.from_model(resolve_schema_to_post_processor)]
