from collections.abc import Sequence

from dagster_components import (
    Component,
    ComponentLoadContext,
    Resolvable,
    ResolvedAssetSpec,
)

import dagster as dg


class ShellCommand(Component, Resolvable):
    """Models a shell script as a Dagster asset."""

    def __init__(
        self,
        script_path: str,
        asset_specs: Sequence[ResolvedAssetSpec],
    ):
        self.script_path = script_path
        self.asset_specs = asset_specs

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions: ...
