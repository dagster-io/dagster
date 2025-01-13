import contextlib
import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

from dagster._core.definitions.definitions_class import Definitions

from dagster_components_tests.integration_tests.component_loader import (
    build_defs_from_component_path,
    load_test_component_project_context,
)
from dagster_components_tests.utils import generate_component_lib_pyproject_toml


@contextlib.contextmanager
def inject_component(path: str, component_to_inject: Path) -> Generator[str, None, None]:
    origin_path = Path(__file__).parent.parent / "components" / path

    with tempfile.TemporaryDirectory() as tmpdir:
        shutil.copytree(origin_path, tmpdir, dirs_exist_ok=True)
        shutil.copy(component_to_inject, Path(tmpdir) / "__init__.py")

        yield tmpdir


@contextlib.contextmanager
def create_code_location_from_component(
    path: str, component_to_inject: Path
) -> Generator[Path, None, None]:
    origin_path = Path(__file__).parent.parent / "components" / path

    with tempfile.TemporaryDirectory() as tmpdir:
        code_location_dir = Path(tmpdir) / "my_location"
        code_location_dir.mkdir()
        with open(code_location_dir / "pyproject.toml", "w") as f:
            f.write(generate_component_lib_pyproject_toml("my_location", is_code_location=True))

        components_dir = code_location_dir / "my_location" / "components" / "my_component"
        components_dir.mkdir(parents=True, exist_ok=True)

        shutil.copytree(origin_path, components_dir, dirs_exist_ok=True)
        shutil.copy(component_to_inject, Path(components_dir) / "__init__.py")

        # print representation of tmpdir and all its contents, including subdirectories
        print(tmpdir)
        print("\n".join(list(repr(p) for p in Path(tmpdir).rglob("*"))))

        yield code_location_dir


def load_test_component_defs_inject_component(path: str, component_to_inject: Path) -> Definitions:
    with inject_component(path=path, component_to_inject=component_to_inject) as tmpdir:
        context = load_test_component_project_context()
        return build_defs_from_component_path(
            path=Path(tmpdir),
            registry=context.component_registry,
            resources={},
        )
