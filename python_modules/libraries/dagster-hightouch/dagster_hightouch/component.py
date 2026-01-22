import os
from collections.abc import Mapping
from typing import Any

import dagster as dg
from dagster.components import Component, ComponentLoadContext, Model, Resolvable, ResolvedAssetSpec
from pydantic import Field

from dagster_hightouch.resources import ConfigurableHightouchResource


class HightouchSyncComponent(Component, Resolvable, Model):
    """Represents a Hightouch sync as a Dagster asset.

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
    sync_id: str = Field(
        description="The ID of the Hightouch sync, or an environment variable starting with $"
    )

    @classmethod
    def get_additional_scope(cls) -> Mapping[str, Any]:
        return {}

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        # Create a unique function name based on the asset key to avoid conflicts when multiple Hightouch components are loaded
        actual_sync_id = self.sync_id
        if actual_sync_id.startswith("$"):
            env_var_name = actual_sync_id[1:]
            actual_sync_id = os.getenv(env_var_name)
            if not actual_sync_id:
                raise ValueError(f"Environment variable '{env_var_name}' not found.")
        asset_key_str = "_".join(self.asset.key.path)
        function_name = f"hightouch_sync_{asset_key_str}"

        @dg.multi_asset(
            name=function_name,
            specs=[self.asset],
        )
        def _assets(hightouch: ConfigurableHightouchResource):
            result = hightouch.sync_and_poll(actual_sync_id)

            # Summing all failed rows (adds, changes, removes) for accurate reporting
            failed_rows = result.sync_run_details.get("failedRows", {})
            total_failed = sum(
                failed_rows.get(k, 0) for k in ["addedCount", "changedCount", "removedCount"]
            )

            yield dg.MaterializeResult(
                asset_key=self.asset.key,
                metadata={
                    "sync_details": dg.MetadataValue.json(result.sync_details),
                    "sync_run_details": dg.MetadataValue.json(result.sync_run_details),
                    "total_failed_rows": total_failed,
                    "failed_adds": failed_rows.get("addedCount", 0),
                    "failed_changes": failed_rows.get("changedCount", 0),
                    "failed_removes": failed_rows.get("removedCount", 0),
                    "destination_details": dg.MetadataValue.json(result.destination_details),
                    "query_size": result.sync_run_details.get("querySize"),
                    "completion_ratio": result.sync_run_details.get("completionRatio"),
                    "failed_rows": result.sync_run_details.get("failedRows", {}).get(
                        "addedCount", 0
                    ),
                },
            )

        return dg.Definitions(assets=[_assets])
