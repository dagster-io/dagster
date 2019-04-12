from dagster import (
    DagsterEvaluateConfigValueError,
    DagsterInvariantViolationError,
    ExecutionContext,
    InProcessExecutorConfig,
    PipelineDefinition,
    PipelineContextDefinition,
    Result,
    RunConfig,
    SolidDefinition,
    check,
    execute_pipeline,
)

from dagster.core.types.evaluator import evaluate_config_value


def execute_single_solid_in_isolation(
    context_params, solid_def, environment=None, raise_on_error=True
):
    '''
    Deprecated.

    Execute a solid outside the context of a pipeline, with an already-created context.

    Prefer execute_solid in dagster.utils.test
    '''
    check.inst_param(context_params, 'context_params', ExecutionContext)
    check.inst_param(solid_def, 'solid_def', SolidDefinition)
    environment = check.opt_dict_param(environment, 'environment')
    check.bool_param(raise_on_error, 'raise_on_error')

    single_solid_environment = {
        'expectations': environment.get('expectations'),
        'context': environment.get('context'),
        'solids': {solid_def.name: environment['solids'][solid_def.name]}
        if solid_def.name in environment.get('solids', {})
        else None,
    }

    pipeline_result = execute_pipeline(
        PipelineDefinition(
            solids=[solid_def],
            context_definitions=PipelineContextDefinition.passthrough_context_definition(
                context_params
            ),
        ),
        environment_dict=single_solid_environment,
        run_config=RunConfig(
            executor_config=InProcessExecutorConfig(raise_on_error=raise_on_error)
        ),
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

    def _new_transform_fn(context, inputs):
        value = transform_fn(context, inputs)
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


# This is a legacy API from when the config parsing only returned a single
# error. Existing test logic was written assuming structure to this is still
# around to avoid having to port all the unit tests.
def throwing_evaluate_config_value(config_type, config_value):
    result = evaluate_config_value(config_type, config_value)
    if not result.success:
        raise DagsterEvaluateConfigValueError(result.errors[0].stack, result.errors[0].message)
    return result.value
