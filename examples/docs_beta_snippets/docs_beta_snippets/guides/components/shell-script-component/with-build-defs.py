import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from dagster_components import (
    AssetSpecSchema,
    Component,
    ComponentLoadContext,
    FieldResolver,
    ResolutionContext,
    ResolvableSchema,
    registered_component_type,
)

import dagster as dg


class ShellScriptSchema(ResolvableSchema):
    script_path: str
    asset_specs: Sequence[AssetSpecSchema]


def resolve_asset_specs(
    context: ResolutionContext, schema: ShellScriptSchema
) -> Sequence[dg.AssetSpec]:
    return context.resolve_value(schema.asset_specs)


@registered_component_type(name="shell_command")
@dataclass
class ShellCommand(Component):
    script_path: str
    asset_specs: Annotated[Sequence[dg.AssetSpec], FieldResolver(resolve_asset_specs)]

    @classmethod
    def get_schema(cls) -> type[ShellScriptSchema]:
        return ShellScriptSchema

    def build_defs(self, load_context: ComponentLoadContext) -> dg.Definitions:
        @dg.multi_asset(name=Path(self.script_path).stem, specs=self.asset_specs)
        def _asset(context: dg.AssetExecutionContext):
            self.execute(context)

        return dg.Definitions(assets=[_asset])

    def execute(self, context: dg.AssetExecutionContext):
        subprocess.run(["sh", self.script_path], check=True)
