from collections.abc import Sequence

from dagster_components import (
    AssetSpecModel,
    Component,
    DefsModuleLoadContext,
    ResolvableModel,
)

import dagster as dg


class ShellCommand(Component, ResolvableModel):
    """Models a shell script as a Dagster asset."""

    script_path: str
    asset_specs: Sequence[AssetSpecModel]

    def build_defs(self, load_context: DefsModuleLoadContext) -> dg.Definitions: ...
