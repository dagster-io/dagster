import pytest
import responses
from dagster._core.code_pointer import CodePointer
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.reconstruct import (
    initialize_repository_def_from_pointer,
    reconstruct_repository_def_from_pointer,
)
from dagster._utils.test.definitions import definitions
from dagster_fivetran import FivetranWorkspace

from dagster_fivetran_tests.beta.conftest import TEST_ACCOUNT_ID, TEST_API_KEY, TEST_API_SECRET


@definitions
def cacheable_fivetran_workspace_data():
    workspace = FivetranWorkspace(
        account_id=TEST_ACCOUNT_ID, api_key=TEST_API_KEY, api_secret=TEST_API_SECRET
    )

    workspace.fetch_fivetran_workspace_data()

    return Definitions(
        resources={"fivetran": workspace},
    )


@pytest.mark.order("last")
def test_cacheable_fivetran_workspace_data(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    assert len(fetch_workspace_data_api_mocks.calls) == 0

    # first, we resolve the repository to generate our cached metadata
    pointer = CodePointer.from_python_file(
        __file__,
        "cacheable_fivetran_workspace_data",
        None,
    )
    init_repository_def = initialize_repository_def_from_pointer(
        pointer,
    )

    # 4 call to creates the defs
    assert len(fetch_workspace_data_api_mocks.calls) == 4

    repository_load_data = init_repository_def.repository_load_data

    # We use a separate file here just to ensure we get a fresh load
    _ = reconstruct_repository_def_from_pointer(
        pointer,
        repository_load_data,
    )

    # no additional calls after a fresh load
    assert len(fetch_workspace_data_api_mocks.calls) == 4
