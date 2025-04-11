from contextlib import contextmanager

import pytest
from dagster_aws.utils import ensure_dagster_aws_tests_import

ensure_dagster_aws_tests_import()
from dagster_aws_tests.aws_credential_test_utils import get_aws_creds


@pytest.fixture
def aws_env():
    aws_creds = get_aws_creds()
    return [
        f"AWS_ACCESS_KEY_ID={aws_creds['aws_access_key_id']}",
        f"AWS_SECRET_ACCESS_KEY={aws_creds['aws_secret_access_key']}",
    ]


@pytest.fixture
def docker_postgres_instance(postgres_instance):
    @contextmanager
    def _instance(overrides=None):
        with postgres_instance(overrides=overrides) as instance:
            yield instance

    return _instance
