# pylint: disable=unused-argument, no-value-for-parameter

# start_marker
import random

from dagster import InputDefinition, Output, OutputDefinition, pipeline, solid


@solid(
    output_defs=[
        OutputDefinition(int, "branch_1", is_required=False),
        OutputDefinition(int, "branch_2", is_required=False),
    ]
)
def branching_solid(_):
    num = random.randint(0, 1)
    if num == 0:
        yield Output(1, "branch_1")
    else:
        yield Output(2, "branch_2")


@solid(input_defs=[InputDefinition("_input", int)])
def branch_1_solid(_, _input):
    pass


@solid(input_defs=[InputDefinition("_input", int)])
def branch_2_solid(_, _input):
    pass


@pipeline
def branching_pipeline():
    branch_1, branch_2 = branching_solid()
    branch_1_solid(branch_1)
    branch_2_solid(branch_2)


# end_marker
