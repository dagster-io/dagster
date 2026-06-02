from dagster import JobDefinition
from docs_snippets.deployment.oss.deployment_options.gcp.gcp_job import gcs_job


def test_gcs_job():
    assert isinstance(gcs_job, JobDefinition)
