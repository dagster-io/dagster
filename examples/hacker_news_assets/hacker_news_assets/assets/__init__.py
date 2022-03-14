from typing import Optional

from hacker_news_assets.resources import get_resource_defs_for_environment

from dagster import AssetGroup, in_process_executor


def build_asset_group(deployment_name: Optional[str]) -> AssetGroup:
    if deployment_name not in ["production", "staging", "local"]:
        raise ValueError(f"Unexpected deploynent name: {deployment_name}")

    resource_defs = get_resource_defs_for_environment(deployment_name)
    executor_def = None if deployment_name in ["production", "staging"] else in_process_executor

    return AssetGroup.from_package_name(
        __name__, resource_defs=resource_defs, executor_def=executor_def
    )
