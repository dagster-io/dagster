from dagster import execute_pipeline

from ..part_one import define_hello_world_pipeline


def test_tutorial_part_one():
    pipeline = define_hello_world_pipeline()

    result = execute_pipeline(pipeline)

    assert result.success
    assert len(result.result_list) == 1
    assert result.result_for_solid('hello_world').transformed_value() == 'hello'
    return result


if __name__ == '__main__':
    test_tutorial_part_one()
