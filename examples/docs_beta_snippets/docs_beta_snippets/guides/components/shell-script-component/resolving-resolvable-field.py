from collections.abc import Sequence

from dagster_components import AssetSpecSchema, Component, YamlSchema


class ShellCommandParams(YamlSchema):
    path: str
    asset_specs: Sequence[AssetSpecSchema]


class ShellCommand(Component): ...
