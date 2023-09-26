from typing import List, Iterable, Optional, Union, Dict, Any
from dagster import (
    AssetsDefinition,
    asset,
    AssetKey,
    AssetExecutionContext,
    FreshnessPolicy,
    AutoMaterializePolicy,
)
from dagster._core.definitions.events import CoercibleToAssetKey
from dagster_elt.sling.resources import SlingMode, SlingResource
import re


def build_sling_asset(
    source_stream: str,
    target_object: str,
    mode: SlingMode = SlingMode.FULL_REFRESH,
    primary_key: Optional[Union[str, List[str]]] = None,
    update_key: Optional[Union[str, List[str]]] = None,
    source_options: Optional[Dict[str, Any]] = None,
    target_options: Optional[Dict[str, Any]] = None,
    asset_key: Optional[CoercibleToAssetKey] = None,
    sling_resource_key: str = "sling",
    group_name: Optional[str] = None,
    deps: Optional[Iterable[CoercibleToAssetKey]] = None,
    freshness_policy: Optional[FreshnessPolicy] = None,
    auto_materialize_policy: Optional[AutoMaterializePolicy] = None,
) -> AssetsDefinition:
    """Factory which builds an asset definition that syncs the given source table to the given
    destination table.
    """
    if primary_key is not None and not isinstance(primary_key, list):
        primary_key = [primary_key]

    if update_key is not None and not isinstance(update_key, list):
        update_key = [update_key]

    @asset(
        required_resource_keys={sling_resource_key},
        key=AssetKey([target_object]) if not asset_key else asset_key,
        deps=deps,
        compute_kind="sling",
        group_name=group_name,
        freshness_policy=freshness_policy,
        auto_materialize_policy=auto_materialize_policy,
    )
    def sync(context: AssetExecutionContext) -> None:
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
                context.add_output_metadata({"row_count": int(match.group(1))})
                context.log.debug(f"Added metadata: {int(match.group(1))}")
            context.log.info(stdout_line)

    return sync
