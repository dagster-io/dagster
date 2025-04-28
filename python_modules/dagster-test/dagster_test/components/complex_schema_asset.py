from collections.abc import Sequence
from dataclasses import dataclass
from typing import Optional

from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components import Component, ComponentLoadContext, Resolvable
from dagster.components.resolved.core_models import (
    AssetPostProcessor,
    OpSpec,
    ResolvedAssetAttributes,
)


@dataclass
class ComplexAssetComponent(Component, Resolvable):
    """An asset that has a complex schema."""

    value: str
    list_value: list[str]
    obj_value: dict[str, str]
    op: Optional[OpSpec] = None
    asset_attributes: Optional[ResolvedAssetAttributes] = None
    asset_post_processors: Optional[Sequence[AssetPostProcessor]] = None

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @asset(spec=self.asset_attributes)
        def dummy(context: AssetExecutionContext):
            return self.value

        defs = Definitions(assets=[dummy])
        for post_processor in self.asset_post_processors or []:
            defs = post_processor(defs)
        return defs
