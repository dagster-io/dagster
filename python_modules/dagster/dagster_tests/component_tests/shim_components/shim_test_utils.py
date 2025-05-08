import os
import subprocess
import tempfile
from typing import Any, Optional

from dagster.components.lib.shim_components.base import ShimScaffolder
from pydantic import BaseModel


def execute_ruff_compliance_test(code: str) -> None:
    """Helper function to test that generated code passes ruff linting.

    Args:
        code: The Python code to test
    """
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


def execute_scaffolder_and_get_symbol(
    scaffolder: ShimScaffolder,
    symbol_name: str,
    params: Optional[BaseModel] = None,
) -> Any:
    """Helper function to execute a scaffolder and get the created symbol.

    Args:
        scaffolder: The scaffolder instance to test
        symbol_name: The name of the symbol that should be created
        params: Optional parameters to pass to the scaffolder

    Returns:
        The created symbol from the namespace
    """
    # Get the code from the scaffolder
    code = scaffolder.get_text(symbol_name, params=params)

    # Create a namespace to execute the code in
    namespace = {}
    exec(code, namespace)

    # Verify that the symbol was created
    assert symbol_name in namespace
    return namespace[symbol_name]
