import os

import pytest

from dagster_dlift_tests.integration_tests.conftest import (
    get_dbt_cloud_environment_id,
    get_dbt_cloud_instance,
)

IS_BUILDKITE = os.getenv("BUILDKITE") is not None

SAMPLE_GQL_QUERY = """
query ExampleQuery($environmentId: BigInt!) {
  environment(id: $environmentId) {
    dbtProjectName
  }
}
"""
GET_DBT_MODELS_QUERY = """
query ExampleQuery($environmentId: BigInt!, $types: [AncestorNodeType!]!, $first: Int) {
  environment(id: $environmentId) {
    definition {
      models(first: $first) {
        edges {
          node {
            schema
            ancestors(types: $types) {
              description
              name
              uniqueId
            }
            uniqueId
            tags
            meta
          }
        }
      }
    }
  }
}
"""


@pytest.mark.skipif(not IS_BUILDKITE, reason="Not running tests in CI yet")
def test_connection() -> None:
    instance = get_dbt_cloud_instance("test")
    instance.test_connection()


@pytest.mark.skipif(not IS_BUILDKITE, reason="Not running tests in CI yet")
def test_graphql() -> None:
    environment_id = get_dbt_cloud_environment_id()
    instance = get_dbt_cloud_instance("test")
    response = instance.query_discovery_api(SAMPLE_GQL_QUERY, {"environmentId": environment_id})
    assert response.status_code == 200
    assert response.json()["data"]["environment"]["dbtProjectName"] == "jaffle_shop"


def test_list_environments() -> None:
    instance = get_dbt_cloud_instance("test")
    ids = instance.list_environment_ids()
    assert len(ids) == 2


def test_get_dbt_models() -> None:
    instance = get_dbt_cloud_instance("test")
    for environment_id in instance.list_environment_ids():
        response = instance.query_discovery_api(
            GET_DBT_MODELS_QUERY, {"environmentId": environment_id, "types": ["Model"], "first": 1}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        for model in data["environment"]["definition"]["models"]["edges"]:
            unique_id = model["node"]["uniqueId"]
            ancestors = model["node"]["ancestors"]
