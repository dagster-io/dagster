import contextlib
import io
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import textwrap
from collections.abc import Iterator, Mapping, Sequence
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Optional, TextIO, TypeVar, Union

import click
from click_aliases import ClickAliasedGroup
from dagster_shared.toml import (
    delete_toml_node as delete_toml_node,
    get_toml_node as get_toml_node,
    has_toml_node as has_toml_node,
    load_toml_as_dict as load_toml_as_dict,
    modify_toml as modify_toml,
    set_toml_node as set_toml_node,
    toml_path_to_str as toml_path_to_str,
)
from typing_extensions import Never, TypeAlias

from dagster_dg.error import DgError

# There is some weirdness concerning the availabilty of hashlib.HASH between different Python
# versions, so for nowe we avoid trying to import it and just alias the type to Any.
Hash: TypeAlias = Any

CLI_CONFIG_KEY = "config"


def is_windows() -> bool:
    return sys.platform == "win32"


def is_macos() -> bool:
    return sys.platform == "darwin"


def is_uv_installed() -> bool:
    return shutil.which("uv") is not None


def get_activated_venv() -> Optional[Path]:
    """Returns the path to the activated virtual environment, or None if no virtual environment is active."""
    venv_path = os.environ.get("VIRTUAL_ENV")
    if venv_path:
        return Path(venv_path).absolute()
    return None


def resolve_local_venv(start_path: Path) -> Optional[Path]:
    path = start_path
    while path != path.parent:
        venv_path = path / ".venv"
        if venv_path.exists():
            return venv_path
        path = path.parent
    return None


def get_logger(name: str, verbose: bool) -> logging.Logger:
    logger = logging.getLogger(name)
    log_level = logging.INFO if verbose else logging.WARNING
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.handlers = [handler]
    logger.setLevel(log_level)
    logger.propagate = False
    return logger


def clear_screen():
    if is_windows():
        os.system("cls")
    else:
        os.system("clear")


def get_venv_executable(venv_dir: Path, executable: str = "python") -> Path:
    if is_windows():
        return venv_dir / "Scripts" / f"{executable}.exe"
    else:
        return venv_dir / "bin" / executable


def install_to_venv(venv_dir: Path, install_args: list[str]) -> None:
    executable = get_venv_executable(venv_dir)
    command = ["uv", "pip", "install", "--python", str(executable), *install_args]
    subprocess.run(command, check=True)


def is_valid_json(value: str) -> bool:
    try:
        json.loads(value)
        return True
    except json.JSONDecodeError:
        return False


# Short for "normalize path"-- use this to get the platform-correct string representation of an
# existing string path.
def cross_platfrom_string_path(path: str):
    return str(Path(path))


# uv commands should be executed in an environment with no pre-existing VIRTUAL_ENV set. If this
# variable is set (common during development) and does not match the venv resolved by uv, it prints
# undesireable warnings.
def strip_activated_venv_from_env_vars(env: Mapping[str, str]) -> Mapping[str, str]:
    return {k: v for k, v in env.items() if not k == "VIRTUAL_ENV"}


def discover_git_root(path: Path) -> Path:
    while path != path.parent:
        if (path / ".git").exists():
            return path
        path = path.parent
    raise ValueError("Could not find git root")


def discover_venv(path: Path) -> Path:
    while path != path.parent:
        if (path / ".venv").exists():
            return path
        path = path.parent
    raise ValueError("Could not find venv")


@contextlib.contextmanager
def pushd(path: Union[str, Path]) -> Iterator[None]:
    old_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_cwd)


def camelcase(string: str) -> str:
    string = re.sub(r"^[\-_\.]", "", str(string))
    if not string:
        return string
    return str(string[0]).upper() + re.sub(
        r"[\-_\.\s]([a-z])", lambda matched: str(matched.group(1)).upper(), string[1:]
    )


def snakecase(string: str) -> str:
    # Add an underscore before capital letters and lower the case
    string = re.sub(r"(?<!^)(?=[A-Z])", "_", string).lower()
    # Replace any non-alphanumeric characters with underscores
    string = re.sub(r"[^a-z0-9_]", "_", string)
    return string


_HELP_OUTPUT_GROUP_ATTR = "rich_help_panel"


# This is a private API of typer, but it is the only way I can see to get our global options grouped
# differently and it works well.
def set_option_help_output_group(param: click.Parameter, group: str) -> None:
    """Sets the help output group for a click parameter."""
    setattr(param, "rich_help_panel", group)


def ensure_dagster_dg_tests_import() -> None:
    from dagster_dg import __file__ as dagster_dg_init_py

    dagster_dg_package_root = (Path(dagster_dg_init_py) / ".." / "..").resolve()
    assert (dagster_dg_package_root / "dagster_dg_tests").exists(), (
        "Could not find dagster_dg_tests where expected"
    )
    sys.path.append(dagster_dg_package_root.as_posix())


def hash_directory_metadata(
    hasher: Hash,
    path: Union[str, Path],
    includes: Optional[Sequence[str]],
    excludes: Sequence[str],
    error_on_missing: bool,
) -> None:
    """Hashes the metadata of all files in the given directory.

    Args:
        hasher: The hasher to use to hash the metadata.
        path: The directory path to hash the metadata of.
        includes: The glob patterns of files to include in the hash, or None to include all files.
        excludes: The glob patterns of files to exclude from the hash.
        error_on_missing: Whether to raise an error if a file is missing. Set to False for cases where
            we expect the filesystem to be actively changing.
    """
    for root, dirs, files in os.walk(path):
        for name in dirs + files:
            if any(fnmatch(name, pattern) for pattern in excludes):
                continue
            if includes and not any(fnmatch(name, pattern) for pattern in includes):
                continue
            filepath = os.path.join(root, name)
            hash_file_metadata(hasher, filepath, error_on_missing)


def hash_file_metadata(hasher: Hash, path: Union[str, Path], error_on_missing) -> None:
    """Hashes the metadata of a file.

    Args:
        hasher: The hasher to use to hash the metadata.
        path: The file path to hash the metadata of.
        error_on_missing: Whether to raise an error if a file is missing.
    """
    try:
        stat = os.stat(path=path)
        hasher.update(str(path).encode())
        hasher.update(str(stat.st_mtime).encode())  # Last modified time
        hasher.update(str(stat.st_size).encode())  # File size
    except FileNotFoundError:
        if error_on_missing:
            raise


T = TypeVar("T")


def not_none(value: Optional[T]) -> T:
    if value is None:
        raise DgError("Expected non-none value.")
    return value


def exit_with_error(error_message: str, do_format: bool = True) -> Never:
    formatted_error_message = format_multiline_str(error_message) if do_format else error_message
    click.echo(click.style(formatted_error_message, fg="red"), err=True)
    sys.exit(1)


# ########################
# ##### ERROR MESSAGES
# ########################


def format_multiline_str(message: str) -> str:
    # width=10000 unwraps any hardwrapping
    dedented = textwrap.dedent(message).strip()
    paragraphs = [textwrap.fill(p, width=10000) for p in dedented.split("\n\n")]
    return "\n\n".join(paragraphs)


def generate_missing_plugin_object_error_message(plugin_object_key: str) -> str:
    return f"""
        No plugin object `{plugin_object_key}` is registered. Use `dg list plugins`
        to see the registered plugin objects in your environment. You may need to install a package
        that provides `{plugin_object_key}` into your environment.
    """


def generate_missing_dagster_components_error_message(
    venv_path: Optional[str] = None,
) -> str:
    env_qualifier = f" for the virtual environment at {venv_path}" if venv_path else ""
    return f"""
        Could not resolve the `dagster-components` executable{env_qualifier}.
        The `dagster-components` executable is included with `dagster>=1.10.8`. It is necessary for `dg` to
        interface with Python environments. Ensure that your Python environment has
        `dagster>=1.10.8` installed.
    """


def generate_project_and_activated_venv_mismatch_warning(
    project_venv_path: Path,
    active_venv_path: Optional[Path],
) -> str:
    return f"""
        Your project is configured with `project.python_environment.active = true`, but the active
        virtual environment does not match the virtual environment found in the project root
        directory. This may lead to unexpected behavior when running `dg` commands.

            active virtual environment: {active_venv_path}
            project virtual environment: {project_venv_path}
    """


NO_LOCAL_VENV_ERROR_MESSAGE = """
This command resolves the `dagster-components` executable from a virtual environment in the project root
directory, but no virtual environment (`.venv` dir) could be found. Please create a virtual
environment in the project root directory or set tool.dg.project.python_environment = "active"
in pyproject.toml to allow use of `dagster-components` from the active Python environment.
"""

NOT_WORKSPACE_ERROR_MESSAGE = """
This command must be run inside a Dagster workspace directory. Ensure that there is a
`pyproject.toml` file with `tool.dg.directory_type = "workspace"` set in the root workspace
directory.
"""


NOT_PROJECT_ERROR_MESSAGE = """
This command must be run inside a Dagster project directory. Ensure that the nearest
pyproject.toml has `tool.dg.directory_type = "project"` set.
"""

NOT_WORKSPACE_OR_PROJECT_ERROR_MESSAGE = """
This command must be run inside a Dagster workspace or project directory. Ensure that the
nearest pyproject.toml has `tool.dg.directory_type = "project"` or `tool.dg.directory_type =
"workspace"` set.
"""


def msg_with_potential_paths(message: str, potential_paths: list[Path]) -> str:
    paths_str = "\n".join([f"- {p}" for p in potential_paths])
    return f"""{message}
You may have wanted to run this command in the following directory:

{paths_str}
"""


NOT_COMPONENT_LIBRARY_ERROR_MESSAGE = """
This command must be run inside a Dagster component library directory. Ensure that the nearest
pyproject.toml has an entry point defined under the `dagster_dg.plugin` group.
"""


def generate_tool_dg_cli_in_project_in_workspace_error_message(
    project_path: Path, workspace_path: Path
) -> str:
    return textwrap.dedent(f"""
        The `tool.dg.cli` section is ignored for project `pyproject.toml` files inside of a
        workspace. Any `tool.dg.cli` settings should be placed in the workspace config file.

        `cli` section detected in workspace project `pyproject.toml` file at:
            {project_path}
        """).strip()


# ########################
# ##### CUSTOM CLICK SUBCLASSES
# ########################

# Here we subclass click.Command and click.Group to customize the help output. We do this in order
# to visually separate global from command-specific options. The form of the output can be seen in
# dagster_dg_tests.test_custom_help_format.


class DgClickHelpMixin:
    def format_help(self, context: click.Context, formatter: click.HelpFormatter):
        """Customizes the help to include hierarchical usage."""
        from typer.rich_utils import rich_format_help

        if not isinstance(self, click.Command):
            raise ValueError("This mixin is only intended for use with click.Command instances.")

        # We use typer's rich_format_help to render our help output, despite the fact that we are
        # not using typer elsewhere in the app. Global options are separated from command-specific
        # options by setting the `rich_help_panel` attribute to "Global options" on our global options.
        rich_format_help(obj=self, ctx=context, markup_mode="rich")


class DgClickCommand(DgClickHelpMixin, click.Command): ...  # pyright: ignore[reportIncompatibleMethodOverride]


class DgClickGroup(DgClickHelpMixin, ClickAliasedGroup): ...  # pyright: ignore[reportIncompatibleMethodOverride]


# ########################
# ##### JSON SCHEMA
# ########################

_JSON_SCHEMA_TYPE_TO_CLICK_TYPE = {"string": str, "integer": int, "number": float, "boolean": bool}


def _get_field_type_info_from_field_info(field_info: Mapping[str, Any]) -> Mapping[str, Any]:
    """Extract the dict holding field type info (in particular, the type and whether it is an array)
    from a JSON schema field info dict.

    If the field info is not a union type, returns itself.
    If the field info is a union type, returns the first non-null type.
    If the field info has no type info, default to type info for type "string".
    """
    if field_info.get("type"):
        return field_info
    else:
        return next(
            (t for t in field_info.get("anyOf", []) if t.get("type") not in (None, "null")),
            {"type": "string"},
        )


def json_schema_property_to_click_option(
    key: str, field_info: Mapping[str, Any], required: bool
) -> click.Option:
    # Extract the dict holding field type info (in particular, the type and whether it is an array)
    # This might be nested in an anyOf block
    field_type_info = _get_field_type_info_from_field_info(field_info)
    is_array_type = field_type_info.get("type") == "array"
    field_type = (
        field_type_info.get("items", {}).get("type") or field_type_info.get("type") or "string"
    )

    option_name = f"--{key.replace('_', '-')}"

    # Handle object type fields as JSON strings
    if field_type == "object":
        option_type = str  # JSON string input
        help_text = f"{key} (JSON string)"
        callback = parse_json_option

    # Handle other basic types
    else:
        option_type = _JSON_SCHEMA_TYPE_TO_CLICK_TYPE[field_type]
        help_text = key
        callback = None

    return click.Option(
        [option_name],
        type=option_type,
        required=required,
        help=help_text,
        callback=callback,
        multiple=is_array_type,
    )


def parse_json_option(context: click.Context, param: click.Option, value: str):
    """Callback to parse JSON string options into Python objects."""
    if value:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            raise click.BadParameter(f"Invalid JSON string for '{param.name}'.")
    return value


def validate_dagster_availability() -> None:
    try:
        import dagster  # noqa
    except ImportError:
        raise Exception("dagster package must be installed to run this command.")


@contextlib.contextmanager
def capture_stdout() -> Iterator[TextIO]:
    """Capture stdout and return it as a string."""
    stdout = sys.stdout
    string_buffer = io.StringIO()
    try:
        sys.stdout = string_buffer
        yield string_buffer
    finally:
        sys.stdout = stdout
