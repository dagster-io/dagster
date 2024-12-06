from typing import Iterator

from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster_components import component
from dagster_components.lib.sling_replication import SlingReplicationComponent
from dagster_embedded_elt.sling import SlingResource


@component(name="debug_sling_replication")
class DebugSlingReplicationComponent(SlingReplicationComponent):
    def execute(self, context: AssetExecutionContext, sling: SlingResource) -> Iterator:
        return sling.replicate(context=context, debug=True)
