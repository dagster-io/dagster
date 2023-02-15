import os
import subprocess
from pathlib import Path


def test_all_libraries_register() -> None:
    # attempt to ensure all libraries in the repository register with DagsterLibraryRegistry
    register_call = "DagsterLibraryRegistry.register"

    library_dir = Path(__file__).parents[2] / "libraries"
    assert str(library_dir).endswith("python_modules/libraries")

    for library in os.listdir(library_dir):
        result = subprocess.run(["grep", register_call, (library_dir / library), "-r"])
        assert (
            result.returncode == 0
        ), f"Dagster library {library} is missing call to {register_call}."
