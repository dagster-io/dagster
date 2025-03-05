import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from dagster_components import (
    AssetSpecSchema,
    Component,
    ComponentLoadContext,
    ResolutionContext,
    ResolvableSchema,
)
from dagster_components.core.schema.objects import AssetSpecSequenceField

import dagster as dg


class ShellScriptSchema(ResolvableSchema):
    script_path: str
    asset_specs: Sequence[AssetSpecSchema]


@dataclass
class ShellCommand(Component):
    """Models a shell script as a Dagster asset."""

    script_path: str
    asset_specs: AssetSpecSequenceField

    @classmethod
    def get_schema(cls) -> type[ShellScriptSchema]:
        return ShellScriptSchema

    def build_defs(self, load_context: ComponentLoadContext) -> dg.Definitions:
        resolved_script_path = Path(load_context.path, self.script_path).absolute()

        @dg.multi_asset(name=Path(self.script_path).stem, specs=self.asset_specs)
        def _asset(context: dg.AssetExecutionContext):
            self.execute(resolved_script_path, context)

        return dg.Definitions(assets=[_asset])

    def execute(self, resolved_script_path: Path, context: dg.AssetExecutionContext):
        return subprocess.run(["sh", str(resolved_script_path)], check=True)
