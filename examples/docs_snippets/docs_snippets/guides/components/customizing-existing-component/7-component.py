from collections.abc import Iterator

from dagster_sling import (
    SlingReplicationCollectionComponent,
    SlingReplicationSpecModel,
    SlingResource,
)

import dagster as dg


class CustomSlingReplicationComponent(SlingReplicationCollectionComponent):
    def execute(
        self,
        context: dg.AssetExecutionContext,
        replication_spec_model: SlingReplicationSpecModel,
    ) -> Iterator:
        context.log.info("*******************CUSTOM*************************")
        return self.sling_resource.replicate(context=context, debug=True)
