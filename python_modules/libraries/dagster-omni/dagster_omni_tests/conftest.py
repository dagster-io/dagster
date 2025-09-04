import pytest
from dagster_omni.component import OmniComponent
from dagster_omni.workspace import OmniWorkspace


@pytest.fixture
def omni_workspace() -> OmniWorkspace:
    return OmniWorkspace(base_url="https://test.omniapp.co", api_key="test-key")


@pytest.fixture
def component(omni_workspace: OmniWorkspace) -> OmniComponent:
    return OmniComponent(workspace=omni_workspace)
