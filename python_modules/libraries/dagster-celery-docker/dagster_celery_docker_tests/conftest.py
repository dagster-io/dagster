import pytest
from dagster_aws.utils import ensure_dagster_aws_tests_import

ensure_dagster_aws_tests_import()
from dagster_aws_tests.aws_credential_test_utils import get_aws_creds


@pytest.fixture
def aws_creds():
    return get_aws_creds()
