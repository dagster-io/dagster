from collections.abc import Sequence

from dagster_components import AssetSpecSchema, Component, ComponentLoadContext
from dagster_components.core.schema.base import PlainSamwiseSchema

import dagster as dg


class ShellScriptSchema(PlainSamwiseSchema):
    script_path: str
    asset_specs: Sequence[AssetSpecSchema]


class ShellCommand(Component):
    """Models a shell script as a Dagster asset."""

    @classmethod
    def get_schema(cls) -> type[ShellScriptSchema]:
        return ShellScriptSchema

    def build_defs(self, load_context: ComponentLoadContext) -> dg.Definitions: ...
