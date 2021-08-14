from dagster import execute_pipeline
from docs_snippets_crag.intro_tutorial.basics.connecting_solids.serial_pipeline import (
    serial_pipeline,
)
from docs_snippets_crag.intro_tutorial.test_util import patch_cereal_requests


@patch_cereal_requests
def test_serial_pipeline():
    result = execute_pipeline(serial_pipeline)
    assert result.success
