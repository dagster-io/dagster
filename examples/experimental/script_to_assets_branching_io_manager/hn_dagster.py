import os

import pandas
from dagster import (
    AssetKey,
    AssetMaterialization,
    DagsterInstance,
    Definitions,
    OpExecutionContext,
    Output,
    asset,
    file_relative_path,
    job,
    op,
)
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.storage.branching.branching_io_manager import BranchingIOManager
from dagster._core.storage.fs_io_manager import PickledObjectFilesystemIOManager
from hackernews import extract, transform


@op
def replicate_asset_materializations_for_group(context: OpExecutionContext):
    assets_to_ship = ["hackernews_source_data", "hackernews_wordcloud", "process_wordcloud"]

    prod_instance = DagsterInstance.from_config(file_relative_path(__file__, "prod_dagster_home/"))

    for asset_key_str in assets_to_ship:
        asset_key = AssetKey(asset_key_str)
        context.log.info(
            f"About to call get_latest_materialization_event on {asset_key} in prod instance."
        )
        latest_event_log_entry = prod_instance.get_latest_materialization_event(asset_key)
        if latest_event_log_entry:
            asset_mat = latest_event_log_entry.asset_materialization
            if asset_mat:
                context.log.info(
                    f"Inserting {latest_event_log_entry} into dev with metadata"
                    f" {asset_mat.metadata}"
                )
                parent_run_id = latest_event_log_entry.run_id
                parent_run_url = f"http://127.0.0.1:3000/runs/{parent_run_id}"
                yield AssetMaterialization(
                    asset_key=asset_key_str,
                    description=asset_mat.description,
                    metadata={
                        **asset_mat.metadata,
                        **{
                            "parent_asset_catalog_url": MetadataValue.url(
                                f"http://127.0.0.1:3000/assets/{asset_key_str}"
                            ),
                            "parent_run_id": parent_run_id,
                            "parent_run_url": MetadataValue.url(parent_run_url),
                            "parent_timestamp": latest_event_log_entry.timestamp,
                        },
                    },
                    # metadata_entries=asset_mat.metadata_entries,
                    partition=asset_mat.partition,
                    tags=asset_mat.tags,
                )
        else:
            context.log.info(f"Did not find entry in catalog for {asset_key_str} in prod instance.")

    yield Output(value=None)


@job
def ship_asset_materializations():
    replicate_asset_materializations_for_group()


@asset
def hackernews_source_data():
    return extract()


@asset
def hackernews_wordcloud(hackernews_source_data: pandas.DataFrame):
    return transform(hackernews_source_data)


@asset
def process_wordcloud(hackernews_wordcloud):
    # do something
    return hackernews_wordcloud


def is_prod():
    return os.getenv("DAGSTER_DEPLOYMENT") == "prod"


DEFAULT_BRANCH_NAME = "dev"


def get_branch_name():
    assert not is_prod()
    return os.getenv("DAGSTER_DEPLOYMENT", DEFAULT_BRANCH_NAME)


def construct_branching_io_manager(get_prod_io_manager, get_branch_io_manager):
    if is_prod():
        return get_prod_io_manager()

    branch_name = get_branch_name()

    prod_io_manager = get_prod_io_manager()

    return BranchingIOManager(
        parent_io_manager=prod_io_manager,
        branch_io_manager=get_branch_io_manager(branch_name),
        branch_name=branch_name,
    )


def get_prod_io_manager():
    return PickledObjectFilesystemIOManager(base_dir="prod_storage")


def get_branch_io_manager(branch_name: str):
    branch_storage_folder = f"{branch_name}_storage"
    return PickledObjectFilesystemIOManager(base_dir=branch_storage_folder)


dev_defs = Definitions(
    assets=[hackernews_source_data, hackernews_wordcloud, process_wordcloud],
    jobs=[] if is_prod() else [ship_asset_materializations],
    resources={
        "io_manager": construct_branching_io_manager(get_prod_io_manager, get_branch_io_manager)
    },
)
