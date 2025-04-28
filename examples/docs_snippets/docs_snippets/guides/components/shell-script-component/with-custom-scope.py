import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import dagster as dg
from dagster.components import (
    Component,
    ComponentLoadContext,
    Resolvable,
    ResolvedAssetSpec,
)


@dataclass
class ShellCommand(Component, Resolvable):
    script_path: str
    asset_specs: Sequence[ResolvedAssetSpec]

    @classmethod
    def get_additional_scope(cls) -> Mapping[str, Any]:
        return {
            "daily_partitions": dg.DailyPartitionsDefinition(start_date="2024-01-01")
        }

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        @dg.multi_asset(name=Path(self.script_path).stem, specs=self.asset_specs)
        def _asset(context: dg.AssetExecutionContext):
            self.execute(context)

        return dg.Definitions(assets=[_asset])

    def execute(self, context: dg.AssetExecutionContext):
        return subprocess.run(["sh", self.script_path], check=True)
