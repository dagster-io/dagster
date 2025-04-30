from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from typing import Optional, Union

from dagster import AssetExecutionContext, AssetMaterialization, Definitions, MaterializeResult
from dagster.components import Component, ComponentLoadContext, Resolvable, scaffold_with
from dagster.components.resolved.core_models import AssetPostProcessor
from dagster_sling.components.common import (
    ResolvedSlingResource,
    SlingReplicationSpecModel,
    apply_post_processors,
    build_sling_component_asset,
    default_execute,
)
from dagster_sling.components.sling_replication.scaffolder import (
    SlingReplicationComponentScaffolder,
)
from dagster_sling.resources import SlingResource


@scaffold_with(SlingReplicationComponentScaffolder)
@dataclass
class SlingReplicationComponent(Component, Resolvable):
    replication: SlingReplicationSpecModel
    resource: ResolvedSlingResource = field(default_factory=SlingResource)
    asset_post_processors: Optional[Sequence[AssetPostProcessor]] = None

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        assets_def = build_sling_component_asset(
            context, self.replication, self.resource, self.execute
        )
        return apply_post_processors(Definitions([assets_def]), self.asset_post_processors)

    def execute(
        self,
        context: AssetExecutionContext,
        sling: SlingResource,
        replication_spec_model: SlingReplicationSpecModel,
    ) -> Iterator[Union[AssetMaterialization, MaterializeResult]]:
        return default_execute(context, sling, replication_spec_model)
