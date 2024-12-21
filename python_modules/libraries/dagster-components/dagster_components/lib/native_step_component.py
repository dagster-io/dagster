import os
from pathlib import Path
from typing import Any, Iterator, Optional, Sequence, Union

import yaml
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.result import MaterializeResult
from dagster_embedded_elt.sling import SlingResource, sling_assets
from dagster_embedded_elt.sling.resources import AssetExecutionContext
from pydantic import BaseModel
from typing_extensions import Self

from dagster_components import Component, ComponentLoadContext
from dagster_components.core.component import ComponentGenerateRequest, component
from dagster_components.core.dsl_schema import AssetAttributes, AssetSpecProcessor, OpSpecBaseModel
from dagster_components.generate import generate_component_yaml


class AssetSpecBaseModel(BaseModel):
    key: str


class NativeComponentSchema(BaseModel):
    op: OpSpecBaseModel
    assets: Optional[Sequence[AssetSpecBaseModel]] = None


# Possibilities
# * op
# * step
# * task
# * computation


@component(name="native_step")
class NativeStepComponent(Component):
    def build_defs(self, context: ComponentLoadContext) -> Definitions: ...

    @classmethod
    def load(cls, context: "ComponentLoadContext") -> Self: ...

    @classmethod
    def generate_files(cls, request: ComponentGenerateRequest, params: Any) -> None:
        super().generate_files(request, params)

    def execute(self): ...
