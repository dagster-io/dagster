import pytest

from dagster import file_relative_path


@pytest.fixture
def docs_snippets_folder():
    return file_relative_path(__file__, "../docs_snippets/")


@pytest.fixture
def mock_s3_bucket(mock_s3_resource):
    yield mock_s3_resource.create_bucket(Bucket="test-bucket")
