from collections.abc import Mapping, Sequence
from typing import Annotated, Any, Callable, Literal, Optional, Union

import dagster._check as check
from dagster._core.definitions.asset_dep import AssetDep
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.asset_spec import AssetSpec, map_asset_specs
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._record import replace
from pydantic import BaseModel, Field

from dagster_components.core.schema.base import FieldResolver, ResolvableSchema
from dagster_components.core.schema.context import ResolutionContext


def _resolve_asset_key(key: str, context: ResolutionContext) -> AssetKey:
    resolved_val = context.resolve_value(key, as_type=Union[str, AssetKey])
    return (
        AssetKey.from_user_string(resolved_val) if isinstance(resolved_val, str) else resolved_val
    )


class OpSpecSchema(ResolvableSchema):
    name: Optional[str] = Field(default=None, description="The name of the op.")
    tags: Optional[dict[str, str]] = Field(
        default=None, description="Arbitrary metadata for the op."
    )


class AssetDepSchema(ResolvableSchema[AssetDep]):
    asset: Annotated[
        str, FieldResolver(lambda context, schema: _resolve_asset_key(schema.asset, context))
    ]
    partition_mapping: Optional[str]


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


class AssetSpecSchema(_ResolvableAssetAttributesMixin, ResolvableSchema[AssetSpec]):
    key: Annotated[
        str, FieldResolver(lambda context, schema: _resolve_asset_key(schema.key, context))
    ] = Field(..., description="A unique identifier for the asset.")


class AssetAttributesSchema(_ResolvableAssetAttributesMixin, ResolvableSchema[Mapping[str, Any]]):
    """Resolves into a dictionary of asset attributes. This is similar to AssetSpecSchema, but
    does not require a key. This is useful in contexts where you want to modify attributes of
    an existing AssetSpec.
    """

    key: Annotated[
        Optional[str],
        FieldResolver(
            lambda context, schema: _resolve_asset_key(schema.key, context) if schema.key else None
        ),
    ] = Field(default=None, description="A unique identifier for the asset.")

    def resolve(self, context: ResolutionContext) -> Mapping[str, Any]:
        # only include fields that are explcitly set
        set_fields = self.model_dump(exclude_unset=True).keys()
        return {k: v for k, v in self.resolve_fields(dict, context).items() if k in set_fields}


class AssetSpecTransformSchema(ResolvableSchema):
    target: str = "*"
    operation: Literal["merge", "replace"] = "merge"
    attributes: AssetAttributesSchema

    def apply_to_spec(self, spec: AssetSpec, context: ResolutionContext) -> AssetSpec:
        # add the original spec to the context and resolve values
        attributes = context.with_scope(asset=spec).resolve_value(self.attributes)

        if self.operation == "merge":
            mergeable_attributes = {"metadata", "tags"}
            merge_attributes = {k: v for k, v in attributes.items() if k in mergeable_attributes}
            replace_attributes = {
                k: v for k, v in attributes.items() if k not in mergeable_attributes
            }
            return spec.merge_attributes(**merge_attributes).replace_attributes(
                **replace_attributes
            )
        elif self.operation == "replace":
            return spec.replace_attributes(**attributes)
        else:
            check.failed(f"Unsupported operation: {self.operation}")

    def apply(self, defs: Definitions, context: ResolutionContext) -> Definitions:
        target_selection = AssetSelection.from_string(self.target, include_sources=True)
        target_keys = target_selection.resolve(defs.get_asset_graph())

        mappable = [d for d in defs.assets or [] if isinstance(d, (AssetsDefinition, AssetSpec))]
        mapped_assets = map_asset_specs(
            lambda spec: self.apply_to_spec(spec, context) if spec.key in target_keys else spec,
            mappable,
        )

        assets = [
            *mapped_assets,
            *[d for d in defs.assets or [] if not isinstance(d, (AssetsDefinition, AssetSpec))],
        ]
        return replace(defs, assets=assets)

    def resolve(self, context: ResolutionContext) -> Callable[[Definitions], Definitions]:
        return lambda defs: self.apply(defs, context)
