from collections.abc import Sequence
from dataclasses import dataclass

from dagster_components import (
    AssetSpecSchema,
    Component,
    ComponentLoadContext,
    ResolvableSchema,
)
from dagster_components.core.schema.objects import AssetSpecSequenceField

import dagster as dg


class ShellScriptSchema(ResolvableSchema):
    script_path: str
    asset_specs: Sequence[AssetSpecSchema]


@dataclass
class ShellCommand(Component):
    script_path: str
    asset_specs: AssetSpecSequenceField

    @classmethod
    def get_schema(cls) -> type[ShellScriptSchema]:
        return ShellScriptSchema

    def build_defs(self, load_context: ComponentLoadContext) -> dg.Definitions: ...
