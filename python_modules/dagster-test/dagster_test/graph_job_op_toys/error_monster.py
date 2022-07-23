from dagster import (
    Failure,
    Field,
    IOManager,
    In,
    Int,
    Out,
    ResourceDefinition,
    RetryRequested,
    String,
    graph,
    io_manager,
    op,
)
from dagster._utils import segfault
from dagster.core.definitions.executor_definition import in_process_executor


class ExampleException(Exception):
    pass


class ErrorableIOManager(IOManager):
    def __init__(self, throw_input, throw_output):
        self._values = {}
        self._throw_input = throw_input
        self._throw_output = throw_output

    def handle_output(self, context, obj):
        if self._throw_output:
            raise ExampleException("throwing up trying to handle output")

        keys = tuple(context.get_identifier())
        self._values[keys] = obj

    def load_input(self, context):
        if self._throw_input:
            raise ExampleException("throwing up trying to load input")

        keys = tuple(context.upstream_output.get_identifier())
        return self._values[keys]


@io_manager(
    config_schema={
        "throw_in_load_input": Field(bool, is_required=False, default_value=False),
        "throw_in_handle_output": Field(bool, is_required=False, default_value=False),
    }
)
def errorable_io_manager(init_context):
    return ErrorableIOManager(
        init_context.resource_config["throw_in_load_input"],
        init_context.resource_config["throw_in_handle_output"],
    )


class ErrorableResource:
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


op_throw_config = {
    "throw_in_op": Field(bool, is_required=False, default_value=False),
    "failure_in_op": Field(bool, is_required=False, default_value=False),
    "crash_in_op": Field(bool, is_required=False, default_value=False),
    "return_wrong_type": Field(bool, is_required=False, default_value=False),
    "request_retry": Field(bool, is_required=False, default_value=False),
}


def _act_on_config(op_config):
    if op_config["crash_in_op"]:
        segfault()
    if op_config["failure_in_op"]:
        try:
            raise ExampleException("sample cause exception")
        except ExampleException as e:
            raise Failure(
                description="I'm a Failure",
                metadata={
                    "metadata_label": "I am metadata text",
                },
            ) from e
    elif op_config["throw_in_op"]:
        raise ExampleException("I threw up")
    elif op_config["request_retry"]:
        raise RetryRequested()


@op(
    out=Out(Int),
    config_schema=op_throw_config,
    required_resource_keys={"errorable_resource"},
)
def emit_num(context):
    _act_on_config(context.op_config)

    if context.op_config["return_wrong_type"]:
        return "wow"

    return 13


@op(
    ins={"num": In(Int)},
    out=Out(String),
    config_schema=op_throw_config,
    required_resource_keys={"errorable_resource"},
)
def num_to_str(context, num):
    _act_on_config(context.op_config)

    if context.op_config["return_wrong_type"]:
        return num + num

    return str(num)


@op(
    ins={"string": In(str)},
    out=Out(Int),
    config_schema=op_throw_config,
    required_resource_keys={"errorable_resource"},
)
def str_to_num(context, string):
    _act_on_config(context.op_config)

    if context.op_config["return_wrong_type"]:
        return string + string

    return int(string)


@graph(
    description="Demo graph that enables configurable types of errors thrown during job execution, "
    "including op execution errors, type errors, and resource initialization errors."
)
def error_monster():
    start = emit_num.alias("start")()
    middle = num_to_str.alias("middle")(num=start)
    str_to_num.alias("end")(string=middle)


error_monster_passing_job = error_monster.to_job(
    resource_defs={
        "errorable_resource": define_errorable_resource(),
        "io_manager": errorable_io_manager,
    },
    config={
        "resources": {"errorable_resource": {"config": {"throw_on_resource_init": False}}},
        "ops": {
            "end": {"config": {"return_wrong_type": False, "throw_in_op": False}},
            "middle": {"config": {"return_wrong_type": False, "throw_in_op": False}},
            "start": {"config": {"return_wrong_type": False, "throw_in_op": False}},
        },
    },
    tags={"monster": "error"},
    executor_def=in_process_executor,
    name="error_monster_passing_job",
)

error_monster_failing_job = error_monster.to_job(
    resource_defs={
        "errorable_resource": define_errorable_resource(),
        "io_manager": errorable_io_manager,
    },
    config={
        "resources": {"errorable_resource": {"config": {"throw_on_resource_init": False}}},
        "ops": {
            "end": {"config": {"return_wrong_type": False, "throw_in_op": False}},
            "middle": {"config": {"return_wrong_type": False, "throw_in_op": True}},
            "start": {"config": {"return_wrong_type": False, "throw_in_op": False}},
        },
    },
    tags={"monster": "error"},
    executor_def=in_process_executor,
    name="error_monster_failing_job",
)


if __name__ == "__main__":
    result = error_monster.to_job(
        config={
            "ops": {
                "start": {"config": {"throw_in_op": False, "return_wrong_type": False}},
                "middle": {"config": {"throw_in_op": False, "return_wrong_type": True}},
                "end": {"config": {"throw_in_op": False, "return_wrong_type": False}},
            },
            "resources": {"errorable_resource": {"config": {"throw_on_resource_init": False}}},
        },
        tags={"monster": "error"},
        resource_defs={
            "errorable_resource": define_errorable_resource(),
            "io_manager": errorable_io_manager,
        },
    ).execute_in_process()
