import importlib
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

import dagster as dg
import pytest
from dagster._utils import pushd
from dagster.components.core.component_tree import ComponentTree, LegacyAutoloadingComponentTree

from dagster_tests.components_tests.utils import create_project_from_components


@contextmanager
def load_test_component_defs(
    src_path: str | Path, local_component_defn_to_inject: Optional[Path] = None
) -> Iterator[dg.Definitions]:
    """Loads a component from a test component project, making the provided local component defn
    available in that component's __init__.py.
    """
    src_path = Path(src_path)
    with construct_component_tree_for_test(src_path, local_component_defn_to_inject) as tree:
        yield tree.build_defs(Path(src_path.stem))


@contextmanager
def construct_component_tree_for_test(
    src_path: str | Path, local_component_defn_to_inject: Optional[Path] = None
) -> Iterator[ComponentTree]:
    """Loads a component from a test component project, making the provided local component defn
    available in that component's __init__.py.
    """
    src_path = Path(src_path)
    with create_project_from_components(
        str(src_path), local_component_defn_to_inject=local_component_defn_to_inject
    ) as (_, project_name):
        yield LegacyAutoloadingComponentTree.from_module(
            defs_module=importlib.import_module(f"{project_name}.defs"),
            project_root=src_path.parent.parent,
        )


def sync_load_test_component_defs(
    src_path: str, local_component_defn_to_inject: Optional[Path] = None
) -> dg.Definitions:
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
