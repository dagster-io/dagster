import subprocess
from collections.abc import Sequence
from typing import Optional

from dagster_components import (
    AssetSpecSchema,
    Component,
    ComponentLoadContext,
    ComponentSchema,
    OpSpecSchema,
    registered_component_type,
)

import dagster as dg


class ShellScriptSchema(ComponentSchema):
    script_path: str
    asset_specs: Sequence[AssetSpecSchema]
    op: Optional[OpSpecSchema] = None


@registered_component_type(name="shell_command")
class ShellCommand(Component):
    def __init__(
        self,
        script_path: str,
        asset_specs: Sequence[dg.AssetSpec],
        op: Optional[OpSpecSchema] = None,
    ):
        self.script_path = script_path
        self.specs = asset_specs
        self.op = op or OpSpecSchema()

    @classmethod
    def get_schema(cls) -> type[ShellScriptSchema]:
        return ShellScriptSchema

    def build_defs(self, load_context: ComponentLoadContext) -> dg.Definitions:
        @dg.multi_asset(name=self.op.name, op_tags=self.op.tags, specs=self.specs)
        def _asset(context: dg.AssetExecutionContext):
            self.execute(context)

        return dg.Definitions(assets=[_asset])

    def execute(self, context: dg.AssetExecutionContext):
        subprocess.run(["sh", self.script_path], check=True)
