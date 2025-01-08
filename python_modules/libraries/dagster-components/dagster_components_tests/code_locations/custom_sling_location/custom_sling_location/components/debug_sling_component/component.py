from typing import Iterator

from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster_components import component_type
from dagster_components.lib.sling_replication_collection import SlingReplicationCollectionComponent
from dagster_embedded_elt.sling import SlingResource


@component_type(name="debug_sling_replication")
class DebugSlingReplicationComponent(SlingReplicationCollectionComponent):
    def execute(self, context: AssetExecutionContext, sling: SlingResource) -> Iterator:
        return sling.replicate(context=context, debug=True)
