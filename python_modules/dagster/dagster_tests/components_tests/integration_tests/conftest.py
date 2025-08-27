from collections.abc import Iterator

import pytest
from dagster.components.core.component_tree import ComponentTree

from dagster_tests.components_tests.integration_tests.component_loader import (
    construct_component_tree_for_test,
)


@pytest.fixture
def component_tree(request: pytest.FixtureRequest) -> Iterator[ComponentTree]:
    component_path = request.param
    with construct_component_tree_for_test(component_path) as tree:
        yield tree
