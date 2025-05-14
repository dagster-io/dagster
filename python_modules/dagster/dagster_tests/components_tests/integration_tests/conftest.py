import pytest

from dagster_tests.components_tests.integration_tests.component_loader import (
    load_test_component_defs,
)


@pytest.fixture
def defs(request):
    component_path = request.param
    with load_test_component_defs(component_path) as defs:
        yield defs
