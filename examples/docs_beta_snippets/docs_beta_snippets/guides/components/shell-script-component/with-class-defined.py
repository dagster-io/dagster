from collections.abc import Sequence
from dataclasses import dataclass

from dagster_components import (
    AssetSpecModel,
    Component,
    ComponentLoadContext,
    ResolvableModel,
    ResolvedFrom,
)
from dagster_components.core.schema.objects import AssetSpecSequenceField

import dagster as dg


class ShellCommandModel(ResolvableModel):
    script_path: str
    asset_specs: Sequence[AssetSpecModel]


@dataclass
class ShellCommand(Component, ResolvedFrom[ShellCommandModel]):
    script_path: str
    asset_specs: AssetSpecSequenceField

    def build_defs(self, load_context: ComponentLoadContext) -> dg.Definitions: ...
