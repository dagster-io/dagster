"""isort:skip_file"""
# pylint: disable=unused-argument,reimported
from dagster import op, job, IOManager


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


@op
def observation_op():
    df = read_df()
    remote_storage_path = persist_to_storage(df)
    yield AssetObservation(asset_key="observation_asset", metadata={"num_rows": len(df)})
    yield AssetMaterialization(
        asset_key="observation_asset", description="Persisted result to storage"
    )
    yield Output(5)


# end_observation_asset_marker_0

# start_partitioned_asset_observation
from dagster import op, AssetMaterialization, Output


@op(config_schema={"date": str})
def partitioned_dataset_op(context):
    partition_date = context.op_config["date"]
    df = read_df_for_date(partition_date)
    remote_storage_path = persist_to_storage(df)
    yield AssetObservation(asset_key="my_partitioned_dataset", partition=partition_date)
    yield AssetMaterialization(asset_key="my_partitioned_dataset", partition=partition_date)
    yield Output(remote_storage_path)


# end_partitioned_asset_observation


# start_observation_asset_marker_2
from dagster import op, AssetObservation, Output, EventMetadata


@op
def observes_dataset_op():
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
    yield AssetMaterialization(asset_key="my_dataset")
    yield Output(remote_storage_path)


# end_observation_asset_marker_2


@job
def my_job():
    observation_op()
