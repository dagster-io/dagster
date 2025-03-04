from collections.abc import Sequence

from dagster_components import AssetSpecSchema, Component
from dagster_components.core.schema.base import PlainSamwiseSchema


class ShellCommandParams(PlainSamwiseSchema):
    path: str
    asset_specs: Sequence[AssetSpecSchema]


class ShellCommand(Component): ...
