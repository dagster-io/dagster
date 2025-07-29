from collections.abc import Sequence

import dagster as dg


class ShellCommand(dg.Component, dg.Model, dg.Resolvable):
    # highlight-start
    """Models a shell script as a Dagster asset."""

    script_path: str
    asset_specs: Sequence[dg.ResolvedAssetSpec]
    # highlight-end

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions: ...
