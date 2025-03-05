from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated

from dagster_components import (
    AssetSpecSchema,
    Component,
    ComponentLoadContext,
    ResolvableFromSchema,
    YamlSchema,
)

import dagster as dg


class ShellScriptSchema(YamlSchema):
    script_path: str
    asset_specs: Sequence[AssetSpecSchema]


@dataclass
class ShellCommand(Component, ResolvableFromSchema[ShellScriptSchema]):
    script_path: str
    asset_specs: Annotated[Sequence[dg.AssetSpec], AssetSpecSchema.resolver_for_seq()]

    def build_defs(self, load_context: ComponentLoadContext) -> dg.Definitions: ...
