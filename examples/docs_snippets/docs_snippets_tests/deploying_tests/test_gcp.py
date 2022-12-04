from docs_snippets.deploying.gcp.gcp_job import gcs_job

from dagster import JobDefinition


def test_gcs_job():
    assert isinstance(gcs_job, JobDefinition)
