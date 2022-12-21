from dagster import JobDefinition
from docs_snippets.deploying.aws.io_manager import my_job


def test_aws_job():
    assert isinstance(my_job, JobDefinition)
