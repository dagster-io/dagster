from pathlib import Path
from typing import Any, Optional

from dagster._core.definitions.definitions_class import Definitions
from dagster._seven import import_module_from_path
from dagster._utils import pushd
from pydantic import BaseModel
from typing_extensions import Self

from dagster_components import Component, ComponentGenerateRequest, ComponentLoadContext, component
from dagster_components.generate import generate_component_yaml


class DefinitionsGenerateParams(BaseModel):
    definitions_path: Optional[str] = None


class DefinitionsParamSchema(BaseModel):
    definitions_path: Optional[str] = None


@component(name="definitions_object")
class DefinitionsObjectComponent(Component):
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
            module = import_module_from_path("definitions", str(self.definitions_path))

        return getattr(module, "defs")
        # return load_definitions_from_module(module)

    @classmethod
    def generate_files(cls, request: ComponentGenerateRequest, params: Any) -> None:
        generate_params = (
            params if isinstance(params, DefinitionsGenerateParams) else DefinitionsGenerateParams()
        )

        with pushd(str(request.component_instance_root_path)):
            Path(
                generate_params.definitions_path
                if generate_params.definitions_path
                else "definitions.py"
            ).touch(exist_ok=True)

        generate_component_yaml(
            request,
            {"definitions_path": generate_params.definitions_path}
            if generate_params.definitions_path
            else {},
        )
