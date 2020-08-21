# pylint: disable=unused-argument

from dagster import InputDefinition, Int, Nothing, Output, OutputDefinition, SolidDefinition, solid


@solid
def my_solid(context):
    return 1


def _return_one(context):
    return 1


solid = SolidDefinition(
    name="my_solid", input_defs=[], output_defs=[OutputDefinition(Int)], compute_fn=_return_one,
)


@solid
def my_logging_solid(context):
    context.log.info("Hello world")


@solid(input_defs=[InputDefinition("a", str), InputDefinition("b", int)])
def my_input_example_solid(context, a, b):
    pass


@solid(
    input_defs=[InputDefinition("a", int), InputDefinition("b", int)],
    output_defs=[OutputDefinition("sum", int), OutputDefinition("difference", int)],
)
def my_input_output_example_solid(context, a, b):
    yield Output(a + b, output_name="sum")
    yield Output(a - b, output_name="difference")


@solid(
    input_defs=[InputDefinition("a", int), InputDefinition("b", int)],
    output_defs=[OutputDefinition("result", int)],
)
def my_explicit_def_solid(context, a, b):
    yield Output(a + b, output_name="result")


@solid
def my_typehint_output_solid(context, a: int, b: int) -> int:
    yield Output(a + b)


@solid
def my_yield_solid(context):
    yield Output(1)


@solid
def return_solid(context):
    return 1


# Is equivalent to
@solid
def yield_solid(context):
    yield Output(1, "result")


# This is invalid
@solid
def incorrect_solid(context):
    yield 1


@solid(output_defs=[OutputDefinition(name="output_1"), OutputDefinition(name="output_2")])
def multiple_output_solid(context):
    yield Output(1, output_name="output_1")
    yield Output(2, output_name="output_2")


def x_solid(
    arg, name="default_name", input_defs=None, **kwargs,
):
    """
    Args:
        args (any): One or more arguments used to generate the nwe solid
        name (str): The name of the new solid.
        input_defs (list[InputDefinition]): Any input definitions for the new solid. Default: None.

    Returns:
        function: The new solid.
    """

    @solid(name=name, input_defs=input_defs or [InputDefinition("start", Nothing)], **kwargs)
    def _x_solid(context):
        # Solid logic here
        pass

    return _x_solid
