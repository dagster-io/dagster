from dagster_aws_tests.conftest import (
    fake_aws_credentials,
    mock_s3_bucket,
    mock_s3_resource,
)

from docs_snippets.concepts.io_management.io_manager_per_output import my_job


def test_io_manager_per_output(fake_aws_credentials, mock_s3_bucket):
    my_job.execute_in_process(
        run_config={
            "resources": {"s3_io": {"config": {"s3_bucket": mock_s3_bucket.name}}}
        },
    )
