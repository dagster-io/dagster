# pylint: disable=unused-argument

from dagster import InputDefinition, Int, Nothing, Output, OutputDefinition, SolidDefinition, solid


@solid
def my_solid(context):
    return 1


def _return_one(context):
    return 1


solid_def = SolidDefinition(
    name="my_solid",
    input_defs=[],
    output_defs=[OutputDefinition(Int)],
    compute_fn=_return_one,
)

# my_logging_solid_start
@solid
def my_logging_solid(context):
    context.log.info("Hello world")


# my_logging_solid_end

# input_example_solid_start
@solid(
    input_defs=[
        InputDefinition(name="a", dagster_type=str),
        InputDefinition(name="b", dagster_type=int),
    ]
)
def my_input_example_solid(context, a, b):
    pass


# input_example_solid_end

# my_input_output_example_solid_start
@solid(
    input_defs=[
        InputDefinition(name="a", dagster_type=int),
        InputDefinition(name="b", dagster_type=int),
    ],
    output_defs=[
        OutputDefinition(name="sum", dagster_type=int),
        OutputDefinition(name="difference", dagster_type=int),
    ],
)
def my_input_output_example_solid(context, a, b):
    yield Output(a + b, output_name="sum")
    yield Output(a - b, output_name="difference")


# my_input_output_example_solid_end


@solid(
    input_defs=[
        InputDefinition(name="a", dagster_type=int),
        InputDefinition(name="b", dagster_type=int),
    ],
    output_defs=[OutputDefinition(name="result", dagster_type=int)],
)
def my_explicit_def_solid(context, a, b):
    yield Output(a + b, output_name="result")


@solid
def my_typehint_output_solid(context, a: int, b: int) -> int:
    yield Output(a + b)


# my_yield_solid_start
@solid
def my_yield_solid(context):
    yield Output(1)


# my_yield_solid_end

# return_and_yield_start
@solid
def return_solid(context):
    return 1


# Is equivalent to
@solid
def yield_solid(context):
    yield Output(1, "result")


# return_and_yield_end


# incorrect_solid_start
# This is invalid
@solid
def incorrect_solid(context):
    yield 1


# incorrect_solid_end

# multi_output_solid_start
@solid(output_defs=[OutputDefinition(name="output_1"), OutputDefinition(name="output_2")])
def multiple_output_solid(context):
    yield Output(1, output_name="output_1")
    yield Output(2, output_name="output_2")


# multi_output_solid_end


# x_solid_start
def x_solid(
    arg,
    name="default_name",
    input_defs=None,
    **kwargs,
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


# x_solid_end
