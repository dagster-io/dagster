import os
from contextlib import contextmanager

from dagster import (
    DagsterInvariantViolationError,
    Output,
    SolidDefinition,
    composite_solid,
    pipeline,
    solid,
)


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

    Examples:

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


def nesting_composite_pipeline(depth, num_children, *args, **kwargs):
    '''Creates a pipeline of nested composite solids up to "depth" layers, with a fan-out of
    num_children at each layer.

    Total number of solids will be num_children ^ depth
    '''

    @solid
    def leaf_node(_):
        return 1

    def create_wrap(inner, name):
        @composite_solid(name=name)
        def wrap():
            for i in range(num_children):
                solid_alias = '%s_node_%d' % (name, i)
                inner.alias(solid_alias)()

        return wrap

    @pipeline(*args, **kwargs)
    def nested_pipeline():
        comp_solid = create_wrap(leaf_node, 'layer_%d' % depth)

        for i in range(depth):
            comp_solid = create_wrap(comp_solid, 'layer_%d' % (depth - (i + 1)))

        comp_solid.alias('outer')()

    return nested_pipeline


@contextmanager
def environ(env):
    """Temporarily set environment variables inside the context manager and
    fully restore previous environment afterwards
    """
    previous_values = {key: os.getenv(key) for key in env}
    os.environ.update(env)
    try:
        yield
    finally:
        for key, value in previous_values.items():
            if value is None:
                del os.environ[key]
            else:
                os.environ[key] = value
