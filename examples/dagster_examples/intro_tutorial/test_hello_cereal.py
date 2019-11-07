from dagster import execute_pipeline, execute_solid

from .hello_cereal import hello_cereal, hello_cereal_pipeline


def test_hello_cereal_solid():
    res = execute_solid(hello_cereal)
    assert res.success
    assert len(res.output_value()) == 77


def test_hello_cereal_pipeline():
    res = execute_pipeline(hello_cereal_pipeline)
    assert res.success
    assert len(res.result_for_solid('hello_cereal').output_value()) == 77
