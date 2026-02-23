import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, TypeVar

import dagster as dg
from dagster.components.lib.shim_components.base import ShimScaffolder, TModel
from dagster.components.scaffold.scaffold import NoParams
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def make_test_scaffold_request(
    filename: str, params: TModel | None = None
) -> dg.ScaffoldRequest[TModel]:
    return dg.ScaffoldRequest[TModel](
        type_name="Test",
        target_path=Path(f"{filename}.py"),
        scaffold_format="python",
        project_root=None,
        params=params if params is not None else NoParams(),  # type: ignore
    )


def execute_ruff_compliance_test(code: str) -> None:
    """Helper function to test that generated code passes ruff linting.

    Args:
        code: The Python code to test
    """
    # Create a temporary file to run ruff on
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        # Create an empty __init__.py file in the same directory as the temp file
        init_path = os.path.join(os.path.dirname(temp_file.name), "__init__.py")
        with open(init_path, "w"):
            pass
        temp_file.write(code.encode())
        temp_file_path = temp_file.name

    try:
        # Run ruff check on the temporary file
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", temp_file_path],
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
    scaffolder: ShimScaffolder[Any],
    symbol_name: str,
    params: TModel | None = None,
) -> Any:
    """Helper function to execute a scaffolder and get the created symbol."""
    # Construct a ScaffoldRequest for the new get_text signature
    request = dg.ScaffoldRequest(
        type_name=scaffolder.__class__.__name__,
        target_path=Path(f"{symbol_name}.py"),
        scaffold_format="python",
        project_root=None,
        params=params if params is not None else NoParams(),
    )
    code = scaffolder.get_text(request)
    namespace = {}
    exec(code, namespace)
    assert symbol_name in namespace
    return namespace[symbol_name]
