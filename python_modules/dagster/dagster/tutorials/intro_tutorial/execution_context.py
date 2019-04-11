from dagster import PipelineDefinition, execute_pipeline, solid


@solid
def debug_message(context):
    context.log.debug('A debug message.')
    return 'foo'


@solid
def error_message(context):
    context.log.error('An error occurred.')


def define_execution_context_pipeline_step_one():
    return PipelineDefinition(solids=[debug_message, error_message])


def define_execution_context_pipeline_step_two():
    return PipelineDefinition(
        name='execution_context_pipeline', solids=[debug_message, error_message]
    )


def define_execution_context_pipeline_step_three():
    return PipelineDefinition(
        name='execution_context_pipeline', solids=[debug_message, error_message]
    )


if __name__ == '__main__':
    execute_pipeline(
        define_execution_context_pipeline_step_three(),
        {'context': {'default': {'config': {'log_level': 'DEBUG'}}}},
    )
