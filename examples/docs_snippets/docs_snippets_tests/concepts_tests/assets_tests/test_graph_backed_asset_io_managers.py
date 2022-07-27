import pytest

from docs_snippets.concepts.assets.graph_backed_asset import my_repo


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
    job = my_repo.get_job(job)
    assert job.execute_in_process().success
