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
from dagster.core.storage.memoizable_io_manager import versioned_filesystem_io_manager
from dagster.core.storage.tags import MEMOIZED_RUN_TAG


@solid(
    version="create_string_version",
    config_schema={"input_str": Field(String)},
    output_defs=[OutputDefinition(name="created_string", io_manager_key="io_manager", metadata={})],
)
def create_string_1_asset(context):
    return context.solid_config["input_str"]


@solid(
    input_defs=[InputDefinition("_string_input", String)],
    version="take_string_version",
    config_schema={"input_str": Field(String)},
    output_defs=[OutputDefinition(name="taken_string", io_manager_key="io_manager", metadata={})],
)
def take_string_1_asset(context, _string_input):
    return context.solid_config["input_str"] + _string_input


@pipeline(
    mode_defs=[
        ModeDefinition("only_mode", resource_defs={"io_manager": versioned_filesystem_io_manager})
    ],
    tags={MEMOIZED_RUN_TAG: "true"},
)
def asset_pipeline():
    return take_string_1_asset(create_string_1_asset())


@repository
def memoized_dev_repo():
    return [asset_pipeline]
