from collections.abc import Sequence
from dataclasses import dataclass

from dagster_components import (
    AssetSpecSchema,
    Component,
    ComponentLoadContext,
    ResolvableSchema,
    registered_component_type,
)

import dagster as dg


class ShellScriptSchema(ResolvableSchema):
    script_path: str
    asset_specs: Sequence[AssetSpecSchema]


@registered_component_type(name="shell_command")
@dataclass
class ShellCommand(Component):
    script_path: str
    asset_specs: Sequence[dg.AssetSpec]

    @classmethod
    def get_schema(cls) -> type[ShellScriptSchema]:
        return ShellScriptSchema

    def build_defs(self, load_context: ComponentLoadContext) -> dg.Definitions: ...
