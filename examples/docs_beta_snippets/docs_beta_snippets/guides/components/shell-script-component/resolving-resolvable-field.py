from collections.abc import Sequence

from dagster_components import AssetSpecSchema, Component, DSLSchema


class ShellCommand(Component, DSLSchema):
    path: str
    asset_specs: Sequence[AssetSpecSchema]
