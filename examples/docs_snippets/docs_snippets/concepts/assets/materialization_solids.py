# pylint: disable=unused-argument

from dagster import (
    AssetKey,
    AssetMaterialization,
    EventMetadataEntry,
    Output,
    OutputContext,
    OutputDefinition,
    pipeline,
    solid,
)


def read_df():
    return 1


def persist_to_storage(df):
    return "tmp"


def calculate_bytes(df):
    return 1.0


# start_materialization_solids_marker_0
@solid
def my_simple_solid(_):
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

# start_output_def_mat_solid_0


@solid(output_defs=[OutputDefinition(asset_key=AssetKey("my_dataset"))])
def my_constant_asset_solid(context):
    df = read_df()
    remote_storage_path = persist_to_storage(df)
    yield Output(remote_storage_path)


# end_output_def_mat_solid_0

# start_output_def_mat_solid_1


def get_asset_key(context: OutputContext):
    mode = context.step_context.mode_def
    return AssetKey(f"my_dataset_{mode}")


@solid(output_defs=[OutputDefinition(asset_key=get_asset_key)])
def my_variable_asset_solid(context):
    df = read_df()
    remote_storage_path = persist_to_storage(df)
    yield Output(remote_storage_path)


# end_output_def_mat_solid_1


# start_materialization_solids_marker_2
@solid
def my_metadata_materialization_solid(context):
    df = read_df()
    remote_storage_path = persist_to_storage(df)
    yield AssetMaterialization(
        asset_key="my_dataset",
        description="Persisted result to storage",
        metadata_entries=[
            EventMetadataEntry.text("Text-based metadata for this event", label="text_metadata"),
            EventMetadataEntry.fspath(remote_storage_path),
            EventMetadataEntry.url("http://mycoolsite.com/url_for_my_data", label="dashboard_url"),
            EventMetadataEntry.float(calculate_bytes(df), "size (bytes)"),
        ],
    )
    yield Output(remote_storage_path)


# end_materialization_solids_marker_2


# start_materialization_solids_marker_3
@solid
def my_asset_key_materialization_solid(context):
    df = read_df()
    remote_storage_path = persist_to_storage(df)
    yield AssetMaterialization(
        asset_key=AssetKey(["dashboard", "my_cool_site"]),
        description="Persisted result to storage",
        metadata_entries=[
            EventMetadataEntry.url("http://mycoolsite.com/dashboard", label="dashboard_url"),
            EventMetadataEntry.float(calculate_bytes(df), "size (bytes)"),
        ],
    )
    yield Output(remote_storage_path)


# end_materialization_solids_marker_3


@pipeline
def my_asset_pipeline():
    my_materialization_solid()
