import os

import pytest
from dagster_dlift.instance import DbtCloudInstance

from dagster_dlift_tests.integration_tests.conftest import (
    get_dbt_cloud_account_id,
    get_dbt_cloud_account_prefix,
    get_dbt_cloud_environment_id,
    get_dbt_cloud_personal_token,
    get_dbt_cloud_region,
)

IS_BUILDKITE = os.getenv("BUILDKITE") is not None

SAMPLE_GQL_QUERY = """
query ExampleQuery($environmentId: BigInt!) {
  environment(id: $environmentId) {
    dbtProjectName
  }
}
"""


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


def test_graphql() -> None:
    environment_id = get_dbt_cloud_environment_id()
    instance = DbtCloudInstance(
        account_id=get_dbt_cloud_account_id(),
        personal_token=get_dbt_cloud_personal_token(),
        account_prefix=get_dbt_cloud_account_prefix(),
        region=get_dbt_cloud_region(),
        name="test",
    )
    response = instance.query_discovery_api(SAMPLE_GQL_QUERY, {"environmentId": environment_id})
    assert response.status_code == 200
    assert response.json()["data"]["environment"]["dbtProjectName"] == "jaffle_shop"
