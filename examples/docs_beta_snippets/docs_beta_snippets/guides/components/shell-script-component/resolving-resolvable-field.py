from collections.abc import Sequence

from dagster_components import (
    AssetSpecSchema,
    Component,
    ResolvableSchema,
    registered_component_type,
)


class ShellCommandParams(ResolvableSchema):
    path: str
    asset_specs: Sequence[AssetSpecSchema]


@registered_component_type(name="shell_command")
class ShellCommand(Component): ...
