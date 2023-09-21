from typing import List, Iterable, Optional, Union
from dagster import AssetsDefinition, asset, AssetKey, AssetExecutionContext
from dagster._core.definitions.events import CoercibleToAssetKey
from . import SlingMode, SlingResource, SlingSource, SlingTarget
import re


def build_sling_asset(
    key: AssetKey,
    sling_resource_key: str,
    source_table: str,
    dest_table: str,
    mode: object = SlingMode.FULL_REFRESH,
    primary_key: Optional[Union[str, List[str]]] = None,
    update_key: Optional[Union[str, List[str]]] = None,
    deps: Optional[Iterable[CoercibleToAssetKey]] = None,
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
        key=key,
        deps=deps,
    )
    def sync(context: AssetExecutionContext) -> None:
        sling: SlingResource = getattr(context.resources, sling_resource_key)
        source_config = SlingSource(
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
            print(stdout_line)
            cleaned_line = re.sub(r"\[[0-9;]+[a-zA-Z]", " ", stdout_line)
            trimmed_line = cleaned_line[cleaned_line.find("INF") + 6 :].strip()
            match = re.search(r"(\d+) rows", trimmed_line)
            if match:
                context.add_output_metadata({"row_count": int(match.group(1))})
            context.log.info(trimmed_line)

    return sync
