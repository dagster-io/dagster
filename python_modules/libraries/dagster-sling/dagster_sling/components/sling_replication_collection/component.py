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
from dagster_sling.components.sling_replication_collection.scaffolder import (
    SlingReplicationCollectionComponentScaffolder,
)
from dagster_sling.resources import SlingResource


@scaffold_with(SlingReplicationCollectionComponentScaffolder)
@dataclass
class SlingReplicationCollectionComponent(Component, Resolvable):
    """Expose one or more Sling replications to Dagster as assets.

    [Sling](https://slingdata.io/) is a Powerful Data Integration tool enabling seamless ELT
    operations as well as quality checks across files, databases, and storage systems.

    dg scaffold dagster_sling.SlingReplicationCollectionComponent {component_path} to get started.

    This will create a component.yaml as well as a `replication.yaml` which is a Sling-specific configuration
    file. See Sling's [documentation](https://docs.slingdata.io/concepts/replication#overview) on `replication.yaml`.
    """

    resource: ResolvedSlingResource = field(default_factory=SlingResource)
    replications: Sequence[SlingReplicationSpecModel] = field(default_factory=list)
    asset_post_processors: Optional[Sequence[AssetPostProcessor]] = None

    def execute(
        self,
        context: AssetExecutionContext,
        sling: SlingResource,
        replication_spec_model: SlingReplicationSpecModel,
    ) -> Iterator[Union[AssetMaterialization, MaterializeResult]]:
        return default_execute(context, sling, replication_spec_model)

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return apply_post_processors(
            Definitions(
                assets=[
                    build_sling_component_asset(context, replication, self.resource, self.execute)
                    for replication in self.replications
                ],
            ),
            self.asset_post_processors,
        )
