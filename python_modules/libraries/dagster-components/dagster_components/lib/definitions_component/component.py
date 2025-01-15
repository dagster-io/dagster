from pathlib import Path
from typing import Optional

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.module_loaders.load_defs_from_module import (
    load_definitions_from_module,
)
from dagster._seven import import_uncached_module_from_path
from dagster._utils import pushd
from pydantic import BaseModel
from typing_extensions import Self

from dagster_components import Component, ComponentLoadContext, component_type
from dagster_components.lib.definitions_component.scaffolder import DefinitionsComponentScaffolder


class DefinitionsParamSchema(BaseModel):
    definitions_path: Optional[str] = None


@component_type(name="definitions")
class DefinitionsComponent(Component):
    def __init__(self, definitions_path: Path):
        self.definitions_path = definitions_path

    @classmethod
    def get_scaffolder(cls) -> DefinitionsComponentScaffolder:
        return DefinitionsComponentScaffolder()

    @classmethod
    def get_schema(cls):
        return DefinitionsParamSchema

    @classmethod
    def load(cls, context: ComponentLoadContext) -> Self:
        # all paths should be resolved relative to the directory we're in
        loaded_params = context.load_params(cls.get_schema())

        return cls(definitions_path=Path(loaded_params.definitions_path or "definitions.py"))

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        with pushd(str(context.path)):
            module = import_uncached_module_from_path("definitions", str(self.definitions_path))

        return load_definitions_from_module(module)
