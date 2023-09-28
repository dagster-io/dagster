import re
from typing import Any, Dict, List, Optional, Union

from dagster import (
    AssetExecutionContext,
    AssetsDefinition,
    AssetSpec,
    MaterializeResult,
    multi_asset,
)

from dagster_embedded_elt.sling.resources import SlingMode, SlingResource


def build_sling_asset(
    asset_spec: AssetSpec,
    source_stream: str,
    target_object: str,
    mode: SlingMode = SlingMode.FULL_REFRESH,
    primary_key: Optional[Union[str, List[str]]] = None,
    update_key: Optional[Union[str, List[str]]] = None,
    source_options: Optional[Dict[str, Any]] = None,
    target_options: Optional[Dict[str, Any]] = None,
    sling_resource_key: str = "sling",
) -> AssetsDefinition:
    """Factory which builds an asset definition that syncs the given source table to the given
    destination table.
    """
    if primary_key is not None and not isinstance(primary_key, list):
        primary_key = [primary_key]

    if update_key is not None and not isinstance(update_key, list):
        update_key = [update_key]

    @multi_asset(
        compute_kind="sling", specs=[asset_spec], required_resource_keys={sling_resource_key}
    )
    def sync(context: AssetExecutionContext) -> MaterializeResult:
        sling: SlingResource = getattr(context.resources, sling_resource_key)
        for stdout_line in sling.sync(
            source_stream=source_stream,
            target_object=target_object,
            mode=mode,
            primary_key=primary_key,
            update_key=update_key,
            source_options=source_options,
            target_options=target_options,
        ):
            match = re.search(r"(\d+) rows", stdout_line)
            if match:
                last_row_count_observed = int(match.group(1))
            context.log.info(stdout_line)

        return MaterializeResult(
            metadata=(
                {} if last_row_count_observed is None else {"row_count": last_row_count_observed}
            )
        )

    return sync
