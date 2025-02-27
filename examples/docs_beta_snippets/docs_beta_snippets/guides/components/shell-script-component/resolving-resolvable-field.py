from collections.abc import Sequence

from dagster_components import AssetSpecSchema, Component, ResolvableSchema


class ShellCommandParams(ResolvableSchema):
    path: str
    asset_specs: Sequence[AssetSpecSchema]


class ShellCommand(Component): ...
