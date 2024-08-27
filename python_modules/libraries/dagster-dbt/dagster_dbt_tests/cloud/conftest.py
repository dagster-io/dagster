from typing import Any

import pytest
from dagster import build_init_resource_context
from dagster_dbt.cloud.resources import DbtCloudClientResource, dbt_cloud_resource

from dagster_dbt_tests.cloud.utils import DBT_CLOUD_ACCOUNT_ID, DBT_CLOUD_API_TOKEN


@pytest.fixture(params=["dbt_cloud_resource", "DbtCloudClientResource"])
def resource_type(request):
    return request.param


@pytest.fixture(name="dbt_cloud")
def dbt_cloud_fixture(resource_type) -> Any:
    if resource_type == "DbtCloudClientResource":
        yield DbtCloudClientResource(
            auth_token=DBT_CLOUD_API_TOKEN, account_id=DBT_CLOUD_ACCOUNT_ID
        )
    else:
        yield dbt_cloud_resource.configured(
            {
                "auth_token": DBT_CLOUD_API_TOKEN,
                "account_id": DBT_CLOUD_ACCOUNT_ID,
            }
        )


@pytest.fixture(name="get_dbt_cloud_resource")
def get_dbt_cloud_resource_fixture(resource_type) -> Any:
    if resource_type == "DbtCloudClientResource":
        return (
            lambda **kwargs: DbtCloudClientResource(
                auth_token=DBT_CLOUD_API_TOKEN, account_id=DBT_CLOUD_ACCOUNT_ID, **kwargs
            )
            .with_replaced_resource_context(build_init_resource_context())
            .get_dbt_client()
        )

    else:
        return lambda **kwargs: dbt_cloud_resource(
            build_init_resource_context(
                config={
                    "auth_token": DBT_CLOUD_API_TOKEN,
                    "account_id": DBT_CLOUD_ACCOUNT_ID,
                    **kwargs,
                }
            )
        )


@pytest.fixture(name="dbt_cloud_service")
def dbt_cloud_service_fixture(get_dbt_cloud_resource) -> Any:
    return get_dbt_cloud_resource()
