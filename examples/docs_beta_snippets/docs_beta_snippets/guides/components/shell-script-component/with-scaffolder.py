import os
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any

from dagster_components import (
    AssetSpecSchema,
    Component,
    ComponentLoadContext,
    FieldResolver,
    ResolutionContext,
    ResolvableSchema,
    registered_component_type,
)
from dagster_components.core.component_scaffolder import (
    ComponentScaffolder,
    ComponentScaffoldRequest,
)
from dagster_components.scaffold import scaffold_component_yaml

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
    """Models a shell script as a Dagster asset."""

    script_path: str
    asset_specs: Annotated[Sequence[dg.AssetSpec], FieldResolver(resolve_asset_specs)]

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
        subprocess.run(["sh", str(resolved_script_path)], check=True)

    @classmethod
    def get_scaffolder(cls) -> ComponentScaffolder:
        return ShellCommandScaffolder()


class ShellCommandScaffolder(ComponentScaffolder):
    """Scaffolds a template shell script alongside a filled-out component YAML file."""

    def scaffold(self, request: ComponentScaffoldRequest, params: Any) -> None:
        scaffold_component_yaml(
            request,
            {
                "script_path": "script.sh",
                "asset_specs": [{"name": "my_asset", "description": "My asset"}],
            },
        )
        script_path = Path(request.component_instance_root_path) / "script.sh"
        script_path.write_text("#!/bin/bash\n\necho 'Hello, world!'")
        os.chmod(script_path, 0o755)
