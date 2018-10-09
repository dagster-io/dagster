from dagster import (
    PipelineDefinition,
    execute_pipeline,
    lambda_solid,
)


def test_tutorial_part_one():
    pipeline = define_pipeline()

    result = execute_pipeline(pipeline)

    assert result.success
    assert len(result.result_list) == 1
    assert result.result_for_solid('hello_world').transformed_value() is None
    return result


def define_pipeline():
    return PipelineDefinition(name='part_one_pipeline', solids=[hello_world])


@lambda_solid
def hello_world():
    print('hello')


if __name__ == '__main__':
    test_tutorial_part_one()
