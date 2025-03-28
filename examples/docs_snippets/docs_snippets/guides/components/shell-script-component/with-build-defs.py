import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from dagster_components import Component, ComponentLoadContext, Resolvable
from dagster_components.resolved.core_models import ResolvedAssetSpec

import dagster as dg


@dataclass
class ShellCommand(Component, Resolvable):
    """Models a shell script as a Dagster asset."""

    def __init__(
        self,
        script_path: str,
        asset_specs: Sequence[ResolvedAssetSpec],
    ):
        self.script_path = script_path
        self.asset_specs = asset_specs

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        resolved_script_path = Path(context.path, self.script_path).absolute()

        @dg.multi_asset(name=Path(self.script_path).stem, specs=self.asset_specs)
        def _asset(context: dg.AssetExecutionContext):
            self.execute(resolved_script_path, context)

        return dg.Definitions(assets=[_asset])

    def execute(self, resolved_script_path: Path, context: dg.AssetExecutionContext):
        return subprocess.run(["sh", str(resolved_script_path)], check=True)
