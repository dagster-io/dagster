import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dagster_components import (
    AssetSpecModel,
    Component,
    ComponentLoadContext,
    ResolvableModel,
    ResolvedFrom,
)
from dagster_components.resolved.core_models import ResolvedAssetSpec

import dagster as dg


class ShellCommandModel(ResolvableModel):
    script_path: str
    asset_specs: Sequence[AssetSpecModel]


@dataclass
class ShellCommand(Component, ResolvedFrom[ShellCommandModel]):
    script_path: str
    asset_specs: Sequence[ResolvedAssetSpec]

    @classmethod
    def get_additional_scope(cls) -> Mapping[str, Any]:
        return {
            "daily_partitions": dg.DailyPartitionsDefinition(start_date="2024-01-01")
        }

    def build_defs(self, load_context: ComponentLoadContext) -> dg.Definitions:
        @dg.multi_asset(name=Path(self.script_path).stem, specs=self.asset_specs)
        def _asset(context: dg.AssetExecutionContext):
            self.execute(context)

        return dg.Definitions(assets=[_asset])

    def execute(self, context: dg.AssetExecutionContext):
        return subprocess.run(["sh", self.script_path], check=True)
