from docs_snippets.deploying.gcp import gcp_job
from dagster import JobDefinition


def test_gcp_job():
    assert isinstance(gcp_job, JobDefinition)
