from typing import Optional

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.module_loaders.load_defs_from_module import (
    load_definitions_from_module,
)
from dagster._seven import import_module_from_path
from dagster._utils import pushd
from path import Path
from pydantic import BaseModel
from typing_extensions import Self

from dagster_components import Component, ComponentGenerateRequest, ComponentLoadContext, component


class DefinitionsGenerateParams(BaseModel):
    definitions_path: Optional[str] = None


class DefinitionsParamSchema(BaseModel):
    definitions_path: Optional[str] = None


@component(name="definitions")
class DefinitionsComponent(Component):
    def __init__(self, definitions_path: Path):
        self.definitions_path = definitions_path

    generate_params_schema = DefinitionsGenerateParams
    params_schema = DefinitionsParamSchema

    @classmethod
    def load(cls, context: ComponentLoadContext) -> Self:
        # all paths should be resolved relative to the directory we're in
        loaded_params = context.load_params(cls.params_schema)

        return cls(definitions_path=Path(loaded_params.definitions_path or "definitions.py"))

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        with pushd(str(context.path)):
            module = import_module_from_path("definitions", self.definitions_path)

        return load_definitions_from_module(module)

    @classmethod
    def generate_files(
        cls, request: ComponentGenerateRequest, params: DefinitionsGenerateParams
    ) -> None:
        raise NotImplementedError("Not implemented")
