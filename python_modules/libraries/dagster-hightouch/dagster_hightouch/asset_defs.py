from typing import Optional, Set

from dagster import AssetKey, AssetMaterialization, AssetsDefinition, Output, asset
from .types import HightouchOutput
from .utils import (
    generate_metadata_from_parsed_run,
    parse_sync_run_details,
)


def build_hightouch_asset(
    sync_id: str,
    destination_type: str,
    destination_object: str,
    non_argument_deps: Optional[Set[AssetKey]],
) -> AssetsDefinition:
    @asset(
        name=destination_type + "_" + destination_object,
        namespace="hightouch",
        non_argument_deps=non_argument_deps,
        required_resource_keys={"hightouch"},
    )
    def _assets(context):
        hightouch_output: HightouchOutput = context.resources.hightouch.sync_and_poll(
            sync_id=sync_id,
        )

        context.log_event(
            AssetMaterialization(
                ["hightouch", "sync_run"],
                description="Hightouch Sync Run Details",
                metadata=generate_metadata_from_parsed_run(
                    parse_sync_run_details(hightouch_output.sync_run_details)
                ),
            )
        )
        yield Output(value=None)

    return _assets
