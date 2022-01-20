from typing import List, Optional
from dagster import AssetKey, Out, Output
from dagster.core.asset_defs import multi_asset

from dagster_fivetran.resources import DEFAULT_POLL_INTERVAL
from dagster_fivetran.utils import generate_materializations


def fivetran_assets_factory(
    connector_id: str,
    asset_keys: List[AssetKey],
    name: Optional[str] = None,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    poll_timeout: Optional[float] = None,
    io_manager_key: Optional[str] = None,
):
    @multi_asset(
        name=name or f"fivetran_sync_{connector_id}",
        outs={
            asset_key.path[-1]: Out(io_manager_key=io_manager_key, asset_key=asset_key)
            for asset_key in asset_keys
        },
        required_resource_keys={"fivetran"},
    )
    def _assets(context):
        fivetran_output = context.resources.fivetran.sync_and_poll(
            connector_id=connector_id,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
        )
        for materialization in generate_materializations(fivetran_output, asset_key_prefix=[]):
            asset_key = materialization.asset_key
            # scan through all tables actually created, if it was expected then emit an Output.
            # otherwise, emit a runtime AssetMaterialization
            if asset_key in asset_keys:
                yield Output(
                    value=None,
                    output_name=asset_key.path[-1],
                    metadata_entries=materialization.metadata_entries,
                )
            else:
                yield materialization

    return _assets
