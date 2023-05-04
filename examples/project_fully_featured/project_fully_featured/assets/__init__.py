import json
import os

from dagster import OpExecutionContext, ResourceParam, load_assets_from_package_module
from dagster._core.definitions.events import AssetKey
from dagster._utils import file_relative_path
from dagster_dbt.asset_decorators import (
    DbtManifest,
    construct_subset_kwargs_from_manifest,
    dbt_multi_asset,
)
from dagster_dbt.asset_defs import _events_for_structured_json_line
from dagster_dbt.asset_utils import default_asset_key_fn
from dagster_dbt.cli.resources import DbtCliClientResource

from . import activity_analytics, core, recommender

CORE = "core"
ACTIVITY_ANALYTICS = "activity_analytics"
RECOMMENDER = "recommender"
DBT_PROJECT_DIR = file_relative_path(__file__, "../../dbt_project")
DBT_PROFILES_DIR = DBT_PROJECT_DIR + "/config"

core_assets = load_assets_from_package_module(package_module=core, group_name=CORE)

activity_analytics_assets = load_assets_from_package_module(
    package_module=activity_analytics,
    key_prefix=["snowflake", ACTIVITY_ANALYTICS],
    group_name=ACTIVITY_ANALYTICS,
)

recommender_assets = load_assets_from_package_module(
    package_module=recommender, group_name=RECOMMENDER
)

# dbt_assets = load_assets_from_dbt_manifest(
#     json.load(open(os.path.join(DBT_PROJECT_DIR, "target", "manifest.json"), encoding="utf-8")),
#     io_manager_key="warehouse_io_manager",
#     # the schemas are already specified in dbt, so we don't need to also specify them in the key
#     # prefix here
#     key_prefix=["snowflake"],
#     source_key_prefix=["snowflake"],
# )

manifest_path = os.path.join(DBT_PROJECT_DIR, "target", "manifest.json")

with open(manifest_path) as f:
    manifest = json.load(f)

manifest_wrapper = DbtManifest(manifest)


@dbt_multi_asset(manifest=manifest)
def dbt_assets(context: OpExecutionContext, dbt: ResourceParam[DbtCliClientResource]):
    kwargs = construct_subset_kwargs_from_manifest(
        context=context,
        manifest=manifest,
    )

    for parsed_json_line in dbt.get_dbt_client().cli_stream_json(
        command="run",
        **kwargs,
    ):
        yield from _events_for_structured_json_line(
            json_line=parsed_json_line, context=context, manifest_json=manifest
        )


# Say that I want to map the existing asset keys to a new set of asset keys.
default_output_asset_keys = dbt_assets.node_keys_by_output_name.values()
newly_mapped_output_asset_keys: dict[AssetKey, AssetKey] = {}

for asset_key in default_output_asset_keys:
    node_info = manifest_wrapper.get_node_by_asset_key(asset_key)

    # do whatever with node_info

    new_asset_key = AssetKey(["yeehaw", *default_asset_key_fn(node_info).path])

    newly_mapped_output_asset_keys[asset_key] = new_asset_key

dbt_assets = dbt_assets.with_attributes(
    output_asset_key_replacements=newly_mapped_output_asset_keys
)
