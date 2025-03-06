from collections.abc import Sequence
from dataclasses import dataclass

from dagster_components import (
    AssetSpecSchema,
    Component,
    ComponentLoadContext,
    DSLSchema,
    ResolvableFromSchema,
)
from dagster_components.core.schema.objects import AssetSpecSequenceField

import dagster as dg


class ShellScriptSchema(DSLSchema):
    script_path: str
    asset_specs: Sequence[AssetSpecSchema]


@dataclass
class ShellCommand(Component, ResolvableFromSchema[ShellScriptSchema]):
    script_path: str
    asset_specs: AssetSpecSequenceField

    def build_defs(self, load_context: ComponentLoadContext) -> dg.Definitions: ...
