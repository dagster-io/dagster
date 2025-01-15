import contextlib
import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path

from dagster._core.definitions.definitions_class import Definitions

from dagster_components_tests.integration_tests.component_loader import (
    build_defs_from_component_path,
    load_test_component_project_context,
)
from dagster_components_tests.utils import generate_component_lib_pyproject_toml


def _setup_component_in_folder(
    src_path: str, dst_path: str, local_component_defn_to_inject: Path
) -> None:
    origin_path = Path(__file__).parent.parent / "components" / src_path

    shutil.copytree(origin_path, dst_path, dirs_exist_ok=True)
    shutil.copy(local_component_defn_to_inject, Path(dst_path) / "__init__.py")


@contextlib.contextmanager
def inject_component(src_path: str, local_component_defn_to_inject: Path) -> Iterator[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        _setup_component_in_folder(src_path, tmpdir, local_component_defn_to_inject)
        yield tmpdir


@contextlib.contextmanager
def create_code_location_from_components(
    *src_paths: str, local_component_defn_to_inject: Path
) -> Iterator[Path]:
    """Scaffolds a code location with the given components in a temporary directory,
    injecting the provided local component defn into each component's __init__.py.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        code_location_dir = Path(tmpdir) / "my_location"
        code_location_dir.mkdir()
        with open(code_location_dir / "pyproject.toml", "w") as f:
            f.write(generate_component_lib_pyproject_toml("my_location", is_code_location=True))

        for src_path in src_paths:
            component_name = src_path.split("/")[-1]

            components_dir = code_location_dir / "my_location" / "components" / component_name
            components_dir.mkdir(parents=True, exist_ok=True)

            _setup_component_in_folder(
                src_path=src_path,
                dst_path=str(components_dir),
                local_component_defn_to_inject=local_component_defn_to_inject,
            )

        yield code_location_dir


def load_test_component_defs_inject_component(
    src_path: str, local_component_defn_to_inject: Path
) -> Definitions:
    """Loads a component from a test component project, making the provided local component defn
    available in that component's __init__.py.
    """
    with inject_component(
        src_path=src_path, local_component_defn_to_inject=local_component_defn_to_inject
    ) as tmpdir:
        context = load_test_component_project_context()
        return build_defs_from_component_path(
            path=Path(tmpdir),
            registry=context.component_registry,
            resources={},
        )
