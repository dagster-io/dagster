import sys
from pathlib import Path

import pytest
from dagster._core.definitions.definitions_class import Definitions
from dagster._utils import pushd

from dagster_components_tests.integration_tests.component_loader import load_test_component_defs


@pytest.fixture(autouse=True)
def chdir():
    with pushd(str(Path(__file__).parent.parent)):
        sys.path.append(str(Path(__file__).parent))
        yield


def test_hello_world() -> None:
    defs = load_test_component_defs("iwritesqlbutnotdbt/helloworld")
    assert isinstance(defs, Definitions)
