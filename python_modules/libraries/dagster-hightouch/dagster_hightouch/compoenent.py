import os
from collections.abc import Mapping
from typing import Any

import dagster as dg
from dagster.components import Component, Model, Resolvable, ResolvedAssetSpec
from dagster_dbt import get_asset_key_for_model
from dagster_hightouch import HightouchResource


def dbt_asset_key(model_name: str) -> dg.AssetKey:
    from dagster_open_platform.defs.dbt.assets import get_dbt_non_partitioned_models

    return get_asset_key_for_model([get_dbt_non_partitioned_models()], model_name)


class DopHightouchSyncComponent(Component, Resolvable, Model):
    asset: ResolvedAssetSpec
    sync_id_env_var: str

    @classmethod
    def get_additional_scope(cls) -> Mapping[str, Any]:
        return {"dbt_asset_key": dbt_asset_key}

    def build_defs(self, context) -> dg.Definitions:
        # Create a unique function name based on the asset key to avoid conflicts
        # when multiple Hightouch components are loaded
        asset_key_str = "_".join(self.asset.key.path)
        function_name = f"hightouch_sync_{asset_key_str}"

        @dg.multi_asset(
            name=function_name,
            specs=[self.asset],
        )
        def _assets(hightouch: HightouchResource):
            result = hightouch.sync_and_poll(os.getenv(self.sync_id_env_var, ""))
            yield dg.MaterializeResult(
                asset_key=self.asset.key,
                metadata={
                    "sync_details": result.sync_details,
                    "sync_run_details": result.sync_run_details,
                    "destination_details": result.destination_details,
                    "query_size": result.sync_run_details.get("querySize"),
                    "completion_ratio": result.sync_run_details.get("completionRatio"),
                    "failed_rows": result.sync_run_details.get("failedRows", {}).get("addedCount"),
                },
            )

        return dg.Definitions(assets=[_assets])