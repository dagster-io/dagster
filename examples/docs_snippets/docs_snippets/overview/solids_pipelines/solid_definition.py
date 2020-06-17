# pylint: disable=unused-argument

from dagster import Int, Output, OutputDefinition, SolidDefinition, solid


@solid
def my_solid(context):
    return 1


def _return_one(_context, inputs):
    yield Output(1)


solid = SolidDefinition(
    name="my_solid", input_defs=[], output_defs=[OutputDefinition(Int)], compute_fn=_return_one,
)
