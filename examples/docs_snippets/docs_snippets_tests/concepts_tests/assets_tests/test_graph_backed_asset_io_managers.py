import pytest

from docs_snippets.concepts.assets.graph_backed_asset import defs


@pytest.mark.parametrize(
    "job",
    [
        "basic_deps_job",
        "store_slack_files",
        "second_basic_deps_job",
        "explicit_deps_job",
    ],
)
def test_jobs(job):
    job = defs.get_job_def(job)
    assert job.execute_in_process().success
