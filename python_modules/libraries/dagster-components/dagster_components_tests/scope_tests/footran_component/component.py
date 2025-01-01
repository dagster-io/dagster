from typing import AbstractSet

from dagster import Definitions, asset
from dagster_components import Component, ComponentLoadContext, component_type
from pydantic import BaseModel


class FootranParams(BaseModel):
    target_address: str


@component_type(name="footran")
class FootranComponent(Component):
    def __init__(self, target_address: str):
        self.target_address = target_address

    params_schema = FootranParams

    @classmethod
    def load(cls, context: ComponentLoadContext):
        loaded_params = context.load_params(cls.params_schema)
        return cls(target_address=loaded_params.target_address)

    def build_defs(self, context: ComponentLoadContext):
        @asset
        def an_asset() -> None: ...

        return Definitions()

    def required_env_vars(self, context: ComponentLoadContext) -> AbstractSet[str]:
        requires = context.component_file_model.requires
        return set(requires.env) if requires and requires.env else set()
