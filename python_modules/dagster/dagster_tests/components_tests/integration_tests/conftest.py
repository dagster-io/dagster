import pytest
from dagster.components.component.component import ComponentRequirements

from dagster_tests.components_tests.integration_tests.component_loader import (
    load_test_component_defs,
    load_test_component_requirements,
)


@pytest.fixture
def defs(request):
    component_path = request.param
    with load_test_component_defs(component_path) as defs:
        yield defs


@pytest.fixture
def requirements(request) -> ComponentRequirements:
    component_path = request.param
    return load_test_component_requirements(component_path)
