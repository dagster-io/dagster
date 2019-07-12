from dagster import (
    composite_solid,
    pipeline,
    solid,
    DagsterInvariantViolationError,
    Output,
    SolidDefinition,
)
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


def nesting_composite_pipeline(depth, num_children):
    '''Creates a pipeline of nested composite solids up to "depth" layers, with a fan-out of
    num_children at each layer.

    Total number of solids will be num_children ^ depth
    '''

    @solid
    def leaf_node(_):
        return 1

    def create_wrap(inner, name):
        @composite_solid
        def wrap():
            for i in range(num_children):
                solid_alias = '%s_node_%d' % (name, i)
                inner.alias(solid_alias)()

        return wrap

    @pipeline
    def nested_pipeline():
        comp_solid = create_wrap(leaf_node, 'layer_%d' % depth)

        for i in range(depth):
            comp_solid = create_wrap(comp_solid, 'layer_%d' % (depth - (i + 1)))

        comp_solid.alias('outer')()

    return nested_pipeline
