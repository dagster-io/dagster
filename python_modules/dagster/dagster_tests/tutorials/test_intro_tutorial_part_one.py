# pylint: disable=W0622,W0614,W0401
from dagster import *


def test_tutorial_part_one():
    pipeline = PipelineDefinition(solids=[hello_world])

    result = execute_pipeline(pipeline)

    assert result.success
    assert len(result.result_list) == 1
    assert result.result_for_solid('hello_world').transformed_value() is None
    return result


@lambda_solid
def hello_world():
    print('hello')


if __name__ == '__main__':
    test_tutorial_part_one()
