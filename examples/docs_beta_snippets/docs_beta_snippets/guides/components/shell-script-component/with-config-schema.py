from collections.abc import Sequence

from dagster_components import (
    AssetSpecSchema,
    Component,
    ComponentLoadContext,
    DSLSchema,
)

import dagster as dg


class ShellCommand(Component, DSLSchema):
    """Models a shell script as a Dagster asset."""

    script_path: str
    asset_specs: Sequence[AssetSpecSchema]

    def build_defs(self, load_context: ComponentLoadContext) -> dg.Definitions: ...
