from dagster import execute_pipeline
from docs_snippets.intro_tutorial.basics.connecting_solids.complex_pipeline import complex_pipeline
from docs_snippets.intro_tutorial.test_util import patch_cereal_requests


@patch_cereal_requests
def test_complex_pipeline():
    result = execute_pipeline(complex_pipeline)
    assert result.success
