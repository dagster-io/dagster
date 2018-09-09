# pylint: disable=W0622,W0614,W0401
from dagster import *


@solid
def solid_one(context, _conf):
    context.info('Something you should know about occurred.')


@solid
def solid_two(context, _conf):
    context.error('An error occurred.')


def test_tutorial_part_five_sample_one():
    pipeline_result = execute_pipeline(PipelineDefinition(solids=[solid_one, solid_two]))

    assert pipeline_result.success
    return pipeline_result


def test_tutorial_part_five_sample_two():
    pipeline_result = execute_pipeline(
        PipelineDefinition(name='part_five', solids=[solid_one, solid_two])
    )

    assert pipeline_result.success
    return pipeline_result


def test_tutorial_part_five_sample_three():
    pipeline_result = execute_pipeline(
        PipelineDefinition(name='part_five', solids=[solid_one, solid_two]),
        config.Environment(context=config.Context(config={'log_level': 'DEBUG'}))
    )

    assert pipeline_result.success
    return pipeline_result


if __name__ == '__main__':
    # test_tutorial_part_five_sample_one()
    # test_tutorial_part_five_sample_two()
    test_tutorial_part_five_sample_three()
