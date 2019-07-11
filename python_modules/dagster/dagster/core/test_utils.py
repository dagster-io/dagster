from dagster import DagsterInvariantViolationError, Output, SolidDefinition
from dagster.core.types.evaluator import evaluate_config
from dagster.core.types.evaluator.errors import DagsterEvaluateConfigValueError


def single_output_solid(name, input_defs, compute_fn, output_def, description=None):
    '''It is commmon to want a Solid that has only inputs, a single output (with the default
    name), and no config. So this is a helper function to do that. This compute function
    must return the naked return value (as opposed to a Output object).

    Args:
        name (str): Name of the solid.
        input_defs (List[InputDefinition]): Inputs of solid.
        compute_fn (callable):
            Callable with the signature
            (context: ExecutionContext, inputs: Dict[str, Any]) : Any
        output_def (OutputDefinition): Output of the solid.
        description (str): Descripion of the solid.

    Returns:
        SolidDefinition:

    Example:

        .. code-block:: python

            single_output_compute(
                'add_one',
                input_defs=InputDefinition('num', types.Int),
                output_def=OutputDefinition(types.Int),
                compute_fn=lambda context, inputs: inputs['num'] + 1
            )

    '''

    def _new_compute_fn(context, input_defs):
        value = compute_fn(context, input_defs)
        if isinstance(value, Output):
            raise DagsterInvariantViolationError(
                '''Single output compute Solid {name} returned a Output. Just return
                value directly without wrapping it in Output'''
            )
        yield Output(value=value)

    return SolidDefinition(
        name=name,
        input_defs=input_defs,
        compute_fn=_new_compute_fn,
        output_defs=[output_def],
        description=description,
    )


# This is a legacy API from when the config parsing only returned a single
# error. Existing test logic was written assuming structure to this is still
# around to avoid having to port all the unit tests.
def throwing_evaluate_config_value(config_type, config_value):
    result = evaluate_config(config_type, config_value)
    if not result.success:
        raise DagsterEvaluateConfigValueError(result.errors[0].stack, result.errors[0].message)
    return result.value
