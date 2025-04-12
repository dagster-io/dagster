import importlib
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Union

import pytest
from dagster._core.definitions.definitions_class import Definitions
from dagster._utils import pushd
from dagster.components.core.load_defs import load_defs

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
        module = importlib.import_module(f"{project_name}.defs.{src_path.stem}")

        yield load_defs(defs_root=module, project_path=src_path.parent.parent)


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
