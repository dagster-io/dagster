from typing import List, Iterable, Optional, Union
from dagster import (
    AssetsDefinition,
    asset,
    AssetKey,
    AssetExecutionContext,
    FreshnessPolicy,
    AutoMaterializePolicy,
)
from dagster._core.definitions.events import CoercibleToAssetKey
from . import SlingMode, SlingResource, SlingSourceConfig, SlingTarget
import re


def build_sling_asset(
    source_table: str,
    dest_table: str,
    mode: SlingMode = SlingMode.FULL_REFRESH,
    sling_resource_key: str = "sling",
    primary_key: Optional[Union[str, List[str]]] = None,
    update_key: Optional[Union[str, List[str]]] = None,
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
        key=AssetKey([dest_table]),
        deps=deps,
        compute_kind="sling",
        group_name=group_name,
        freshness_policy=freshness_policy,
        auto_materialize_policy=auto_materialize_policy,
    )
    def sync(context: AssetExecutionContext) -> None:
        sling: SlingResource = getattr(context.resources, sling_resource_key)
        source_config = SlingSourceConfig(
            stream=source_table,
            primary_key=primary_key,
            update_key=update_key,
        )
        target_config = SlingTarget(object=dest_table)
        for stdout_line in sling.sync(
            source=source_config,
            target=target_config,
            mode=mode,
        ):
            cleaned_line = re.sub(r"\[[0-9;]+[a-zA-Z]", " ", stdout_line)
            trimmed_line = cleaned_line[cleaned_line.find("INF") + 6 :].strip()
            match = re.search(r"(\d+) rows", trimmed_line)
            if match:
                context.add_output_metadata({"row_count": int(match.group(1))})
            context.log.info(trimmed_line)

    return sync
