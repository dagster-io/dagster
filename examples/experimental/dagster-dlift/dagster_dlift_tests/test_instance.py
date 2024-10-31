import pytest
from dagster_dlift.cloud_instance import ENVIRONMENTS_SUBPATH
from dagster_dlift.gql_queries import (
    GET_DBT_MODELS_QUERY,
    GET_DBT_SOURCES_QUERY,
    VERIFICATION_QUERY,
)
from dagster_dlift.test.instance_fake import (
    DbtCloudInstanceFake,
    ExpectedAccessApiRequest,
    ExpectedDiscoveryApiRequest,
    build_model_response,
    build_source_response,
)


def test_verification() -> None:
    """Test proper error states when we can't properly verify the instance."""
    # We get no response back from the discovery api
    fake_instance = DbtCloudInstanceFake(
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
    fake_instance = DbtCloudInstanceFake(
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
    fake_instance = DbtCloudInstanceFake(
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
    expected_unique_id_dep_graph = {
        "model.jaffle_shop.customers": {
            "model.jaffle_shop.stg_customers",
            "model.jaffle_shop.stg_orders",
        },
        "model.jaffle_shop.stg_customers": set(),
        "model.jaffle_shop.stg_orders": set(),
    }
    fake_instance = DbtCloudInstanceFake(
        access_api_responses={},
        discovery_api_responses={
            ExpectedDiscoveryApiRequest(
                query=GET_DBT_MODELS_QUERY,
                variables={"environmentId": 1, "first": 100, "after": idx if idx > 0 else None},
            ): build_model_response(
                unique_id=unique_id,
                parents=parents,
                has_next_page=True if idx < len(expected_unique_id_dep_graph) - 1 else False,
                start_cursor=idx,
            )
            for idx, (unique_id, parents) in enumerate(expected_unique_id_dep_graph.items())
        },
    )
    models = fake_instance.get_dbt_models(1)
    assert len(models) == len(expected_unique_id_dep_graph)
    assert {model["uniqueId"] for model in models} == set(expected_unique_id_dep_graph.keys())
    assert {
        model["uniqueId"]: {parent["uniqueId"] for parent in model["parents"]} for model in models
    } == expected_unique_id_dep_graph


def test_get_sources() -> None:
    """Test that we can get sources from the instance, even if they are paginated."""
    expected_unique_id_sources = {
        "source.jaffle_shop.jaffle_shop.customers",
        "source.jaffle_shop.jaffle_shop.orders",
    }

    fake_instance = DbtCloudInstanceFake(
        access_api_responses={},
        discovery_api_responses={
            ExpectedDiscoveryApiRequest(
                query=GET_DBT_SOURCES_QUERY,
                variables={"environmentId": 1, "first": 100, "after": idx if idx > 0 else None},
            ): build_source_response(
                unique_id=unique_id,
                has_next_page=True if idx < len(expected_unique_id_sources) - 1 else False,
                start_cursor=idx,
            )
            for idx, unique_id in enumerate(expected_unique_id_sources)
        },
    )
    assert {
        source["uniqueId"] for source in fake_instance.get_dbt_sources(1)
    } == expected_unique_id_sources
