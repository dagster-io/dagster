import os
import subprocess
import warnings
from pathlib import Path

import dagster_shared
import pytest
from dagster_shared.libraries import (
    DagsterLibraryRegistry,
    check_dagster_package_version,
    core_version_from_library_version,
    library_version_from_core_version,
)

EXCLUDE_LIBRARIES = []


def test_library_registry():
    assert DagsterLibraryRegistry.get() == {
        "dagster-shared": dagster_shared.__version__,
    }


def test_non_dagster_library_registry(library_registry_fixture):
    DagsterLibraryRegistry.register("not-dagster", "0.0.1", is_dagster_package=False)

    assert DagsterLibraryRegistry.get() == {
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


@pytest.fixture
def library_registry_fixture():
    previous_libraries = DagsterLibraryRegistry.get()

    yield

    DagsterLibraryRegistry._libraries = previous_libraries  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]


def test_check_dagster_package_version(monkeypatch):
    monkeypatch.setattr(dagster_shared.version, "__version__", "0.17.0")  # type: ignore

    # Ensure no warning emitted
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        check_dagster_package_version("foo", "1.1.0")

    # Lib version matching 1.1.0-- see dagster._utils.library_version_from_core_version
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        check_dagster_package_version("foo", "0.17.0")

    with pytest.warns(Warning):  # minor version
        check_dagster_package_version("foo", "1.2.0")

    with pytest.warns(Warning):  # patch version
        check_dagster_package_version("foo", "1.1.1")

    with pytest.warns(Warning):  # minor version
        check_dagster_package_version("foo", "0.18.0")

    with pytest.warns(Warning):  # patch version
        check_dagster_package_version("foo", "0.17.1")


def test_library_version_from_core_version():
    assert library_version_from_core_version("1.1.16") == "0.17.16"
    assert library_version_from_core_version("0.17.16") == "0.17.16"
    assert library_version_from_core_version("1.1.16pre0") == "0.17.16rc0"
    assert library_version_from_core_version("1.1.16rc0") == "0.17.16rc0"
    assert library_version_from_core_version("1.1.16post0") == "0.17.16post0"


def test_core_version_from_library_version():
    assert core_version_from_library_version("0.17.16") == "1.1.16"
    assert core_version_from_library_version("1.1.16") == "1.1.16"
    assert core_version_from_library_version("0.17.16pre0") == "1.1.16rc0"
    assert core_version_from_library_version("0.17.16rc0") == "1.1.16rc0"
    assert core_version_from_library_version("0.17.16post0") == "1.1.16post0"
