from collections.abc import Iterator

from dagster_components import component_type
from dagster_components.lib import SlingReplicationCollectionComponent
from dagster_sling import SlingResource

import dagster as dg


@component_type(name="debug_sling_replication")
class DebugSlingReplicationComponent(SlingReplicationCollectionComponent):
    def execute(
        self, context: dg.AssetExecutionContext, sling: SlingResource
    ) -> Iterator:
        context.log.info("*******************CUSTOM*************************")
        return sling.replicate(context=context, debug=True)
