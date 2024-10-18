import os

import pytest
from dagster_dlift.instance import DbtCloudInstance

from dagster_dlift_tests.integration_tests.conftest import (
    get_dbt_cloud_account_id,
    get_dbt_cloud_account_prefix,
    get_dbt_cloud_personal_token,
    get_dbt_cloud_region,
)

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


@pytest.mark.skipif(not IS_BUILDKITE, reason="Not running tests in CI yet")
def test_connection() -> None:
    instance = DbtCloudInstance(
        account_id=get_dbt_cloud_account_id(),
        personal_token=get_dbt_cloud_personal_token(),
        account_prefix=get_dbt_cloud_account_prefix(),
        region=get_dbt_cloud_region(),
        name="test",
    )
    instance.test_connection()
