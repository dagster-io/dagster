from dagster import (
    PipelineDefinition,
    execute_pipeline,
    solid,
)


@solid
def solid_one(info):
    info.context.debug('A debug message.')
    return 'foo'


@solid
def solid_two(info):
    info.context.error('An error occurred.')
    raise Exception()


def define_execution_context_pipeline_step_one():
    return PipelineDefinition(solids=[solid_one, solid_two])


def define_execution_context_pipeline_step_two():
    return PipelineDefinition(name='part_five_pipeline', solids=[solid_one, solid_two])


def define_execution_context_pipeline_step_three():
    return PipelineDefinition(name='part_five_pipeline', solids=[solid_one, solid_two])


if __name__ == '__main__':
    execute_pipeline(
        define_execution_context_pipeline_step_three(),
        {
            'context': {
                'default': {
                    'config': {
                        'log_level': 'DEBUG',
                    },
                },
            },
        },
    )
