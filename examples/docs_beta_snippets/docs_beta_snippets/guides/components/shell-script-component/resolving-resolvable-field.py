from collections.abc import Sequence

from dagster_components import AssetSpecModel, Component, ResolvableModel


class ShellCommand(Component, ResolvableModel):
    path: str
    asset_specs: Sequence[AssetSpecModel]
