from collections.abc import Sequence
from dataclasses import dataclass

import dagster as dg


@dataclass
class ShellCommand(dg.Component, dg.Resolvable):
    """Models a shell script as a Dagster asset."""

    script_path: str
    asset_specs: Sequence[dg.ResolvedAssetSpec]

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions: ...
