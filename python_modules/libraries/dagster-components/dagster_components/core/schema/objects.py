from collections.abc import Mapping, Sequence
from typing import Annotated, Any, Literal, Optional, Union

import dagster._check as check
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.asset_spec import AssetSpec, map_asset_specs
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._record import replace

from dagster_components.core.schema.base import ComponentSchemaBaseModel
from dagster_components.core.schema.metadata import ResolvableFieldInfo
from dagster_components.core.schema.resolver import TemplatedValueResolver


def _post_process_key(resolved: Optional[str]) -> Optional[AssetKey]:
    return AssetKey.from_user_string(resolved) if resolved else None


class OpSpecBaseModel(ComponentSchemaBaseModel):
    name: Optional[str] = None
    tags: Optional[dict[str, str]] = None


class AssetAttributesModel(ComponentSchemaBaseModel):
    key: Annotated[
        Optional[str],
        ResolvableFieldInfo(output_type=AssetKey, post_process_fn=_post_process_key),
    ] = None
    deps: Sequence[str] = []
    description: Optional[str] = None
    metadata: Annotated[
        Union[str, Mapping[str, Any]], ResolvableFieldInfo(output_type=Mapping[str, Any])
    ] = {}
    group_name: Optional[str] = None
    skippable: bool = False
    code_version: Optional[str] = None
    owners: Sequence[str] = []
    tags: Annotated[
        Union[str, Mapping[str, str]], ResolvableFieldInfo(output_type=Mapping[str, str])
    ] = {}
    kinds: Optional[Sequence[str]] = None
    automation_condition: Annotated[
        Optional[str], ResolvableFieldInfo(output_type=Optional[AutomationCondition])
    ] = None


class AssetSpecTransformModel(ComponentSchemaBaseModel):
    target: str = "*"
    operation: Literal["merge", "replace"] = "merge"
    attributes: AssetAttributesModel

    class Config:
        arbitrary_types_allowed = True

    def apply_to_spec(
        self,
        spec: AssetSpec,
        value_resolver: TemplatedValueResolver,
    ) -> AssetSpec:
        # add the original spec to the context and resolve values
        attributes = self.attributes.resolve_properties(value_resolver.with_scope(asset=spec))

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

    def apply(self, defs: Definitions, value_resolver: TemplatedValueResolver) -> Definitions:
        target_selection = AssetSelection.from_string(self.target, include_sources=True)
        target_keys = target_selection.resolve(defs.get_asset_graph())

        mappable = [d for d in defs.assets or [] if isinstance(d, (AssetsDefinition, AssetSpec))]
        mapped_assets = map_asset_specs(
            lambda spec: self.apply_to_spec(spec, value_resolver)
            if spec.key in target_keys
            else spec,
            mappable,
        )

        assets = [
            *mapped_assets,
            *[d for d in defs.assets or [] if not isinstance(d, (AssetsDefinition, AssetSpec))],
        ]
        return replace(defs, assets=assets)
