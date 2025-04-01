import pytest
import responses
from dagster._core.code_pointer import CodePointer
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.reconstruct import (
    initialize_repository_def_from_pointer,
    reconstruct_repository_def_from_pointer,
)
from dagster._utils.test.definitions import lazy_definitions
from dagster_dbt.cloud_v2.resources import DbtCloudCredentials, DbtCloudWorkspace

from dagster_dbt_tests.cloud_v2.conftest import (
    TEST_ACCESS_URL,
    TEST_ACCOUNT_ID,
    TEST_ENVIRONMENT_ID,
    TEST_PROJECT_ID,
    TEST_TOKEN,
)


@lazy_definitions
def cacheable_dbt_cloud_workspace_data():
    workspace = DbtCloudWorkspace(
        credentials=DbtCloudCredentials(
            account_id=TEST_ACCOUNT_ID,
            access_url=TEST_ACCESS_URL,
            token=TEST_TOKEN,
        ),
        project_id=TEST_PROJECT_ID,
        environment_id=TEST_ENVIRONMENT_ID,
    )

    workspace.fetch_workspace_data()

    return Definitions(
        resources={"dbt_cloud": workspace},
    )


@pytest.mark.order("last")
def test_cacheable_dbt_cloud_workspace_data(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    assert len(fetch_workspace_data_api_mocks.calls) == 0

    # first, we resolve the repository to generate our cached metadata
    pointer = CodePointer.from_python_file(
        __file__,
        "cacheable_dbt_cloud_workspace_data",
        None,
    )
    init_repository_def = initialize_repository_def_from_pointer(
        pointer,
    )

    # 7 call to creates the defs
    assert len(fetch_workspace_data_api_mocks.calls) == 7

    repository_load_data = init_repository_def.repository_load_data

    # We use a separate file here just to ensure we get a fresh load
    _ = reconstruct_repository_def_from_pointer(
        pointer,
        repository_load_data,
    )

    # no additional calls after a fresh load
    assert len(fetch_workspace_data_api_mocks.calls) == 7
