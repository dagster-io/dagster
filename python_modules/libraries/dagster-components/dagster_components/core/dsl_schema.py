from abc import ABC
from typing import AbstractSet, Annotated, Any, Dict, Literal, Mapping, Optional, Sequence, Union

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.asset_spec import AssetSpec, map_asset_specs
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._record import replace
from pydantic import BaseModel, Field

from dagster_components.core.component_rendering import RenderingScope, TemplatedValueResolver


class OpSpecBaseModel(BaseModel):
    name: Optional[str] = None
    tags: Optional[Dict[str, str]] = None


class AssetAttributesModel(BaseModel):
    key: Optional[str] = None
    deps: Sequence[str] = []
    description: Optional[str] = None
    metadata: Union[str, Mapping[str, Any]] = {}
    group_name: Optional[str] = None
    skippable: bool = False
    code_version: Optional[str] = None
    owners: Sequence[str] = []
    tags: Union[str, Mapping[str, str]] = {}
    automation_condition: Optional[Union[str, AutomationCondition]] = RenderingScope(
        Field(None), required_scope={"automation_condition"}
    )

    class Config:
        # required for AutomationCondition
        arbitrary_types_allowed = True

    def get_resolved_attributes(self, value_resolver: TemplatedValueResolver) -> Mapping[str, Any]:
        return value_resolver.resolve(self.model_dump(exclude_unset=True))


class AssetSpecProcessor(ABC, BaseModel):
    target: str = "*"
    attributes: AssetAttributesModel

    class Config:
        arbitrary_types_allowed = True

    def _apply_to_spec(self, spec: AssetSpec, attributes: Mapping[str, Any]) -> AssetSpec: ...

    def apply_to_spec(
        self,
        spec: AssetSpec,
        value_resolver: TemplatedValueResolver,
        target_keys: AbstractSet[AssetKey],
    ) -> AssetSpec:
        if spec.key not in target_keys:
            return spec

        # add the original spec to the context and resolve values
        return self._apply_to_spec(
            spec, self.attributes.get_resolved_attributes(value_resolver.with_context(asset=spec))
        )

    def apply(self, defs: Definitions, value_resolver: TemplatedValueResolver) -> Definitions:
        target_selection = AssetSelection.from_string(self.target, include_sources=True)
        target_keys = target_selection.resolve(defs.get_asset_graph())

        mappable = [d for d in defs.assets or [] if isinstance(d, (AssetsDefinition, AssetSpec))]
        mapped_assets = map_asset_specs(
            lambda spec: self.apply_to_spec(spec, value_resolver, target_keys),
            mappable,
        )

        assets = [
            *mapped_assets,
            *[d for d in defs.assets or [] if not isinstance(d, (AssetsDefinition, AssetSpec))],
        ]
        return replace(defs, assets=assets)


class MergeAttributes(AssetSpecProcessor):
    # default operation is "merge"
    operation: Literal["merge"] = "merge"

    def _apply_to_spec(self, spec: AssetSpec, attributes: Mapping[str, Any]) -> AssetSpec:
        mergeable_attributes = {"metadata", "tags"}
        merge_attributes = {k: v for k, v in attributes.items() if k in mergeable_attributes}
        replace_attributes = {k: v for k, v in attributes.items() if k not in mergeable_attributes}
        return spec.merge_attributes(**merge_attributes).replace_attributes(**replace_attributes)


class ReplaceAttributes(AssetSpecProcessor):
    # operation must be set explicitly
    operation: Literal["replace"]

    def _apply_to_spec(self, spec: AssetSpec, attributes: Mapping[str, Any]) -> AssetSpec:
        return spec.replace_attributes(**attributes)


AssetAttributes = Sequence[
    Annotated[
        Union[MergeAttributes, ReplaceAttributes],
        RenderingScope(Field(union_mode="left_to_right"), required_scope={"asset"}),
    ]
]
