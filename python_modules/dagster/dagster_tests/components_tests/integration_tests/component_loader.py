import importlib
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Union

import pytest
from dagster._core.definitions.definitions_class import Definitions
from dagster._utils import pushd
from dagster.components.core.tree import ComponentTree

from dagster_tests.components_tests.utils import create_project_from_components


@contextmanager
def load_test_component_defs(
    src_path: Union[str, Path], local_component_defn_to_inject: Optional[Path] = None
) -> Iterator[Definitions]:
    """Loads a component from a test component project, making the provided local component defn
    available in that component's __init__.py.
    """
    src_path = Path(src_path)
    with create_project_from_components(
        str(src_path), local_component_defn_to_inject=local_component_defn_to_inject
    ) as (_, project_name):
        tree = ComponentTree(
            defs_module=importlib.import_module(f"{project_name}.defs"),
            project_root=src_path.parent.parent,
        )
        yield tree.load_defs_at_path(Path(src_path.stem))


def sync_load_test_component_defs(
    src_path: str, local_component_defn_to_inject: Optional[Path] = None
) -> Definitions:
    with load_test_component_defs(src_path, local_component_defn_to_inject) as defs:
        return defs


@pytest.fixture(autouse=True)
def chdir():
    with pushd(str(Path(__file__).parent.parent)):
        path = str(Path(__file__).parent)
        try:
            sys.path.append(str(Path(__file__).parent))
            yield
        finally:
            sys.path.remove(path)
