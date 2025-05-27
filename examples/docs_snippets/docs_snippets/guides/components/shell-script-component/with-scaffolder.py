import os
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import dagster as dg
from dagster.components.scaffold.scaffold import ScaffoldRequest, scaffold_with


# highlight-start
class ShellCommandScaffolder(dg.Scaffolder):
    """Scaffolds a template shell script alongside a filled-out defs.yaml file."""

    def scaffold(self, request: ScaffoldRequest) -> None:
        dg.scaffold_component(
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


# highlight-start
@scaffold_with(ShellCommandScaffolder)
# highlight-end
@dataclass
class ShellCommand(dg.Component, dg.Resolvable):
    """Models a shell script as a Dagster asset."""

    script_path: str
    asset_specs: Sequence[dg.ResolvedAssetSpec]

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        resolved_script_path = Path(context.path, self.script_path).absolute()

        @dg.multi_asset(name=Path(self.script_path).stem, specs=self.asset_specs)
        def _asset(context: dg.AssetExecutionContext):
            self.execute(resolved_script_path, context)

        return dg.Definitions(assets=[_asset])

    def execute(self, resolved_script_path: Path, context: dg.AssetExecutionContext):
        return subprocess.run(["sh", str(resolved_script_path)], check=True)
