import os
from collections.abc import Mapping
from typing import Any, Optional

import dagster as dg
from dagster.components import Component, Model, Resolvable, ResolvedAssetSpec, ComponentLoadContext
from pydantic import Field

from .resources import ConfigurableHightouchResource

class HightouchSyncComponent(Component, Resolvable, Model):
    """
    Represents a Hightouch sync as a Dagster asset.

    This component allows you to trigger a Hightouch sync and monitor its completion
    as part of your Dagster asset graph. When materialized, it calls the Hightouch API,
    polls for completion, and reports metadata such as rows processed and sync status.

    Attributes:
        sync_id (str): The ID of the Hightouch sync. Can be a literal string or
            an environment variable (e.g., "$HIGHTOUCH_SYNC_ID").
        asset (ResolvedAssetSpec): The specification of the asset that this
            sync produces.

    Example:
        .. code-block:: yaml

            type: HightouchSyncComponent
            attributes:
              sync_id: "12345"
              asset:
                key: ["marketing", "salesforce_sync"]
    """
    asset: ResolvedAssetSpec
    sync_id: str = Field(description="The ID of the Hightouch sync, or an environment variable starting with $")

    @classmethod
    def get_additional_scope(cls) -> Mapping[str, Any]:
        return {}

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        # Create a unique function name based on the asset key to avoid conflicts
        # when multiple Hightouch components are loaded
        actual_sync_id = self.sync_id
        if actual_sync_id.startswith("$"):
            actual_sync_id = os.getenv(actual_sync_id[1:], "")

        asset_key_str = "_".join(self.asset.key.path)
        function_name = f"hightouch_sync_{asset_key_str}"

        @dg.multi_asset(
            name=function_name,
            specs=[self.asset],
        )
        def _assets(hightouch: ConfigurableHightouchResource):
            result = hightouch.sync_and_poll(actual_sync_id)

            yield dg.MaterializeResult(
                asset_key=self.asset.key,
                metadata={
                    "sync_details": dg.MetadataValue.json(result.sync_details),
                    "sync_run_details": dg.MetadataValue.json(result.sync_run_details),
                    "destination_details": dg.MetadataValue.json(result.destination_details),
                    "query_size": result.sync_run_details.get("querySize"),
                    "completion_ratio": result.sync_run_details.get("completionRatio"),
                    "failed_rows": result.sync_run_details.get("failedRows", {}).get("addedCount", 0),
                },
            )

        return dg.Definitions(assets=[_assets])