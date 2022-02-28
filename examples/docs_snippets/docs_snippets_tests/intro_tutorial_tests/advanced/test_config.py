from docs_snippets.intro_tutorial.advanced.configuring_ops.configurable_job import (
    configurable_job,
)
from docs_snippets.intro_tutorial.test_util import patch_cereal_requests


@patch_cereal_requests
def test_tutorial_config_schema():
    result = configurable_job.execute_in_process(
        run_config={
            "ops": {
                "download_csv": {"config": {"url": "something"}},
            }
        },
    )

    assert result.success
