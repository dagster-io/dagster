from dagster import execute_pipeline
from docs_snippets.intro_tutorial.basics.single_solid_pipeline.hello_cereal import (
    hello_cereal_pipeline,
)
from docs_snippets.intro_tutorial.test_util import patch_cereal_requests


@patch_cereal_requests
def test_tutorial_intro_tutorial_hello_world():
    result = execute_pipeline(hello_cereal_pipeline)
    assert result.success
