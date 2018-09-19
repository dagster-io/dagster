from dagster import (
    DagsterInvariantViolationError,
    ExecutionContext,
    PipelineDefinition,
    PipelineContextDefinition,
    Result,
    SolidDefinition,
    check,
    config,
    execute_pipeline,
)


def execute_single_solid(context, solid_def, environment=None, throw_on_error=True):
    check.inst_param(context, 'context', ExecutionContext)
    check.inst_param(solid_def, 'solid_def', SolidDefinition)
    environment = check.opt_inst_param(
        environment,
        'environment',
        config.Environment,
        config.Environment(),
    )
    check.bool_param(throw_on_error, 'throw_on_error')

    single_solid_environment = config.Environment(
        expectations=environment.expectations,
        context=environment.context,
        solids={solid_def.name: environment.solids[solid_def.name]}
        if solid_def.name in environment.solids else None
    )

    pipeline_result = execute_pipeline(
        PipelineDefinition(
            solids=[solid_def],
            context_definitions=PipelineContextDefinition.passthrough_context_definition(context),
        ),
        environment=single_solid_environment,
    )

    return pipeline_result


def single_output_transform(name, inputs, transform_fn, output, description=None):
    '''It is commmon to want a Solid that has only inputs, a single output (with the default
    name), and no config. So this is a helper function to do that. This transform function
    must return the naked return value (as opposed to a Result object).

    Args:
        name (str): Name of the solid.
        inputs (List[InputDefinition]): Inputs of solid.
        transform_fn (callable):
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
                transform_fn=lambda context, inputs: inputs['num'] + 1
            )

    '''

    def _new_transform_fn(info, inputs):
        value = transform_fn(info.context, inputs)
        if isinstance(value, Result):
            raise DagsterInvariantViolationError(
                '''Single output transform Solid {name} returned a Result. Just return
                value directly without wrapping it in Result'''
            )
        yield Result(value=value)

    return SolidDefinition(
        name=name,
        inputs=inputs,
        transform_fn=_new_transform_fn,
        outputs=[output],
        description=description,
    )
