from collections.abc import Sequence

import dagster as dg


class ShellCommand(dg.Component, dg.Resolvable):
    """Models a shell script as a Dagster asset."""

    def __init__(
        self,
        script_path: str,
        asset_specs: Sequence[dg.ResolvedAssetSpec],
    ):
        self.script_path = script_path
        self.asset_specs = asset_specs

    # highlight-start
    @classmethod
    def get_spec(cls) -> dg.ComponentTypeSpec:
        return dg.ComponentTypeSpec(
            owners=["john@dagster.io"],
            tags=["shell", "script"],
        )

    # highlight-end

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions: ...
