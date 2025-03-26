import os
import subprocess
from pathlib import Path

import dagster
import dagster_shared
import pytest
from dagster_shared.libraries import DagsterLibraryRegistry

EXCLUDE_LIBRARIES = []


def test_library_registry():
    assert DagsterLibraryRegistry.get() == {
        "dagster": dagster.__version__,
        "dagster-shared": dagster_shared.__version__,
    }


def test_non_dagster_library_registry(library_registry_fixture):
    DagsterLibraryRegistry.register("not-dagster", "0.0.1", is_dagster_package=False)

    assert DagsterLibraryRegistry.get() == {
        "dagster": dagster.version.__version__,
        "dagster-shared": dagster_shared.__version__,
        "not-dagster": "0.0.1",
    }


def test_all_libraries_register() -> None:
    # attempt to ensure all libraries in the repository register with DagsterLibraryRegistry
    register_call = "DagsterLibraryRegistry.register"

    library_dir = Path(__file__).parents[3] / "libraries"
    assert str(library_dir).endswith("python_modules/libraries")

    for library in os.listdir(library_dir):
        if (
            library in EXCLUDE_LIBRARIES
            or library.startswith(".")
            or library.endswith("CONTRIBUTING.md")
        ):
            continue
        result = subprocess.run(["grep", register_call, (library_dir / library), "-r"], check=False)
        assert (
            result.returncode == 0
        ), f"Dagster library {library} is missing call to {register_call}."


def test_legacy_import_still_works():
    from dagster._core.libraries import DagsterLibraryRegistry  # noqa


@pytest.fixture
def library_registry_fixture():
    previous_libraries = DagsterLibraryRegistry.get()

    yield

    DagsterLibraryRegistry._libraries = previous_libraries  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]
