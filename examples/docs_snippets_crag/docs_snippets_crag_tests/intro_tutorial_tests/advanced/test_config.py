from dagster import execute_pipeline
from docs_snippets_crag.intro_tutorial.advanced.configuring_solids.configurable_pipeline import (
    configurable_pipeline,
)
from docs_snippets_crag.intro_tutorial.test_util import patch_cereal_requests


@patch_cereal_requests
def test_tutorial_config_schema():
    result = execute_pipeline(
        configurable_pipeline,
        run_config={
            "solids": {
                "download_csv": {"config": {"url": "something"}},
            }
        },
    )

    assert result.success
