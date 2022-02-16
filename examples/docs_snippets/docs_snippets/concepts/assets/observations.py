"""isort:skip_file"""
# pylint: disable=unused-argument,reimported
import os
import pandas as pd
from dagster import asset, build_assets_job, IOManager, AssetKey, DailyPartitionsDefinition


def read_df():
    return range(372)


def read_df_for_date(_):
    return 1


def persist_to_storage(df):
    return "tmp"


def calculate_bytes(df):
    return 1.0


# start_observation_asset_marker_0
from dagster import AssetObservation


@asset
def observation_asset():
    df = read_df()
    remote_storage_path = persist_to_storage(df)
    yield AssetObservation(asset_key=AssetKey("observation_asset"), metadata={"num_rows": len(df)})
    yield Output(5)


# end_observation_asset_marker_0

# start_partitioned_asset_observation
from dagster import op, AssetMaterialization, Output


@asset(partitions_def=DailyPartitionsDefinition(start_date="2022-02-15"))
def my_partitioned_dataset(context):
    partition_date = context.partition_key
    df = read_df_for_date(partition_date)
    remote_storage_path = persist_to_storage(df)
    yield AssetMaterialization(asset_key="my_partitioned_dataset", partition=partition_date)
    yield AssetObservation(asset_key="my_partitioned_dataset", partition=partition_date)
    yield Output(remote_storage_path)


# end_partitioned_asset_observation


# start_observation_asset_marker_2
from dagster import asset, AssetObservation, Output, EventMetadata


@asset
def my_dataset():
    df = read_df()
    remote_storage_path = persist_to_storage(df)
    yield AssetObservation(
        asset_key="my_dataset",
        metadata={
            "text_metadata": "Text-based metadata for this event",
            "path": EventMetadata.path(remote_storage_path),
            "dashboard_url": EventMetadata.url("http://mycoolsite.com/url_for_my_data"),
            "size (bytes)": calculate_bytes(df),
        },
    )
    yield Output(remote_storage_path)


# end_observation_asset_marker_2


asset_observation_job = build_assets_job("asset_observation_job", [observation_asset])
metadata_observation_job = build_assets_job("metadata_observation_job", [my_dataset])
partitioned_observation_job = build_assets_job(
    "partitioned_observation_job", [my_partitioned_dataset]
)
