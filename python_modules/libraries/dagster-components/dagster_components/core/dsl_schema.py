from typing import Any, Dict, Literal, Mapping, Optional, Union

from dagster._core.definitions.asset_spec import AssetSpec, map_asset_specs
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._record import replace
from dagster._utils.warnings import suppress_dagster_warnings
from pydantic import BaseModel


class OpSpecBaseModel(BaseModel):
    name: Optional[str] = None
    tags: Optional[Dict[str, str]] = None


class AutomationConditionModel(BaseModel):
    type: str
    params: Mapping[str, Any] = {}

    def to_automation_condition(self) -> AutomationCondition:
        return getattr(AutomationCondition, self.type)(**self.params)


class AssetSpecProcessorModel(BaseModel):
    target: str = "*"
    strategy: Union[Literal["replace"], Literal["merge"]] = "replace"
    description: Optional[str] = None
    metadata: Optional[Mapping[str, Any]] = None
    group_name: Optional[str] = None
    tags: Optional[Mapping[str, str]] = None
    automation_condition: Optional[AutomationConditionModel] = None

    def _props(self) -> Mapping[str, Any]:
        return {
            **self.model_dump(exclude={"target", "strategy"}),
            "automation_condition": self.automation_condition.to_automation_condition()
            if self.automation_condition
            else None,
        }

    @suppress_dagster_warnings
    def _apply_to_spec(self, spec: AssetSpec) -> AssetSpec:
        if self.strategy == "replace":
            return spec.replace_attributes(**self._props())
        else:
            return spec.merge_attributes(**self._props())

    def transform(self, defs: Definitions) -> Definitions:
        """Applies the specified transformation to the asset specs in the given definitions."""
        mappable = [d for d in defs.assets or [] if isinstance(d, (AssetsDefinition, AssetSpec))]
        mapped_assets = map_asset_specs(self._apply_to_spec, mappable)
        assets = [
            *mapped_assets,
            *[d for d in defs.assets or [] if not isinstance(d, (AssetsDefinition, AssetSpec))],
        ]
        return replace(defs, assets=assets)
