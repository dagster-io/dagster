# pylint: disable=unused-argument

from dagster import Failure, InputDefinition, Output, OutputDefinition, pipeline, solid

conditional = True


@solid(output_defs=[OutputDefinition(int, "a", is_required=False)])
def my_solid(context):
    if conditional:
        yield Output(1, "a")


@solid(
    output_defs=[
        OutputDefinition(int, "a", is_required=False),
        OutputDefinition(int, "b", is_required=False),
    ]
)
def branching_solid(context):
    if conditional:
        yield Output(1, "a")
    else:
        yield Output(2, "b")


@solid(input_defs=[InputDefinition("inp", int)])
def path_1(context, inp):
    pass


@solid(input_defs=[InputDefinition("inp", int)])
def path_2(context, inp):
    pass


@pipeline
def my_pipeline():
    a, b = my_solid()
    path_1(a)
    path_2(b)


def do_dangerous_thing():
    raise Exception("my_exception")


class MyException(Exception):
    pass


@solid
def exception_handling_solid(context):
    try:
        do_dangerous_thing()
    except MyException as e:
        raise Failure("Failure description", metadata_entries=[...]) from e
        # Or in Python 2
        # six.raise_from(Failure("Failure description"), metadata_entries=[...], e)
