import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import dagster as dg
from dagster.components import (
    Component,
    ComponentLoadContext,
    Resolvable,
    ResolvedAssetSpec,
)


@dataclass
class ShellCommand(Component, Resolvable):
    """Models a shell script as a Dagster asset."""

    script_path: str
    asset_specs: Sequence[ResolvedAssetSpec]

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        resolved_script_path = Path(context.path, self.script_path).absolute()

        @dg.multi_asset(name=Path(self.script_path).stem, specs=self.asset_specs)
        def _asset(context: dg.AssetExecutionContext):
            self.execute(resolved_script_path, context)

        return dg.Definitions(assets=[_asset])

    def execute(self, resolved_script_path: Path, context: dg.AssetExecutionContext):
        return subprocess.run(["sh", str(resolved_script_path)], check=True)
