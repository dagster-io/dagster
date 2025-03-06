from collections.abc import Sequence

from dagster_components import AssetSpecSchema, Component, ResolvableModel


class ShellCommand(Component, ResolvableModel):
    path: str
    asset_specs: Sequence[AssetSpecSchema]
