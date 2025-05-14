from collections.abc import Sequence
from dataclasses import dataclass

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

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions: ...
