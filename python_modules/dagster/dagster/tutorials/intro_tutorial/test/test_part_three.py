import os
import subprocess

from dagster import execute_pipeline

from ..part_three import define_diamond_dag_pipeline


def test_tutorial_part_three():
    pipeline = define_diamond_dag_pipeline()

    result = execute_pipeline(pipeline)

    assert result.success
    assert len(result.result_list) == 4
    assert result.result_for_solid('solid_a').transformed_value() == 1
    assert result.result_for_solid('solid_b').transformed_value() == 2
    assert result.result_for_solid('solid_c').transformed_value() == 3
    assert result.result_for_solid('solid_d').transformed_value() == 6
    return result
