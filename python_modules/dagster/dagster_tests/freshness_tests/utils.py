import enum
import inspect
import os
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Callable

from dagster._core.workspace.load_target import PythonFileTarget


def _get_code_repr_of_value(value) -> str:
    if isinstance(value, enum.Enum):
        return f"{value.__class__.__name__}.{value.name}"
    return repr(value)


@contextmanager
def create_target_from_fn_and_local_scope(
    location_name: str,
    fn: Callable,
) -> Generator[PythonFileTarget, None, None]:
    """Copied from dagster internal repo. Lovely inspect hack which treats the passed function body as the contents of a
    Dagster code location. This util creates a temporary Python file with the function
    contents and returns a PythonFileTarget pointing to it. It also best-effort sets
    up any local variables at the top of the function, so that e.g. test parameters
    can be used as part of definitions.

    Example usage:

        .. code-block:: python
            @pytest.mark.parametrize("foo", [1, 2])
            def my_test(foo: int):
                def my_fn():
                    @asset
                    def my_asset():
                        return foo

                with create_target_from_fn_and_local_scope("my_location", my_fn) as target:
                    ...


    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file = Path(temp_dir) / "workspace.py"

        fn_contents = "\n".join(inspect.getsource(fn).strip().split("\n")[1:])
        fn_contents_lines = fn_contents.split("\n")
        indent = len(fn_contents_lines[0]) - len(fn_contents_lines[0].lstrip())

        if "return" in fn_contents_lines[-1]:
            fn_contents_lines = fn_contents_lines[:-1]

        fn_contents = "\n".join(line[indent:] for line in fn_contents_lines)

        # get all local variables in the closure of the passed function
        local_closure_from_fn = inspect.getclosurevars(fn).nonlocals

        python_src_to_set_local_closure_vars = "\n".join(
            f"{k} = {_get_code_repr_of_value(v)}" for k, v in local_closure_from_fn.items()
        )

        file_contents = f"""
## Preamble
import dagster as dg
from dagster._core.definitions.freshness import FreshnessPolicy
import datetime

## Automatically generated from function closure variables
{python_src_to_set_local_closure_vars}

## Function contents
{fn_contents}
"""
        temp_file.write_text(file_contents)

        yield PythonFileTarget(
            python_file=str(temp_file),
            attribute=None,
            working_directory=os.path.join(os.path.dirname(__file__), ".."),
            location_name=location_name,
        )
