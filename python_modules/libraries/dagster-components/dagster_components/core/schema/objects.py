from collections.abc import Mapping, Sequence
from typing import Any, Callable, Literal, Optional, Union

import dagster._check as check
from dagster._core.definitions.asset_dep import AssetDep
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.asset_spec import AssetSpec, map_asset_specs
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.partition_mapping import PartitionMapping
from dagster._record import replace
from pydantic import BaseModel

from dagster_components.core.schema.base import ResolvableSchema
from dagster_components.core.schema.context import ResolutionContext


def _resolve_asset_key(key: str, context: ResolutionContext) -> AssetKey:
    resolved_val = context.resolve_value(key, as_type=Union[str, AssetKey])
    return (
        AssetKey.from_user_string(resolved_val) if isinstance(resolved_val, str) else resolved_val
    )


class OpSpecSchema(ResolvableSchema):
    name: Optional[str] = None
    tags: Optional[dict[str, str]] = None


class AssetDepSchema(ResolvableSchema[AssetDep]):
    asset: str
    partition_mapping: Optional[str] = None

    def resolve(self, context: ResolutionContext) -> AssetDep:
        return AssetDep(
            asset=_resolve_asset_key(self.asset, context),
            partition_mapping=context.resolve_value(
                self.partition_mapping, as_type=Optional[PartitionMapping]
            ),
        )


class _ResolvableAssetAttributesMixin(BaseModel):
    deps: Sequence[str] = []
    description: Optional[str] = None
    metadata: Union[str, Mapping[str, Any]] = {}
    group_name: Optional[str] = None
    skippable: bool = False
    code_version: Optional[str] = None
    owners: Sequence[str] = []
    tags: Union[str, Mapping[str, str]] = {}
    kinds: Optional[Sequence[str]] = None
    automation_condition: Optional[str] = None


class AssetAttributesSchema(_ResolvableAssetAttributesMixin, ResolvableSchema[Mapping[str, Any]]):
    key: Optional[str] = None

    def resolve(self, context: ResolutionContext) -> Mapping[str, Any]:
        # only include fields that are explcitly set
        set_fields = self.model_dump(exclude_unset=True).keys()
        return {k: v for k, v in self.resolve_fields(context).items() if k in set_fields}


class AssetSpecSchema(_ResolvableAssetAttributesMixin, ResolvableSchema[AssetSpec]):
    key: str

    def resolve(self, context: ResolutionContext) -> AssetSpec:
        return AssetSpec(
            **self.resolve_fields(context, exclude={"key"}),
            key=_resolve_asset_key(self.key, context),
        )


class AssetSpecTransformSchema(ResolvableSchema):
    target: str = "*"
    operation: Literal["merge", "replace"] = "merge"
    attributes: AssetAttributesSchema

    class Config:
        arbitrary_types_allowed = True

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
