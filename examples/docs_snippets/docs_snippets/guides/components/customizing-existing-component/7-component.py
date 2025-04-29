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
        sling: SlingResource,
        replication_spec_model: SlingReplicationSpecModel,
    ) -> Iterator:
        context.log.info("*******************CUSTOM*************************")
        return sling.replicate(context=context, debug=True)
