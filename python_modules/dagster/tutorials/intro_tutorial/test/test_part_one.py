import os
import subprocess

from dagster import execute_pipeline

from ..part_one import define_hello_world_pipeline


def test_tutorial_part_one():
    pipeline = define_hello_world_pipeline()

    result = execute_pipeline(pipeline)

    assert result.success
    assert len(result.result_list) == 1
    assert result.result_for_solid('hello_world').transformed_value() == 'hello'
    return result


def test_tutorial_part_one_script():
    subprocess.check_output(
        [
            'python',
            os.path.normpath(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '../part_one.py')
            )
        ]
    )
