import os

from hacker_news_assets.resources import get_resource_defs_for_environment

from dagster import AssetGroup, in_process_executor


def build_asset_group():
    env = os.environ.get("ENVIRONMENT", "local")
    if env not in ["production", "staging", "local"]:
        raise ValueError(f"Unexpected value for ENVIRONMENT env variable: {env}")

    resource_defs = get_resource_defs_for_environment(env)
    executor_def = None if env in ["production", "staging"] else in_process_executor

    return AssetGroup.from_package_name(
        __name__, resource_defs=resource_defs, executor_def=executor_def
    )


asset_group = build_asset_group()
