import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dagster_components import (
    AssetSpecSchema,
    Component,
    ComponentLoadContext,
    ResolvableFromSchema,
    YamlSchema,
)
from dagster_components.core.schema.objects import AssetSpecSequenceField

import dagster as dg


class ShellScriptSchema(YamlSchema):
    script_path: str
    asset_specs: Sequence[AssetSpecSchema]


@dataclass
class ShellCommand(Component, ResolvableFromSchema[ShellScriptSchema]):
    script_path: str
    asset_specs: AssetSpecSequenceField

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
