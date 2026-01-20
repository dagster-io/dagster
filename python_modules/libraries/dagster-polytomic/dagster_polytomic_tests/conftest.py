import pytest
from dagster_polytomic.workspace import PolytomicWorkspace


@pytest.fixture
def polytomic_workspace() -> PolytomicWorkspace:
    return PolytomicWorkspace(api_key="test-key")
