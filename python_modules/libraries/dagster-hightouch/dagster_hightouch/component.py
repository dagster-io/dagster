import os
from collections.abc import Mapping
from typing import Any

import dagster as dg
from dagster.components import Component, Model, Resolvable, ResolvedAssetSpec
from pydantic import Field

from dagster_hightouch.resources import HightouchResource


class HightouchSyncComponent(Component, Resolvable, Model):
    """A component that represents a Hightouch Sync.

    It defines an asset that triggers the sync and waits for it to complete.
    """

    asset: ResolvedAssetSpec
    sync_id_env_var: str = Field(
        ...,
        description="The name of the environment variable containing the Hightouch Sync ID.",
    )

    @classmethod
    def get_additional_scope(cls) -> Mapping[str, Any]:
        return {}

    def build_defs(self, context) -> dg.Definitions:
        asset_key_str = "_".join(self.asset.key.path)
        function_name = f"hightouch_sync_{asset_key_str}"

        sync_id = os.getenv(self.sync_id_env_var)

        @dg.multi_asset(
            name=function_name,
            specs=[self.asset],
        )
        def _asset(context: dg.AssetExecutionContext, hightouch: HightouchResource):
            if not sync_id:
                raise ValueError(f"Environment variable {self.sync_id_env_var} is not set.")

            context.log.info(f"Triggering Hightouch sync: {sync_id}")
            result = hightouch.sync_and_poll(sync_id=sync_id)

            yield dg.MaterializeResult(
                asset_key=self.asset.key,
                metadata={
                    "sync_details": result.sync_details,
                    "sync_run_details": result.sync_run_details,
                    "destination_details": result.destination_details,
                    "query_size": result.sync_run_details.get("querySize"),
                    "completion_ratio": result.sync_run_details.get("completionRatio"),
                },
            )

        return dg.Definitions(assets=[_asset])
