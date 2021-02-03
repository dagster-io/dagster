# pylint: disable=unused-argument

from dagster import Int, Output, OutputDefinition, SolidDefinition, solid


# start_solid_definition_marker_0
@solid
def my_solid(context):
    return 1


# end_solid_definition_marker_0

# start_solid_definition_marker_1
def _return_one(_context, inputs):
    yield Output(1)


solid = SolidDefinition(
    name="my_solid",
    input_defs=[],
    output_defs=[OutputDefinition(Int)],
    compute_fn=_return_one,
)
# end_solid_definition_marker_1
