from abc import abstractmethod
from typing import Any, ClassVar, Dict, Literal, Mapping, Optional, Union

from dagster._core.definitions.asset_spec import map_asset_specs
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._record import replace
from dagster_dbt.asset_specs import AssetSpec
from pydantic import BaseModel


class OpSpecBaseModel(BaseModel):
    name: Optional[str] = None
    tags: Optional[Dict[str, str]] = None


class AutomationConditionModel(BaseModel):
    type: str
    params: Mapping[str, Any] = {}

    def to_automation_condition(self) -> AutomationCondition:
        return getattr(AutomationCondition, self.type)(**self.params)


class DefsTransformModel(BaseModel):
    type: ClassVar[str]

    @abstractmethod
    def transform(self, defs: Definitions) -> Definitions: ...


class SpecTransformModel(DefsTransformModel):
    target: str = "*"

    def _attributes(self) -> Mapping[str, Any]:
        return self.model_dump(exclude={"target", "type"})

    @abstractmethod
    def _apply_to_spec(self, spec: AssetSpec) -> AssetSpec: ...

    def transform(self, defs: Definitions) -> Definitions:
        """Applies the specified transformation to the asset specs in the given definitions."""
        mappable = [d for d in defs.assets or [] if isinstance(d, (AssetsDefinition, AssetSpec))]
        mapped_assets = map_asset_specs(self._apply_to_spec, mappable)
        assets = [
            *mapped_assets,
            *[d for d in defs.assets or [] if not isinstance(d, (AssetsDefinition, AssetSpec))],
        ]
        return replace(defs, assets=assets)


class MergeSpecTransformModel(SpecTransformModel):
    type: Literal["merge"] = "merge"
    metadata: Optional[Mapping[str, Any]] = None
    tags: Optional[Mapping[str, str]] = None

    def _apply_to_spec(self, spec: AssetSpec) -> AssetSpec:
        return spec.merge_attributes(**self._attributes())


class ReplaceSpecTransformModel(SpecTransformModel):
    type: Literal["replace"] = "replace"
    description: Optional[str] = None
    metadata: Optional[Mapping[str, Any]] = None
    group_name: Optional[str] = None
    tags: Optional[Mapping[str, str]] = None
    automation_condition: Optional[AutomationConditionModel] = None

    def _attributes(self) -> Mapping[str, Any]:
        return {
            **super()._attributes(),
            "automation_condition": self.automation_condition,
        }

    def _apply_to_spec(self, spec):
        return spec.replace_attributes(**self._attributes())


DefsTransformUnion = Union[MergeSpecTransformModel, ReplaceSpecTransformModel]
