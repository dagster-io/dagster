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
    ResolvableFromSchema,
    Scaffolder,
    ScaffoldRequest,
    scaffold_component_yaml,
)
from dagster_components.core.schema.resolvable_from_schema import (
    ResolvableFromSchema,
    YamlSchema,
)
from dagster_components.scaffoldable.decorator import scaffoldable

import dagster as dg


# highlight-start
class ShellCommandScaffolder(Scaffolder):
    """Scaffolds a template shell script alongside a filled-out component YAML file."""

    def scaffold(self, request: ScaffoldRequest, params: Any) -> None:
        scaffold_component_yaml(
            request,
            {
                "script_path": "script.sh",
                "asset_specs": [
                    {"key": "my_asset", "description": "Output of running a script"}
                ],
            },
        )
        script_path = Path(request.target_path) / "script.sh"
        script_path.write_text("#!/bin/bash\n\necho 'Hello, world!'")
        os.chmod(script_path, 0o755)


# highlight-end


class ShellScriptSchema(YamlSchema):
    script_path: str
    asset_specs: Sequence[AssetSpecSchema]


# highlight-start
@scaffoldable(scaffolder=ShellCommandScaffolder)
# highlight-end
@dataclass
class ShellCommand(Component, ResolvableFromSchema[ShellScriptSchema]):
    """Models a shell script as a Dagster asset."""

    script_path: str
    asset_specs: Annotated[Sequence[dg.AssetSpec], AssetSpecSchema.resolver_for_seq()]

    def build_defs(self, load_context: ComponentLoadContext) -> dg.Definitions:
        resolved_script_path = Path(load_context.path, self.script_path).absolute()

        @dg.multi_asset(name=Path(self.script_path).stem, specs=self.asset_specs)
        def _asset(context: dg.AssetExecutionContext):
            self.execute(resolved_script_path, context)

        return dg.Definitions(assets=[_asset])

    def execute(self, resolved_script_path: Path, context: dg.AssetExecutionContext):
        return subprocess.run(["sh", str(resolved_script_path)], check=True)
