from dagster import (
    Field,
    InputDefinition,
    ModeDefinition,
    OutputDefinition,
    String,
    pipeline,
    repository,
    solid,
)
from dagster.core.storage.asset_store import versioned_filesystem_asset_store


@solid(
    version="create_string_version",
    config_schema={"input_str": Field(String)},
    output_defs=[
        OutputDefinition(name="created_string", asset_store_key="object_manager", asset_metadata={})
    ],
)
def create_string_1_asset(context):
    return context.solid_config["input_str"]


@solid(
    input_defs=[InputDefinition("_string_input", String)],
    version="take_string_version",
    config_schema={"input_str": Field(String)},
    output_defs=[
        OutputDefinition(name="taken_string", asset_store_key="object_manager", asset_metadata={})
    ],
)
def take_string_1_asset(context, _string_input):
    return context.solid_config["input_str"] + _string_input


@pipeline(
    mode_defs=[
        ModeDefinition(
            "only_mode", resource_defs={"object_manager": versioned_filesystem_asset_store}
        )
    ]
)
def asset_pipeline():
    return take_string_1_asset(create_string_1_asset())


@repository
def memoized_dev_repo():
    return [asset_pipeline]
