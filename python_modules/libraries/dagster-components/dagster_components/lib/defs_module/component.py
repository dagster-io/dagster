from collections.abc import Sequence
from dataclasses import dataclass
from typing import Optional

from dagster._core.definitions.definitions_class import Definitions
from pydantic import BaseModel
from typing_extensions import Self

from dagster_components import Component, ComponentLoadContext, Resolvable
from dagster_components.core.defs_module import DefsModule, FolderDefsModule
from dagster_components.resolved.core_models import AssetPostProcessor


@dataclass
class ResolvedDefsModuleArgs(Resolvable):
    asset_post_processors: Sequence[AssetPostProcessor]


class DefsFolderComponent(Component):
    """Wraps a DefsModule to allow the addition of arbitrary attributes."""

    def __init__(
        self, post_processors: Sequence[AssetPostProcessor], defs_module: Optional[DefsModule]
    ):
        self.post_processors = post_processors
        self.defs_module = defs_module

    @classmethod
    def get_schema(cls):
        return ResolvedDefsModuleArgs.model()

    @classmethod
    def load(cls, attributes: BaseModel, context: ComponentLoadContext) -> Self:  # type: ignore
        resolved_args = ResolvedDefsModuleArgs.resolve_from_model(
            context.resolution_context.at_path("attributes"),
            attributes,
        )
        return cls(resolved_args.asset_post_processors, FolderDefsModule.from_context(context))

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        defs = self.defs_module.build_defs(context) if self.defs_module else Definitions()
        for post_processor in self.post_processors:
            defs = post_processor(defs)
        return defs
