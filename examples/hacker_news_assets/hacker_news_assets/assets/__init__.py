from typing import Optional

from hacker_news_assets.resources import get_resource_defs_for_environment

from dagster import AssetGroup, in_process_executor


def build_asset_group(env: Optional[str]) -> AssetGroup:
    if env not in ["production", "staging", "local"]:
        raise ValueError(f"Unexpected env: {env}")

    resource_defs = get_resource_defs_for_environment(env)
    executor_def = None if env in ["production", "staging"] else in_process_executor

    return AssetGroup.from_package_name(
        __name__, resource_defs=resource_defs, executor_def=executor_def
    )
