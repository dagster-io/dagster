import json
import subprocess
import sys
from typing import List, Optional, Sequence, Set

from dagster import (
    AssetsDefinition,
    Definitions,
    Nothing,
    OpExecutionContext,
    asset,
    define_asset_job,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.instance import DagsterInstance
from dagster._core.storage.branching.branching_io_manager import (
    get_text_metadata_value,
    latest_materialization_log_entry,
)
from dagster._utils import file_relative_path

STORAGE_NAMESPACE_METADATA_KEY = "storage_namespace"


def upstream_asset_partition_materialized_in_storage_namespace(
    instance: DagsterInstance,
    upstream_asset_key: AssetKey,
    partition_key: Optional[str],
    storage_namespace: str,
):
    event_log_entry = latest_materialization_log_entry(
        instance=instance,
        asset_key=upstream_asset_key,
        partition_key=partition_key,
    )
    return (
        event_log_entry
        and event_log_entry.asset_materialization
        and get_text_metadata_value(
            event_log_entry.asset_materialization, STORAGE_NAMESPACE_METADATA_KEY
        )
        == storage_namespace
    )


def in_branch():
    return True


def create_asset_namespace_mapping(
    instance: DagsterInstance,
    current_asset_key_str: str,
    partition_key: Optional[str],
    upstream_asset_array: List[str],
    parent_storage_namespace: str,
    branch_storage_namespace: str,
    in_branch: bool,
):
    if not in_branch:
        return {
            asset_key_str: parent_storage_namespace
            for asset_key_str in [current_asset_key_str, *upstream_asset_array]
        }

    # always write this asset to branch namespace if in branch
    asset_namespaces = {current_asset_key_str: branch_storage_namespace}

    # then for every upstream asset see if it has been materialized in the branch
    # if not, read from the parent
    for upstream_asset in upstream_asset_array:
        upstream_asset_key = AssetKey(upstream_asset)
        if upstream_asset_partition_materialized_in_storage_namespace(
            instance=instance,
            upstream_asset_key=upstream_asset_key,
            partition_key=partition_key,
            storage_namespace=branch_storage_namespace,
        ):
            asset_namespaces[upstream_asset] = branch_storage_namespace
        else:
            asset_namespaces[upstream_asset] = parent_storage_namespace

    return asset_namespaces


def build_asset(name: str, upstream_assets: Optional[Sequence[str]] = None) -> AssetsDefinition:
    branch_storage_namespace = "feature-one"
    parent_storage_namespace = "prod"

    upstream_asset_array = [*upstream_assets] if upstream_assets else []

    @asset(
        name=name,
        non_argument_deps=set(upstream_asset_array),
        dagster_type=Nothing,  # type: ignore
    )
    def _implementation(context: OpExecutionContext):
        asset_namespaces = create_asset_namespace_mapping(
            instance=context.instance,
            current_asset_key_str=name,
            partition_key=context.partition_key if context.has_partition_key else None,
            upstream_asset_array=upstream_asset_array,
            parent_storage_namespace=parent_storage_namespace,
            branch_storage_namespace=branch_storage_namespace,
            in_branch=in_branch(),
        )

        # imagine submitting spark job instead
        # TODO: consolidate entry points?
        # TODO: fetch input logical versions from event log so that it can pass to script
        script_path = file_relative_path(__file__, f"scripts_for_external_execution/{name}.py")
        result = subprocess.run(
            [sys.executable, script_path, json.dumps(asset_namespaces)],
            stdout=subprocess.PIPE,
            text=True,
        )

        # TODO get computed logical version out of this

        if in_branch():
            context.add_output_metadata({STORAGE_NAMESPACE_METADATA_KEY: branch_storage_namespace})
            context.log.info(f'Writing "{name}" to storage branch  "{branch_storage_namespace}"')

        print("STDOUT:\n" + result.stdout)

        assert result.returncode == 0

    return _implementation


defs = Definitions(
    jobs=[define_asset_job("the_job", selection="*")],
    assets=[
        build_asset("hackernews_source_data"),
        build_asset("hackernews_wordcloud", upstream_assets=["hackernews_source_data"]),
        build_asset("process_wordcloud", upstream_assets=["hackernews_wordcloud"]),
    ],
)

if __name__ == "__main__":
    defs.get_implicit_global_asset_job_def().execute_in_process()
