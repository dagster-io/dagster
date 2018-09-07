from dagster import (
    ExecutionContext,
    PipelineDefinition,
    PipelineContextDefinition,
    SolidDefinition,
    check,
    config,
    execute_pipeline,
)


def execute_single_solid(context, solid, environment, throw_on_error=True):
    check.inst_param(context, 'context', ExecutionContext)
    check.inst_param(solid, 'solid', SolidDefinition)
    check.inst_param(environment, 'environment', config.Environment)
    check.bool_param(throw_on_error, 'throw_on_error')

    single_solid_environment = config.Environment(
        expectations=environment.expectations,
        context=environment.context,
        solids={solid.name: environment.solids[solid.name]}
        if solid.name in environment.solids else None
    )

    pipeline_result = execute_pipeline(
        PipelineDefinition(
            solids=[solid],
            context_definitions=PipelineContextDefinition.passthrough_context_definition(context),
        ),
        environment=single_solid_environment,
    )

    return pipeline_result
