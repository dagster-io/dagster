from dagster import (
    check,
    ExpectationDefinition,
    InputDefinition,
    MaterializationDefinition,
    OutputDefinition,
    SourceDefinition,
)

# This is a collection point for older APIs that should no longer be "public"
# but still used in unit tests because I don't want to rewrite them all


def create_custom_source_input(
    name,
    source_fn,
    *,
    argument_def_dict=None,
    depends_on=None,
    expectations=None,
    source_type='CUSTOM'
):
    '''
    This function exist and is used a lot because separation of inputs and sources used to not
    exist so most of the unit tests in the systems were written without tha abstraction. So
    this exists as a bridge from the old api to the new api.
    '''
    return InputDefinition(
        name=name,
        sources=[
            SourceDefinition(
                source_type=source_type,
                source_fn=source_fn,
                argument_def_dict=argument_def_dict,
            )
        ],
        depends_on=depends_on,
        expectations=check.opt_list_param(
            expectations, 'expectations', of_type=ExpectationDefinition
        )
    )

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
