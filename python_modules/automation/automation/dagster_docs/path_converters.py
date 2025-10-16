"""Path converter functions for different project layouts."""

from pathlib import Path
from typing import Union


def dagster_path_converter(file_path: Path, root_path: Path) -> Union[str, None]:
    """Convert Dagster project file paths to importable module paths.

    Handles the specific Dagster project structure:
    - python_modules/dagster/dagster/... -> dagster...
    - python_modules/libraries/dagster-aws/dagster_aws/... -> dagster_aws...
    """
    try:
        relative_path = file_path.relative_to(root_path)
        if relative_path.parts[0] != "python_modules":
            return None

        parts = list(relative_path.parts[1:])  # Skip "python_modules"

        if parts and parts[0] == "dagster":
            # Core dagster module: python_modules/dagster/dagster/... -> dagster...
            module_parts = list(parts[1:])  # Skip first "dagster" directory
        elif parts and parts[0] == "libraries" and len(parts) >= 2:
            # Library module: python_modules/libraries/dagster-aws/dagster_aws/... -> dagster_aws...
            lib_name = parts[1].replace("-", "_")  # dagster-aws -> dagster_aws
            remaining_parts = list(parts[2:])

            # Always include the lib_name as the first part of the module path
            module_parts = [lib_name] + remaining_parts
        else:
            return None

        # Remove __init__.py and .py extension
        if module_parts and module_parts[-1] == "__init__.py":
            module_parts = module_parts[:-1]
        elif module_parts and module_parts[-1].endswith(".py"):
            module_parts[-1] = module_parts[-1][:-3]

        return ".".join(module_parts) if module_parts else None

    except (ValueError, IndexError):
        return None


def generic_path_converter(file_path: Path, root_path: Path) -> Union[str, None]:
    """Convert generic file paths to importable module paths.

    Simple conversion: path/to/module.py -> path.to.module
    Useful for testing and simple project structures.
    """
    try:
        relative_path = file_path.relative_to(root_path)
        parts = list(relative_path.parts)

        # Remove .py extension
        if parts and parts[-1].endswith(".py"):
            parts[-1] = parts[-1][:-3]

        # Remove __init__ (from __init__.py)
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]

        return ".".join(parts) if parts else None

    except (ValueError, IndexError):
        return None


def simple_package_converter(package_name: str):
    """Create a path converter for a simple package structure.

    Returns a function that converts paths like:
    package_root/submodule.py -> package_name.submodule

    Args:
        package_name: The base package name to prepend
    """

    def converter(file_path: Path, root_path: Path) -> Union[str, None]:
        try:
            relative_path = file_path.relative_to(root_path)
            parts = list(relative_path.parts)

            # Remove .py extension
            if parts and parts[-1].endswith(".py"):
                parts[-1] = parts[-1][:-3]

            # Remove __init__ (from __init__.py)
            if parts and parts[-1] == "__init__":
                parts = parts[:-1]

            if parts:
                module_path = ".".join(parts)
                return f"{package_name}.{module_path}"
            else:
                return package_name

        except (ValueError, IndexError):
            return None

    return converter
