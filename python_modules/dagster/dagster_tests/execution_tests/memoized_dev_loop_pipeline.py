from dagster import Field, In, Out, String, job, op, repository
from dagster._core.storage.memoizable_io_manager import versioned_filesystem_io_manager
from dagster._legacy import ModeDefinition, pipeline


@op(
    version="create_string_version",
    config_schema={"input_str": Field(String)},
    out={"created_string": Out(io_manager_key="io_manager", metadata={})},
)
def create_string_1_asset(context):
    return context.op_config["input_str"]


@op(
    ins={"_string_input": In(String)},
    version="take_string_version",
    config_schema={"input_str": Field(String)},
    out={"taken_string": Out(io_manager_key="io_manager", metadata={})},
)
def take_string_1_asset(context, _string_input):
    return context.op_config["input_str"] + _string_input


@pipeline(
    mode_defs=[
        ModeDefinition("only_mode", resource_defs={"io_manager": versioned_filesystem_io_manager})
    ],
)
def asset_pipeline():
    return take_string_1_asset(create_string_1_asset())


# op + job version


@op(
    version="create_string_version",
    config_schema={"input_str": Field(String)},
)
def create_string_1_asset_op(context):
    return context.op_config["input_str"]


@op(
    version="take_string_version",
    config_schema={"input_str": Field(String)},
)
def take_string_1_asset_op(context, _string_input):
    return context.op_config["input_str"] + _string_input


@job
def asset_job():
    take_string_1_asset_op(create_string_1_asset_op())


@repository
def memoized_dev_repo():
    return [asset_pipeline, asset_job]
