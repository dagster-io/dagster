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
from dagster._config.structured_config import ResourceDependency, StructuredConfigIOManagerBase
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.storage.branching.branching_io_manager import (
    BranchingIOManager as _BranchingIOManager,
)
from dagster._core.storage.fs_io_manager import PickledObjectFilesystemIOManager
from dagster._core.storage.io_manager import IOManager

from .hackernews import extract, transform


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


class BranchingIOManager(StructuredConfigIOManagerBase):
    parent_io_manager: ResourceDependency[IOManager]
    branch_io_manager: ResourceDependency[IOManager]
    branch_name: str = "dev"
    branch_metadata_key: str = "io_manager_branch"

    def create_io_manager_to_pass_to_user_code(self, context) -> IOManager:
        return _BranchingIOManager(
            parent_io_manager=self.parent_io_manager,
            branch_io_manager=self.branch_io_manager,
            branch_name=self.branch_name,
            branch_metadata_key=self.branch_metadata_key,
        )


prod_io_manager = PickledObjectFilesystemIOManager(base_dir="prod_storage")

if is_prod():
    io_manager = prod_io_manager
else:
    branch_name = get_branch_name()
    branch_io_manager = PickledObjectFilesystemIOManager(base_dir=f"{branch_name}_storage")

    io_manager = BranchingIOManager(
        parent_io_manager=prod_io_manager,
        branch_io_manager=branch_io_manager,
        branch_name=branch_name,
    )


dev_defs = Definitions(
    assets=[hackernews_source_data, hackernews_wordcloud, process_wordcloud],
    jobs=[] if is_prod() else [ship_asset_materializations],
    resources={"io_manager": io_manager},
)
