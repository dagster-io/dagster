from dagster import execute_pipeline

from ..repo import example_pipeline


def test_config_mapping():
    res = execute_pipeline(example_pipeline)
    assert res.success
    assert res.result_for_solid("hello_external").output_value() == "Hello, Sam!"

    res = execute_pipeline(
        example_pipeline, run_config={"solids": {"hello_external": {"config": {"name": "Bob"}}}}
    )
    assert res.success
    assert res.result_for_solid("hello_external").output_value() == "Hello, Bob!"
