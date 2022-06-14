# isort: skip_file
# pylint: disable=unused-argument,reimported


def read_df():
    return 1


def read_df_for_date(_):
    return 1


def persist_to_storage(df):
    return "tmp"


def calculate_bytes(df):
    return 1.0


# start_materialization_ops_marker_0
from dagster import op


@op
def my_simple_op():
    df = read_df()
    remote_storage_path = persist_to_storage(df)
    return remote_storage_path


# end_materialization_ops_marker_0

# start_materialization_ops_marker_1
from dagster import AssetMaterialization, op


@op
def my_materialization_op(context):
    df = read_df()
    remote_storage_path = persist_to_storage(df)
    context.log_event(
        AssetMaterialization(
            asset_key="my_dataset", description="Persisted result to storage"
        )
    )
    return remote_storage_path


# end_materialization_ops_marker_1


# start_partitioned_asset_materialization
from dagster import op, AssetMaterialization


@op(config_schema={"date": str})
def my_partitioned_asset_op(context):
    partition_date = context.op_config["date"]
    df = read_df_for_date(partition_date)
    remote_storage_path = persist_to_storage(df)
    context.log_event(
        AssetMaterialization(asset_key="my_dataset", partition=partition_date)
    )
    return remote_storage_path


# end_partitioned_asset_materialization


# start_materialization_ops_marker_2
from dagster import op, AssetMaterialization, MetadataValue


@op
def my_metadata_materialization_op(context):
    df = read_df()
    remote_storage_path = persist_to_storage(df)
    context.log_event(
        AssetMaterialization(
            asset_key="my_dataset",
            description="Persisted result to storage",
            metadata={
                "text_metadata": "Text-based metadata for this event",
                "path": MetadataValue.path(remote_storage_path),
                "dashboard_url": MetadataValue.url(
                    "http://mycoolsite.com/url_for_my_data"
                ),
                "size (bytes)": calculate_bytes(df),
            },
        )
    )
    return remote_storage_path


# end_materialization_ops_marker_2


# start_materialization_ops_marker_3
from dagster import op, AssetKey, AssetMaterialization, job, Output


@op
def my_asset_key_materialization_op(context):
    df = read_df()
    remote_storage_path = persist_to_storage(df)
    yield AssetMaterialization(
        asset_key=AssetKey(["dashboard", "my_cool_site"]),
        description="Persisted result to storage",
        metadata={
            "dashboard_url": MetadataValue.url("http://mycoolsite.com/dashboard"),
            "size (bytes)": calculate_bytes(df),
        },
    )
    yield Output(remote_storage_path)


# end_materialization_ops_marker_3


@job
def my_asset_job():
    my_materialization_op()
