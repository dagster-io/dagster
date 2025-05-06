import os
import subprocess
import tempfile

from dagster import Definitions
from dagster.components.lib.shim_components.resources import ResourcesScaffolder


def test_resources_scaffolder():
    """Test that the ResourcesScaffolder creates valid Python code that evaluates to a Definitions object."""
    # Get the code from the scaffolder
    scaffolder = ResourcesScaffolder()
    code = scaffolder.get_text("resources", None)

    # Create a namespace to execute the code in
    namespace = {}
    exec(code, namespace)

    # Verify that defs was created and is a Definitions object
    assert "resources" in namespace
    defs_fn = namespace["resources"]
    defs = defs_fn()
    assert isinstance(defs, Definitions)
    assert defs.resources == {}


def test_resources_scaffolder_ruff_compliance():
    """Test that the generated code passes ruff linting."""
    # Get the code from the scaffolder
    scaffolder = ResourcesScaffolder()
    code = scaffolder.get_text("resources", None)

    # Create a temporary file to run ruff on
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        temp_file.write(code.encode())
        temp_file_path = temp_file.name

    try:
        # Run ruff check on the temporary file
        result = subprocess.run(
            ["ruff", "check", temp_file_path],
            capture_output=True,
            text=True,
            check=False,
        )

        # Assert that ruff found no issues
        assert result.returncode == 0, f"Ruff found issues: {result.stdout}\n{result.stderr}"
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)
