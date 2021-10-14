from tempfile import TemporaryDirectory

from docs_snippets_crag.concepts.io_management.io_manager_per_output import my_job

from dagster_aws_tests.conftest import mock_s3_bucket, mock_s3_resource


def test_io_manager_per_output(mock_s3_bucket):
    my_job.execute_in_process(
        run_config={"resources": {"s3_io": {"config": {"s3_bucket": mock_s3_bucket.name}}}},
    )
