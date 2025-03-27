from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated, Optional

from dagster._core.definitions.definitions_class import Definitions
from typing_extensions import Self

from dagster_components import AssetPostProcessorModel
from dagster_components.component.component import Component
from dagster_components.core.context import ComponentLoadContext
from dagster_components.core.defs_module import (
    DefsModule,
    PythonModuleDecl,
    SubpackageDefsModuleDecl,
)
from dagster_components.resolved.core_models import AssetPostProcessor
from dagster_components.resolved.model import ResolvableModel, ResolvedFrom, Resolver, resolve_model


class DefsModuleArgsModel(ResolvableModel):
    asset_post_processors: Optional[Sequence[AssetPostProcessorModel]] = None


@dataclass
class ResolvedDefsModuleArgs(ResolvedFrom[DefsModuleArgsModel]):
    asset_post_processors: Annotated[Sequence[AssetPostProcessor], Resolver.from_annotation()]


class DefsFolderComponent(Component):
    """Wraps a DefsModule to allow the addition of arbitrary attributes."""

    def __init__(
        self, post_processors: Sequence[AssetPostProcessor], defs_module: Optional[DefsModule]
    ):
        self.post_processors = post_processors
        self.defs_module = defs_module

    @classmethod
    def get_schema(cls) -> type[DefsModuleArgsModel]:
        return DefsModuleArgsModel

    @classmethod
    def load(cls, attributes: DefsModuleArgsModel, context: ComponentLoadContext) -> Self:  # type: ignore
        path = context.path
        decl = PythonModuleDecl.from_path(path) or SubpackageDefsModuleDecl.from_path(path)
        defs_module = decl.load(context) if decl else None
        resolved_args = resolve_model(
            attributes, ResolvedDefsModuleArgs, context.resolution_context.at_path("attributes")
        )
        return cls(post_processors=resolved_args.asset_post_processors, defs_module=defs_module)

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        defs = self.defs_module.build_defs() if self.defs_module else Definitions()
        for post_processor in self.post_processors:
            defs = post_processor.fn(defs)
        return defs
