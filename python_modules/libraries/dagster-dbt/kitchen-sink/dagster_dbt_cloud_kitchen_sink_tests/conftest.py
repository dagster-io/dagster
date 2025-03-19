import pytest
from dagster_dbt.cloud_v2.resources import DbtCloudWorkspace
from dagster_dbt_cloud_kitchen_sink.resources import (
    get_dbt_cloud_workspace,
    get_environment_id,
    get_project_id,
)


@pytest.fixture
def workspace() -> DbtCloudWorkspace:
    return get_dbt_cloud_workspace()


@pytest.fixture
def project_id() -> int:
    return get_project_id()


@pytest.fixture
def environment_id() -> int:
    return get_environment_id()
