# pylint: disable=W0622,W0614,W0401

from dagster import (
    PipelineDefinition,
    execute_pipeline,
    solid,
)


@solid
def solid_one(info):
    info.context.info('Something you should know about occurred.')


@solid
def solid_two(info):
    info.context.error('An error occurred.')


def define_step_one_pipeline():
    return PipelineDefinition(name='part_five_step_one_pipeline', solids=[solid_one, solid_two])


def test_tutorial_part_five_sample_one():
    pipeline_result = execute_pipeline(define_step_one_pipeline())

    assert pipeline_result.success
    return pipeline_result


def define_step_two_pipeline():
    return PipelineDefinition(name='part_five_step_two_pipeline', solids=[solid_one, solid_two])


def test_tutorial_part_five_sample_two():
    pipeline_result = execute_pipeline(define_step_two_pipeline())

    assert pipeline_result.success
    return pipeline_result


def define_step_three_pipeline():
    return PipelineDefinition(name='part_five_step_three_pipeline', solids=[solid_one, solid_two])


def test_tutorial_part_five_sample_three():
    pipeline_result = execute_pipeline(
        define_step_two_pipeline(),
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

    assert pipeline_result.success
    return pipeline_result


if __name__ == '__main__':
    # test_tutorial_part_five_sample_one()
    # test_tutorial_part_five_sample_two()
    test_tutorial_part_five_sample_three()
