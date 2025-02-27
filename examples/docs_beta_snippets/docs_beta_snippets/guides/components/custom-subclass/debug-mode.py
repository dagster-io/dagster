from collections.abc import Iterator

from dagster_components.lib import SlingReplicationCollection
from dagster_sling import SlingResource

import dagster as dg


class DebugSlingReplicationComponent(SlingReplicationCollection):
    def execute(
        self, context: dg.AssetExecutionContext, sling: SlingResource
    ) -> Iterator:
        context.log.info("*******************CUSTOM*************************")
        return sling.replicate(context=context, debug=True)
