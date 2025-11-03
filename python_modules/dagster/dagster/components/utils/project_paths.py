"""Utilities for discovering project paths."""

import importlib
import re
from functools import cache
from pathlib import Path

from dagster_shared import check
from dagster_shared.utils.config import (
    discover_config_file,
    get_canonical_defs_module_name,
    load_toml_as_dict,
)

from dagster._core.errors import DagsterError

_LOCAL_DEFS_STATE_DIR = ".local_defs_state"


@cache
def get_defs_module_path_for_project(project_root: Path) -> Path:
    """Get the defs module path for a project by discovering and parsing its config.

    Args:
        project_root: The root directory of the project.

    Returns:
        The filesystem path to the defs module directory.

    Raises:
        DagsterError: If no config file is found or the config is invalid.
    """
    # Discover the config file from the project root
    config_file = discover_config_file(project_root)
    if not config_file:
        raise DagsterError(f"Could not find dg.toml or pyproject.toml in {project_root}")

    # Load the config to get the root_module and defs_module
    config_dict = load_toml_as_dict(config_file)

    # Check if it's a nested config (pyproject.toml) or root (dg.toml)
    if config_file.name == "dg.toml":
        project_config = config_dict.get("project", {})
    else:
        project_config = config_dict.get("tool", {}).get("dg", {}).get("project", {})

    root_module = project_config.get("root_module")
    defs_module_name = project_config.get("defs_module")

    check.invariant(
        defs_module_name or root_module,
        f"Either defs_module or root_module must be set in the project config {config_file}",
    )

    defs_module_name = get_canonical_defs_module_name(defs_module_name, root_module)

    # Import the module to get its filesystem path
    defs_module = importlib.import_module(defs_module_name)

    # Get the module path, handling both __file__ and __path__ attributes
    if defs_module.__file__:
        # Get the directory path (handle both __init__.py and direct module files)
        defs_module_path = Path(defs_module.__file__).parent
    elif hasattr(defs_module, "__path__") and defs_module.__path__:
        defs_module_path = Path(defs_module.__path__[0])
    else:
        raise DagsterError(f"Could not determine path for module {defs_module_name}")

    return defs_module_path


def get_local_defs_state_dir(project_root: Path) -> Path:
    """Get the local state directory for the project.

    This discovers the defs module path from the project configuration and creates
    a project-local subdirectory within it for storing component state.

    Args:
        project_root: The root directory of the project.

    Returns:
        The path to the state directory.
    """
    defs_module_path = get_defs_module_path_for_project(project_root)

    local_state_dir = defs_module_path / _LOCAL_DEFS_STATE_DIR
    local_state_dir.mkdir(parents=True, exist_ok=True)

    # create .gitignore if it doesn't exist to ensure that this directory is ignored by git
    gitignore_path = local_state_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text("\n".join(["*", "*/", ".*"]))

    return local_state_dir


def get_local_state_dir(key: str, project_root: Path) -> Path:
    """Get the local state directory for a specific component state key.

    Args:
        key: The defs state key for the component.
        project_root: The root directory of the project.

    Returns:
        The path to the state directory for this key.
    """
    sanitized_key = re.sub(r"[^A-Za-z0-9._-]", "__", key)
    state_dir = get_local_defs_state_dir(project_root) / sanitized_key
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def get_local_state_path(key: str, project_root: Path) -> Path:
    """Get the local state file path for a specific component state key.

    Args:
        key: The defs state key for the component.
        project_root: The root directory of the project.

    Returns:
        The path to the state file for this key.
    """
    return get_local_state_dir(key, project_root) / "state"


def get_code_server_metadata_key(key: str) -> str:
    """Returns a key for storing defs state in the code server reconstruction metadata.
    Avoids using the original key directly to avoid potential collisions.
    """
    return f"defs-state-[{key}]"
