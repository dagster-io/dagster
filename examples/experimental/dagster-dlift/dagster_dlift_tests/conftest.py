from collections.abc import Mapping
from typing import AbstractSet, Any, Optional  # noqa: UP035

from dagster_dlift.gql_queries import (
    GET_DBT_MODELS_QUERY,
    GET_DBT_SOURCES_QUERY,
    GET_DBT_TESTS_QUERY,
)
from dagster_dlift.project import DbtCloudCredentials
from dagster_dlift.test.client_fake import (
    DbtCloudClientFake,
    ExpectedAccessApiRequest,
    ExpectedDiscoveryApiRequest,
    build_response_for_type,
)
from dagster_dlift.test.project_fake import DbtCloudProjectEnvironmentFake
from dagster_dlift.translator import DbtCloudContentType
from dagster_dlift.utils import get_job_name


def query_per_content_type(content_type: DbtCloudContentType) -> str:
    return {
        DbtCloudContentType.MODEL: GET_DBT_MODELS_QUERY,
        DbtCloudContentType.SOURCE: GET_DBT_SOURCES_QUERY,
        DbtCloudContentType.TEST: GET_DBT_TESTS_QUERY,
    }[content_type]


def build_expected_requests(
    dep_graph_per_type: Mapping[DbtCloudContentType, Mapping[str, Optional[AbstractSet[str]]]],
) -> Mapping[ExpectedDiscoveryApiRequest, Any]:
    return {
        ExpectedDiscoveryApiRequest(
            query=query_per_content_type(content_type),
            variables={"environmentId": 1, "first": 100, "after": idx if idx > 0 else None},
        ): build_response_for_type(
            content_type=content_type,
            unique_id=unique_id,
            parents=parents,
            has_next_page=True if idx < len(dep_graph) - 1 else False,
            start_cursor=idx,
        )
        for content_type, dep_graph in dep_graph_per_type.items()
        for idx, (unique_id, parents) in enumerate(dep_graph.items())
    }


def jaffle_shop_contents() -> (
    Mapping[DbtCloudContentType, Mapping[str, Optional[AbstractSet[str]]]]
):
    return {
        DbtCloudContentType.MODEL: {
            "model.jaffle_shop.customers": {
                "model.jaffle_shop.stg_customers",
                "model.jaffle_shop.stg_orders",
            },
            "model.jaffle_shop.stg_customers": set(),
            "model.jaffle_shop.stg_orders": set(),
        },
        DbtCloudContentType.SOURCE: {
            "source.jaffle_shop.jaffle_shop.customers": None,
            "source.jaffle_shop.jaffle_shop.orders": None,
        },
        DbtCloudContentType.TEST: {
            "test.jaffle_shop.customers": {"model.jaffle_shop.stg_customers"},
            "test.jaffle_shop.orders": {"model.jaffle_shop.stg_orders"},
        },
    }


def build_dagster_job_response(environment_id: int, project_id: int) -> Mapping[str, Any]:
    return {"name": get_job_name(environment_id, project_id), "id": 1}


def build_expected_access_api_requests() -> Mapping[ExpectedAccessApiRequest, Any]:
    return {
        # List of jobs
        ExpectedAccessApiRequest(
            "/jobs/", params={"environment_id": 1, "limit": 100, "offset": 0}
        ): {"data": [build_dagster_job_response(1, 1)]}
    }


def create_seeded_jaffle_shop_client() -> DbtCloudClientFake:
    return DbtCloudClientFake(
        access_api_responses=build_expected_access_api_requests(),
        discovery_api_responses=build_expected_requests(dep_graph_per_type=jaffle_shop_contents()),
    )


def create_jaffle_shop_project() -> DbtCloudProjectEnvironmentFake:
    """Create a fake jaffle shop-style project."""
    return DbtCloudProjectEnvironmentFake(
        client=create_seeded_jaffle_shop_client(),
        environment_id=1,
        project_id=1,
        credentials=DbtCloudCredentials(
            account_id=123, token="fake", access_url="fake", discovery_api_url="fake"
        ),
    )
