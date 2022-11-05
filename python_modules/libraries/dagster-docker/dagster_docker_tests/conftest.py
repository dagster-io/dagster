import pytest
from dagster_aws_tests.aws_credential_test_utils import get_aws_creds


@pytest.fixture
def aws_env():
    aws_creds = get_aws_creds()
    return [
        f"AWS_ACCESS_KEY_ID={aws_creds['aws_access_key_id']}",
        f"AWS_SECRET_ACCESS_KEY={aws_creds['aws_secret_access_key']}",
    ]
