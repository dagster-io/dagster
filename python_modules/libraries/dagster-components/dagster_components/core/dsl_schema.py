from abc import ABC, abstractmethod
from typing import Annotated, Any, Dict, Literal, Mapping, Optional, Sequence, Union

from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.asset_spec import AssetSpec, map_asset_specs
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._record import replace
from pydantic import BaseModel, Field


class OpSpecBaseModel(BaseModel):
    name: Optional[str] = None
    tags: Optional[Dict[str, str]] = None


class AutomationConditionModel(BaseModel):
    type: str
    params: Mapping[str, Any] = {}

    def to_automation_condition(self) -> AutomationCondition:
        return getattr(AutomationCondition, self.type)(**self.params)


class AssetSpecProcessor(ABC, BaseModel):
    target: str = "*"
    description: Optional[str] = None
    metadata: Optional[Mapping[str, Any]] = None
    group_name: Optional[str] = None
    tags: Optional[Mapping[str, str]] = None
    automation_condition: Optional[AutomationConditionModel] = None

    def _attributes(self) -> Mapping[str, Any]:
        return {
            **self.model_dump(exclude={"target", "operation"}, exclude_unset=True),
            **{
                "automation_condition": self.automation_condition.to_automation_condition()
                if self.automation_condition
                else None
            },
        }

    @abstractmethod
    def _apply_to_spec(self, spec: AssetSpec) -> AssetSpec: ...

    def apply(self, defs: Definitions) -> Definitions:
        target_selection = AssetSelection.from_string(self.target, include_sources=True)
        target_keys = target_selection.resolve(defs.get_asset_graph())

        mappable = [d for d in defs.assets or [] if isinstance(d, (AssetsDefinition, AssetSpec))]
        mapped_assets = map_asset_specs(
            lambda spec: self._apply_to_spec(spec) if spec.key in target_keys else spec, mappable
        )

        assets = [
            *mapped_assets,
            *[d for d in defs.assets or [] if not isinstance(d, (AssetsDefinition, AssetSpec))],
        ]
        return replace(defs, assets=assets)


class MergeAttributes(AssetSpecProcessor):
    # default operation is "merge"
    operation: Literal["merge"] = "merge"

    def _apply_to_spec(self, spec: AssetSpec) -> AssetSpec:
        attributes = self._attributes()
        mergeable_attributes = {"metadata", "tags"}
        merge_attributes = {k: v for k, v in attributes.items() if k in mergeable_attributes}
        replace_attributes = {k: v for k, v in attributes.items() if k not in mergeable_attributes}
        return spec.merge_attributes(**merge_attributes).replace_attributes(**replace_attributes)


class ReplaceAttributes(AssetSpecProcessor):
    # operation must be set explicitly
    operation: Literal["replace"]

    def _apply_to_spec(self, spec: AssetSpec) -> AssetSpec:
        return spec.replace_attributes(**self._attributes())


AssetAttributes = Sequence[
    Annotated[
        Union[MergeAttributes, ReplaceAttributes],
        Field(union_mode="left_to_right"),
    ]
]
