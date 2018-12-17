import os
import subprocess

from dagster import execute_pipeline

from ..part_four import define_configurable_hello_world_pipeline


def test_tutorial_part_four():
    pipeline = define_configurable_hello_world_pipeline()

    result = execute_pipeline(pipeline, {'solids': {'hello_world': {'config': 'Hello, World!'}}})

    assert result.success
    assert len(result.result_list) == 1
    assert result.result_for_solid('hello_world').transformed_value() == 'Hello, World!'
    return result
