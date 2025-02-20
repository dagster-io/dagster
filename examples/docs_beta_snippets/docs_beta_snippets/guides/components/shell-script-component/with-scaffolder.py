import os
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dagster_components import (
    AssetSpecSchema,
    Component,
    ComponentLoadContext,
    ComponentScaffolder,
    ComponentScaffoldRequest,
    ResolvableSchema,
    registered_component_type,
    scaffold_component_yaml,
)

import dagster as dg


# highlight-start
class ShellCommandScaffolder(ComponentScaffolder):
    """Scaffolds a template shell script alongside a filled-out component YAML file."""

    def scaffold(self, request: ComponentScaffoldRequest, params: Any) -> None:
        scaffold_component_yaml(
            request,
            {
                "script_path": "script.sh",
                "asset_specs": [
                    {"key": "my_asset", "description": "Output of running a script"}
                ],
            },
        )
        script_path = Path(request.component_instance_root_path) / "script.sh"
        script_path.write_text("#!/bin/bash\n\necho 'Hello, world!'")
        os.chmod(script_path, 0o755)


# highlight-end


class ShellScriptSchema(ResolvableSchema):
    script_path: str
    asset_specs: Sequence[AssetSpecSchema]


@registered_component_type(name="shell_command")
@dataclass
class ShellCommand(Component):
    """Models a shell script as a Dagster asset."""

    script_path: str
    asset_specs: Sequence[dg.AssetSpec]

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

    # highlight-start
    @classmethod
    def get_scaffolder(cls) -> ComponentScaffolder:
        return ShellCommandScaffolder()


# highlight-end
