from collections.abc import Iterator

from dagster_components import registered_component_type
from dagster_components.lib import SlingReplicationCollection
from dagster_sling import SlingResource

import dagster as dg


@registered_component_type(name="debug_sling_replication")
class DebugSlingReplicationComponent(SlingReplicationCollection):
    def execute(
        self, context: dg.AssetExecutionContext, sling: SlingResource
    ) -> Iterator:
        context.log.info("*******************CUSTOM*************************")
        return sling.replicate(context=context, debug=True)
