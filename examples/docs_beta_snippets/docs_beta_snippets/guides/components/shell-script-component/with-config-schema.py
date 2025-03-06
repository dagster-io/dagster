from collections.abc import Sequence

from dagster_components import (
    AssetSpecModel,
    Component,
    ComponentLoadContext,
    ResolvableModel,
)

import dagster as dg


class ShellCommand(Component, ResolvableModel):
    """Models a shell script as a Dagster asset."""

    script_path: str
    asset_specs: Sequence[AssetSpecModel]

    def build_defs(self, load_context: ComponentLoadContext) -> dg.Definitions: ...
