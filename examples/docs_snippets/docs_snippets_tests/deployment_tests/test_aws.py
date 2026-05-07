from dagster import JobDefinition
from docs_snippets.deployment.oss.deployment_options.aws.io_manager import my_job


def test_aws_job():
    assert isinstance(my_job, JobDefinition)
