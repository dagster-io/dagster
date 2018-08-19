from dagster import (
    check,
    ExpectationDefinition,
    InputDefinition,
    MaterializationDefinition,
    OutputDefinition,
)

# This is a collection point for older APIs that should no longer be "public"
# but still used in unit tests because I don't want to rewrite them all


def create_single_materialization_output(
    name, materialization_fn, argument_def_dict, expectations=None
):
    '''
    Similar to create_single_source_input this exists because a move in the primitive APIs.
    Materializations and outputs used to not be separate concepts so this is a compatability
    layer with the old api. Once the *new* api stabilizes this should be removed but it stays
    for now.
    '''
    return OutputDefinition(
        materializations=[
            MaterializationDefinition(
                name=name,
                materialization_fn=materialization_fn,
                argument_def_dict=argument_def_dict,
            )
        ],
        expectations=expectations
    )
