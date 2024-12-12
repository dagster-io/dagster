import os
import subprocess
from pathlib import Path

# Some libraries are excluded because they either:
# - lack a Dagster dependency, which is a prerequisite for registering in the DagsterLibraryRegistry.
# - are temporary or on a separate release schedule from the rest of the libraries.
EXCLUDE_LIBRARIES = ["dagster-components", "dagster-dg"]


def test_all_libraries_register() -> None:
    # attempt to ensure all libraries in the repository register with DagsterLibraryRegistry
    register_call = "DagsterLibraryRegistry.register"

    library_dir = Path(__file__).parents[2] / "libraries"
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
