# pylint: disable=unused-argument

from dagster import (
    AssetKey,
    AssetMaterialization,
    EventMetadata,
    Output,
    OutputContext,
    OutputDefinition,
    pipeline,
    solid,
)


def read_df():
    return 1


def read_df_for_date(_):
    return 1


def persist_to_storage(df):
    return "tmp"


def calculate_bytes(df):
    return 1.0


# start_materialization_solids_marker_0
@solid
def my_simple_solid():
    df = read_df()
    remote_storage_path = persist_to_storage(df)
    return remote_storage_path


# end_materialization_solids_marker_0

# start_materialization_solids_marker_1
@solid
def my_materialization_solid(context):
    df = read_df()
    remote_storage_path = persist_to_storage(df)
    yield AssetMaterialization(asset_key="my_dataset", description="Persisted result to storage")
    yield Output(remote_storage_path)


# end_materialization_solids_marker_1

# start_simple_asset_solid


@solid
def my_asset_solid(context):
    df = read_df()
    persist_to_storage(df)
    yield AssetMaterialization(asset_key="my_dataset")
    yield Output(df)


# end_simple_asset_solid

# start_output_def_mat_solid_0


@solid(output_defs=[OutputDefinition(asset_key=AssetKey("my_dataset"))])
def my_constant_asset_solid(context):
    df = read_df()
    persist_to_storage(df)
    yield Output(df)


# end_output_def_mat_solid_0

# start_output_def_mat_solid_1


def get_asset_key(context: OutputContext):
    mode = context.step_context.mode_def.name
    return AssetKey(f"my_dataset_{mode}")


@solid(output_defs=[OutputDefinition(asset_key=get_asset_key)])
def my_variable_asset_solid(context):
    df = read_df()
    persist_to_storage(df)
    yield Output(df)


# end_output_def_mat_solid_1

# start_partitioned_asset_materialization


@solid(config_schema={"date": str})
def my_partitioned_asset_solid(context):
    partition_date = context.solid_config["date"]
    df = read_df_for_date(partition_date)
    remote_storage_path = persist_to_storage(df)
    yield AssetMaterialization(asset_key="my_dataset", partition=partition_date)
    yield Output(remote_storage_path)


# end_partitioned_asset_materialization


# start_materialization_ops_marker_2
@op
def my_metadata_materialization_op(context):
    df = read_df()
    remote_storage_path = persist_to_storage(df)
    yield AssetMaterialization(
        asset_key="my_dataset",
        description="Persisted result to storage",
        metadata={
            "text_metadata": "Text-based metadata for this event",
            "path": EventMetadata.path(remote_storage_path),
            "dashboard_url": EventMetadata.url("http://mycoolsite.com/url_for_my_data"),
            "size (bytes)": calculate_bytes(df),
        },
    )
    yield Output(remote_storage_path)


# end_materialization_ops_marker_2


# start_materialization_solids_marker_3
@solid
def my_asset_key_materialization_solid(context):
    df = read_df()
    remote_storage_path = persist_to_storage(df)
    yield AssetMaterialization(
        asset_key=AssetKey(["dashboard", "my_cool_site"]),
        description="Persisted result to storage",
        metadata={
            "dashboard_url": EventMetadata.url("http://mycoolsite.com/dashboard"),
            "size (bytes)": calculate_bytes(df),
        },
    )
    yield Output(remote_storage_path)


# end_materialization_solids_marker_3


@pipeline
def my_asset_pipeline():
    my_materialization_solid()
