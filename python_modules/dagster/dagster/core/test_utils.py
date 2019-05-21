from dagster import (
    DagsterEvaluateConfigValueError,
    DagsterInvariantViolationError,
    Result,
    SolidDefinition,
)

from dagster.core.types.evaluator import evaluate_config_value


def single_output_transform(name, inputs, compute_fn, output, description=None):
    '''It is commmon to want a Solid that has only inputs, a single output (with the default
    name), and no config. So this is a helper function to do that. This compute function
    must return the naked return value (as opposed to a Result object).

    Args:
        name (str): Name of the solid.
        inputs (List[InputDefinition]): Inputs of solid.
        compute_fn (callable):
            Callable with the signature
            (context: ExecutionContext, inputs: Dict[str, Any]) : Any
        output (OutputDefinition): Output of the solid.
        description (str): Descripion of the solid.

    Returns:
        SolidDefinition:

    Example:

        .. code-block:: python

            single_output_transform(
                'add_one',
                inputs=InputDefinition('num', types.Int),
                output=OutputDefinition(types.Int),
                compute_fn=lambda context, inputs: inputs['num'] + 1
            )

    '''

    def _new_compute_fn(context, inputs):
        value = compute_fn(context, inputs)
        if isinstance(value, Result):
            raise DagsterInvariantViolationError(
                '''Single output compute Solid {name} returned a Result. Just return
                value directly without wrapping it in Result'''
            )
        yield Result(value=value)

    return SolidDefinition(
        name=name,
        inputs=inputs,
        compute_fn=_new_compute_fn,
        outputs=[output],
        description=description,
    )


# This is a legacy API from when the config parsing only returned a single
# error. Existing test logic was written assuming structure to this is still
# around to avoid having to port all the unit tests.
def throwing_evaluate_config_value(config_type, config_value):
    result = evaluate_config_value(config_type, config_value)
    if not result.success:
        raise DagsterEvaluateConfigValueError(result.errors[0].stack, result.errors[0].message)
    return result.value
