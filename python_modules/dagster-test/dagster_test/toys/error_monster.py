import six
from dagster import (
    EventMetadataEntry,
    Failure,
    Field,
    InputDefinition,
    Int,
    ModeDefinition,
    OutputDefinition,
    PresetDefinition,
    ResourceDefinition,
    RetryRequested,
    String,
    execute_pipeline,
    pipeline,
    solid,
)
from dagster.utils import segfault


class ErrorableResource(object):
    pass


def resource_init(init_context):
    if init_context.resource_config["throw_on_resource_init"]:
        raise Exception("throwing from in resource_fn")
    return ErrorableResource()


def define_errorable_resource():
    return ResourceDefinition(
        resource_fn=resource_init,
        config_schema={
            "throw_on_resource_init": Field(bool, is_required=False, default_value=False)
        },
    )


solid_throw_config = {
    "throw_in_solid": Field(bool, is_required=False, default_value=False),
    "crash_in_solid": Field(bool, is_required=False, default_value=False),
    "return_wrong_type": Field(bool, is_required=False, default_value=False),
    "request_retry": Field(bool, is_required=False, default_value=False),
}


class ExampleException(Exception):
    pass


def _act_on_config(solid_config):
    if solid_config["crash_in_solid"]:
        segfault()
    if solid_config["throw_in_solid"]:
        try:
            raise ExampleException("sample cause exception")
        except ExampleException as e:
            six.raise_from(
                Failure(
                    description="I'm a Failure",
                    metadata_entries=[
                        EventMetadataEntry.text(
                            label="metadata_label",
                            text="I am metadata text",
                            description="metadata_description",
                        )
                    ],
                ),
                e,
            )
    elif solid_config["request_retry"]:
        raise RetryRequested()


@solid(
    output_defs=[OutputDefinition(Int)],
    config_schema=solid_throw_config,
    required_resource_keys={"errorable_resource"},
)
def emit_num(context):
    _act_on_config(context.solid_config)

    if context.solid_config["return_wrong_type"]:
        return "wow"

    return 13


@solid(
    input_defs=[InputDefinition("num", Int)],
    output_defs=[OutputDefinition(String)],
    config_schema=solid_throw_config,
    required_resource_keys={"errorable_resource"},
)
def num_to_str(context, num):
    _act_on_config(context.solid_config)

    if context.solid_config["return_wrong_type"]:
        return num + num

    return str(num)


@solid(
    input_defs=[InputDefinition("string", String)],
    output_defs=[OutputDefinition(Int)],
    config_schema=solid_throw_config,
    required_resource_keys={"errorable_resource"},
)
def str_to_num(context, string):
    _act_on_config(context.solid_config)

    if context.solid_config["return_wrong_type"]:
        return string + string

    return int(string)


@pipeline(
    description=(
        "Demo pipeline that enables configurable types of errors thrown during pipeline execution, "
        "including solid execution errors, type errors, and resource initialization errors."
    ),
    mode_defs=[
        ModeDefinition(
            name="errorable_mode", resource_defs={"errorable_resource": define_errorable_resource()}
        )
    ],
    preset_defs=[
        PresetDefinition.from_pkg_resources(
            "passing",
            pkg_resource_defs=[("dagster_test.toys.environments", "error.yaml")],
            mode="errorable_mode",
        )
    ],
)
def error_monster():
    start = emit_num.alias("start")()
    middle = num_to_str.alias("middle")(num=start)
    str_to_num.alias("end")(string=middle)


if __name__ == "__main__":
    result = execute_pipeline(
        error_monster,
        {
            "solids": {
                "start": {"config": {"throw_in_solid": False, "return_wrong_type": False}},
                "middle": {"config": {"throw_in_solid": False, "return_wrong_type": True}},
                "end": {"config": {"throw_in_solid": False, "return_wrong_type": False}},
            },
            "resources": {"errorable_resource": {"config": {"throw_on_resource_init": False}}},
        },
    )
    print("Pipeline Success: ", result.success)
