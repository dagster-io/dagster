import pytest
from dagster_dlift.client import ENVIRONMENTS_SUBPATH
from dagster_dlift.gql_queries import VERIFICATION_QUERY
from dagster_dlift.test.client_fake import (
    DbtCloudClientFake,
    ExpectedAccessApiRequest,
    ExpectedDiscoveryApiRequest,
)
from dagster_dlift.translator import DbtCloudContentType

from dagster_dlift_tests.conftest import create_jaffle_shop_project, jaffle_shop_contents


def test_verification() -> None:
    """Test proper error states when we can't properly verify the instance."""
    # We get no response back from the discovery api
    fake_instance = DbtCloudClientFake(
        access_api_responses={
            ExpectedAccessApiRequest(subpath=ENVIRONMENTS_SUBPATH): {"data": [{"id": 1}]}
        },
        discovery_api_responses={
            ExpectedDiscoveryApiRequest(
                query=VERIFICATION_QUERY, variables={"environmentId": 1}
            ): {}
        },
    )

    with pytest.raises(Exception, match="Failed to verify"):
        fake_instance.verify_connections()

    # We get a response back from the discovery api, but it's not what we expect
    fake_instance = DbtCloudClientFake(
        access_api_responses={
            ExpectedAccessApiRequest(subpath=ENVIRONMENTS_SUBPATH): {"data": [{"id": 1}]}
        },
        discovery_api_responses={
            ExpectedDiscoveryApiRequest(query=VERIFICATION_QUERY, variables={"environmentId": 1}): {
                "data": {"environment": {"__typename": "NotEnvironment"}}
            }
        },
    )

    with pytest.raises(Exception, match="Failed to verify"):
        fake_instance.verify_connections()

    # Finally, we get a valid response back from the discovery api
    fake_instance = DbtCloudClientFake(
        access_api_responses={
            ExpectedAccessApiRequest(subpath=ENVIRONMENTS_SUBPATH): {"data": [{"id": 1}]}
        },
        discovery_api_responses={
            ExpectedDiscoveryApiRequest(query=VERIFICATION_QUERY, variables={"environmentId": 1}): {
                "data": {"environment": {"__typename": "Environment"}}
            }
        },
    )
    fake_instance.verify_connections()


def test_get_models() -> None:
    """Test that we can get models from the instance, even if they are paginated."""
    client = create_jaffle_shop_project()._unscoped_client  # noqa
    models = client.get_dbt_models(1)
    expected_unique_id_dep_graph = jaffle_shop_contents()[DbtCloudContentType.MODEL]
    assert len(models) == len(expected_unique_id_dep_graph)
    assert {model["uniqueId"] for model in models} == set(expected_unique_id_dep_graph.keys())
    assert {
        model["uniqueId"]: {parent["uniqueId"] for parent in model["parents"]} for model in models
    } == expected_unique_id_dep_graph


def test_get_sources() -> None:
    """Test that we can get sources from the instance, even if they are paginated."""
    client = create_jaffle_shop_project()._unscoped_client  # noqa
    sources = client.get_dbt_sources(1)
    expected_unique_id_dep_graph = jaffle_shop_contents()[DbtCloudContentType.SOURCE]
    assert len(sources) == len(expected_unique_id_dep_graph)
    assert {source["uniqueId"] for source in client.get_dbt_sources(1)} == set(
        expected_unique_id_dep_graph.keys()
    )


def test_get_tests() -> None:
    """Tests that we can get tests from the instance, even if they are paginated."""
    client = create_jaffle_shop_project()._unscoped_client  # noqa
    tests = client.get_dbt_tests(1)
    expected_unique_id_dep_graph = jaffle_shop_contents()[DbtCloudContentType.TEST]
    assert len(tests) == len(expected_unique_id_dep_graph)
    assert {source["uniqueId"] for source in client.get_dbt_tests(1)} == set(
        expected_unique_id_dep_graph.keys()
    )
