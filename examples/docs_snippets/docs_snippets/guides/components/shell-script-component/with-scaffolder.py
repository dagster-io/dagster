import os
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dagster_components import (
    AssetSpecModel,
    Component,
    ComponentLoadContext,
    Scaffolder,
    ScaffoldRequest,
    scaffold_component,
)
from dagster_components.resolved.core_models import ResolvedAssetSpec
from dagster_components.resolved.model import ResolvableModel, ResolvedFrom
from dagster_components.scaffold.scaffold import scaffold_with

import dagster as dg


# highlight-start
class ShellCommandScaffolder(Scaffolder):
    """Scaffolds a template shell script alongside a filled-out component YAML file."""

    def scaffold(self, request: ScaffoldRequest, params: Any) -> None:
        scaffold_component(
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


class ShellCommandModel(ResolvableModel):
    script_path: str
    asset_specs: Sequence[AssetSpecModel]


# highlight-start
@scaffold_with(ShellCommandScaffolder)
# highlight-end
@dataclass
class ShellCommand(Component, ResolvedFrom[ShellCommandModel]):
    """Models a shell script as a Dagster asset."""

    script_path: str
    asset_specs: Sequence[ResolvedAssetSpec]

    def build_defs(self, load_context: ComponentLoadContext) -> dg.Definitions:
        resolved_script_path = Path(load_context.path, self.script_path).absolute()

        @dg.multi_asset(name=Path(self.script_path).stem, specs=self.asset_specs)
        def _asset(context: dg.AssetExecutionContext):
            self.execute(resolved_script_path, context)

        return dg.Definitions(assets=[_asset])

    def execute(self, resolved_script_path: Path, context: dg.AssetExecutionContext):
        return subprocess.run(["sh", str(resolved_script_path)], check=True)
