import os

from dagster import Field, InputDefinition, ModeDefinition, Output, String, pipeline, solid
from dagster.core.storage.system_storage import fs_intermediate_storage


@solid(
    version="create_string_version",
    config_schema={"input_str": Field(String), "base_dir": Field(String)},
)
def create_string_1(context):
    yield Output(
        context.solid_config["input_str"],
        address=os.path.join(
            context.solid_config["base_dir"], "intermediates/create_string_1.compute/result"
        ),
    )


@solid(
    version="create_string_version_2",
    config_schema={"input_str": Field(String), "base_dir": Field(String)},
)
def create_string_2(context):
    yield Output(
        context.solid_config["input_str"],
        address=os.path.join(
            context.solid_config["base_dir"], "intermediates/create_string_2.compute/result"
        ),
    )


@solid(
    input_defs=[InputDefinition("_string_input", String)],
    version="take_string_version",
    config_schema={"input_str": Field(String), "base_dir": Field(String)},
)
def take_string_1(context, _string_input):
    yield Output(
        context.solid_config["input_str"],
        address=os.path.join(
            context.solid_config["base_dir"], "intermediates/take_string_1.compute/result"
        ),
    )


@solid(
    input_defs=[InputDefinition("_string_input", String)],
    version="take_string_version_2",
    config_schema={"input_str": Field(String), "base_dir": Field(String)},
)
def take_string_2(context, _string_input):
    yield Output(
        context.solid_config["input_str"],
        address=os.path.join(
            context.solid_config["base_dir"], "intermediates/take_string_2.compute/result"
        ),
    )


@solid(
    input_defs=[
        InputDefinition("_string_input_1", String),
        InputDefinition("_string_input_2", String),
    ],
    version="take_string_two_inputs_version",
    config_schema={"input_str": Field(String), "base_dir": Field(String)},
)
def take_string_two_inputs(context, _string_input_1, _string_input_2):
    yield Output(
        context.solid_config["input_str"],
        address=os.path.join(
            context.solid_config["base_dir"], "intermediates/take_string_two_inputs.compute/result"
        ),
    )


@pipeline(
    mode_defs=[ModeDefinition("only_mode", intermediate_storage_defs=[fs_intermediate_storage])]
)
def basic_pipeline():
    take_string_two_inputs(
        _string_input_1=take_string_1(create_string_1()),
        _string_input_2=take_string_2(create_string_2()),
    )
