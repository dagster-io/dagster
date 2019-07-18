from dagster import Any, Output, OutputDefinition, SolidDefinition, execute_solid


def invoke_compute(table_def, inputs, mode_def=None):
    '''
    Invoke the core computation defined on a table directly.
    '''

    def _compute_fn(context, _):
        yield Output(table_def.lakehouse_fn(context, **inputs))

    return execute_solid(
        SolidDefinition(
            name='wrap_lakehouse_fn_solid',
            input_defs=[],
            output_defs=[OutputDefinition(Any)],
            compute_fn=_compute_fn,
        ),
        mode_def=mode_def,
    )
