from typing import Callable, Literal

import dagster._check as check
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.asset_spec import AssetSpec, map_asset_specs
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._record import replace

from dagster_components.core.common.schema import AssetAttributesSchema
from dagster_components.core.resolution_engine.context import ResolutionContext
from dagster_components.core.resolution_engine.resolver import Resolver, resolver
from dagster_components.core.schema.base import ComponentSchema


class AssetSpecTransformSchema(ComponentSchema):
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


@resolver(fromtype=AssetSpecTransformSchema)
class AssetSpecTransformResolver(Resolver[AssetSpecTransformSchema]):
    def resolve(self, context: ResolutionContext) -> Callable[[Definitions], Definitions]:
        return lambda defs: self.schema.apply(defs, context)
