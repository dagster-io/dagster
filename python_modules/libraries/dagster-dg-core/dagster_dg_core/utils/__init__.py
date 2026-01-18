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
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    Optional,
    TextIO,
    TypeAlias,
    TypeVar,
    Union,
    overload,
)

import click
from click_aliases import ClickAliasedGroup
from dagster_shared.utils import environ
from typing_extensions import Never

from dagster_dg_core.error import DgError

if TYPE_CHECKING:
    import tomlkit

# There is some weirdness concerning the availabilty of hashlib.HASH between different Python
# versions, so for nowe we avoid trying to import it and just alias the type to Any.
Hash: TypeAlias = Any

CLI_CONFIG_KEY = "config"

DG_CLI_MAX_OUTPUT_WIDTH = 120


def show_dg_unlaunched_commands() -> bool:
    """We hide cli commands that we have not launched yet. Override this by setting
    the DG_SHOW_UNLAUNCHED_COMMANDS environment variable to any value.
    """
    return os.getenv("DG_SHOW_UNLAUNCHED_COMMANDS") is not None


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


def get_shortest_path_repr(abs_path: Path) -> Path:
    try:
        return abs_path.relative_to(Path.cwd())
    except ValueError:  # raised when path is not a descendant of cwd
        return abs_path


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


def get_venv_activation_cmd(venv_dir: Path) -> str:
    if is_windows():
        return str(venv_dir / "Scripts" / "activate.bat")
    else:
        return f"source {venv_dir / 'bin' / 'activate'}"


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


def discover_repo_root(path: Path) -> Path:
    """Find the dagster repo root by looking for python_modules/dagster/.

    This works even when dagster is a subfolder in a monorepo.
    """
    while path != path.parent:
        if (path / "python_modules" / "dagster").is_dir():
            return path
        path = path.parent
    raise ValueError("Could not find dagster repo root")


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
    """Convert a string to snake_case.

    This function handles consecutive uppercase letters more gracefully than the naive approach.
    For example: "ACMEDatabricksJobComponent" -> "acme_databricks_job_component"
    Rather than: "ACMEDatabricksJobComponent" -> "a_c_m_e_databricks_job_component"
    """
    if not string:
        return string

    # First, handle sequences of uppercase letters followed by lowercase letters
    # This matches patterns like "ACME" in "ACMEDatabricks" -> "ACME_Databricks"
    # The pattern (?<![A-Z])([A-Z]+)(?=[A-Z][a-z]) matches:
    # - One or more uppercase letters ([A-Z]+)
    # - That are followed by an uppercase letter then lowercase ((?=[A-Z][a-z]))
    # - But not preceded by another uppercase letter ((?<![A-Z]))
    string = re.sub(r"([A-Z]+)(?=[A-Z][a-z])", r"\1_", string)

    # Add underscores before uppercase letters that follow lowercase letters or numbers
    # This handles the transition from lowercase/numbers to uppercase
    string = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", string)

    # Convert to lowercase
    string = string.lower()

    # Replace any non-alphanumeric characters with underscores
    string = re.sub(r"[^a-z0-9_]", "_", string)

    # Clean up multiple consecutive underscores
    string = re.sub(r"_+", "_", string)

    # Remove leading/trailing underscores
    string = string.strip("_")

    return string


_HELP_OUTPUT_GROUP_ATTR = "rich_help_panel"


# This is a private API of typer, but it is the only way I can see to get our global options grouped
# differently and it works well.
def set_option_help_output_group(param: click.Parameter, group: str) -> None:
    """Sets the help output group for a click parameter."""
    setattr(param, "rich_help_panel", group)


@contextlib.contextmanager
def modify_toml(path: Path) -> Iterator["tomlkit.TOMLDocument"]:
    import tomlkit

    toml = tomlkit.parse(path.read_text())
    yield toml
    path.write_text(tomlkit.dumps(toml))


@contextlib.contextmanager
def modify_toml_as_dict(path: Path) -> Iterator[dict[str, Any]]:  # unwrap gets the dict
    """Modify a TOML file as a plain python dict, destroying any comments or formatting.

    This is a destructive means of modifying TOML. We convert the parsed TOML document into a plain
    python object, modify it, and then write it back to the file. This will destroy comments and
    styling. It is useful mostly in a testing context where we want to e.g. set arbitrary invalid
    values in the file without worrying about the details of the TOML syntax (it has multiple kinds of
    dict-like objects, for instance).
    """
    import tomlkit

    toml_dict = load_toml_as_dict(path)
    yield toml_dict
    path.write_text(tomlkit.dumps(toml_dict))


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


def generate_missing_registry_object_error_message(registry_object_key: str) -> str:
    return f"""
        No registry object `{registry_object_key}` is registered. Use `dg list components`
        to see the registered objects in your environment. You may need to install a package
        that provides `{registry_object_key}` into your environment.
    """


def generate_project_and_activated_venv_mismatch_warning(
    project_venv_path: Path,
    active_venv_path: Optional[Path],
) -> str:
    return f"""
        The active virtual environment does not match the virtual environment found in the project
        root directory. This may lead to unexpected behavior when running `dg` commands.

            active virtual environment: {active_venv_path}
            project virtual environment: {project_venv_path}
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
pyproject.toml has an entry point defined under the `dagster_dg_cli.registry_modules` group.
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
# dagster_dg_core_tests.test_custom_help_format.


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


class DgClickCommand(DgClickHelpMixin, click.Command):  # pyright: ignore[reportIncompatibleMethodOverride]
    def __init__(self, *args, unlaunched: bool = False, **kwargs):
        """DgClickCommand with conditional hiding for unlaunched features.

        Args:
            unlaunched: If True, the command will be hidden unless DG_SHOW_UNLAUNCHED_COMMANDS
                environment variable is set.
        """
        if unlaunched:
            kwargs["hidden"] = not show_dg_unlaunched_commands()
        super().__init__(*args, **kwargs)


class DgClickGroup(DgClickHelpMixin, ClickAliasedGroup):  # pyright: ignore[reportIncompatibleMethodOverride]
    def __init__(self, *args, unlaunched: bool = False, **kwargs):
        """DgClickGroup with conditional hiding for unlaunched features.

        Args:
            unlaunched: If True, the group will be hidden unless DG_SHOW_UNLAUNCHED_COMMANDS
                environment variable is set.
        """
        if unlaunched:
            kwargs["hidden"] = not show_dg_unlaunched_commands()
        super().__init__(*args, **kwargs)


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
        help_text = f"[scaffolder parameter] {key} (JSON string)"
        callback = parse_json_option

    # Handle other basic types
    else:
        option_type = _JSON_SCHEMA_TYPE_TO_CLICK_TYPE[field_type]
        help_text = f"(scaffolder param) {key}"
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


# ########################
# ##### TOML MANIPULATION
# ########################

TomlPath: TypeAlias = tuple[Union[str, int], ...]
TomlDoc: TypeAlias = Union["tomlkit.TOMLDocument", dict[str, Any]]


def load_toml_as_dict(path: Path) -> dict[str, Any]:
    import tomlkit

    return tomlkit.parse(path.read_text()).unwrap()


def get_toml_node(
    doc: TomlDoc,
    path: TomlPath,
    expected_type: Union[type[T], tuple[type[T], ...]],
) -> T:
    """Given a tomlkit-parsed document/table (`doc`),retrieve the nested value at `path` and ensure
    it is of type `expected_type`. Returns the value if so, or raises a KeyError / TypeError if not.
    """
    value = _gather_toml_nodes(doc, path)[-1]
    if not isinstance(value, expected_type):
        expected_types = expected_type if isinstance(expected_type, tuple) else (expected_type,)
        type_str = " or ".join(t.__name__ for t in expected_types)
        raise TypeError(
            f"Expected '{toml_path_to_str(path)}' to be {type_str}, "
            f"but got {type(value).__name__} instead."
        )
    return value


def has_toml_node(doc: TomlDoc, path: TomlPath) -> bool:
    """Given a tomlkit-parsed document/table (`doc`), return whether a value is defined at `path`."""
    result = _gather_toml_nodes(doc, path, error_on_missing=False)
    return False if result is None else True


def delete_toml_node(doc: TomlDoc, path: TomlPath) -> None:
    """Given a tomlkit-parsed document/table (`doc`), delete the nested value at `path`. Raises
    an error if the leading keys do not already lead to a TOML container node.
    """
    import tomlkit

    nodes = _gather_toml_nodes(doc, path)
    container = nodes[-2] if len(nodes) > 1 else doc
    key_or_index = path[-1]
    if isinstance(container, dict):
        assert isinstance(key_or_index, str)  # We already know this from _traverse_toml_path
        del container[key_or_index]
    elif isinstance(container, tomlkit.TOMLDocument):
        assert isinstance(key_or_index, str)  # We already know this from _traverse_toml_path
        container.remove(key_or_index)
    elif isinstance(container, list):
        assert isinstance(key_or_index, int)  # We already know this from _traverse_toml_path
        container.pop(key_or_index)
    else:
        raise Exception("Unreachable.")


def set_toml_node(doc: TomlDoc, path: TomlPath, value: object) -> None:
    """Given a tomlkit-parsed document/table (`doc`),set a nested value at `path` to `value`. Raises
    an error if the leading keys do not already lead to a TOML container node.
    """
    container = _gather_toml_nodes(doc, path[:-1])[-1] if len(path) > 1 else doc
    key_or_index = path[-1]  # type: ignore  # pyright bug
    if isinstance(container, dict):
        if not isinstance(key_or_index, str):
            raise TypeError(f"Expected key to be a string, but got {type(key_or_index).__name__}")
        container[key_or_index] = value
    elif isinstance(container, list):
        if not isinstance(key_or_index, int):
            raise TypeError(f"Expected key to be an integer, but got {type(key_or_index).__name__}")
        container[key_or_index] = value
    else:
        raise Exception("Unreachable.")


@overload
def _gather_toml_nodes(
    doc: TomlDoc, path: TomlPath, error_on_missing: Literal[True] = ...
) -> list[Any]: ...


@overload
def _gather_toml_nodes(
    doc: TomlDoc, path: TomlPath, error_on_missing: Literal[False] = ...
) -> Optional[list[Any]]: ...


def _gather_toml_nodes(
    doc: TomlDoc, path: TomlPath, error_on_missing: bool = True
) -> Optional[list[Any]]:
    nodes: list[Any] = []
    current: Any = doc
    for key in path:
        if isinstance(key, str):
            if not isinstance(current, dict) or key not in current:
                if error_on_missing:
                    raise KeyError(f"Key '{key}' not found in path: {toml_path_to_str(path)}")
                return None
            current = current[key]
        elif isinstance(key, int):
            if not isinstance(current, list) or key < 0 or key >= len(current):
                if error_on_missing:
                    raise KeyError(f"Index '{key}' not found in path: {toml_path_to_str(path)}")
                return None
            current = current[key]
        else:
            raise TypeError(f"Expected key to be a string or integer, but got {type(key)}")
        nodes.append(current)

    return nodes


def toml_path_to_str(path: TomlPath) -> str:
    if len(path) == 0:
        return ""
    first = path[0]
    if not isinstance(first, str):
        raise TypeError(f"Expected first element of path to be a string, but got {type(first)}")
    elif len(path) == 1:
        return first
    else:
        str_path = first
        for item in path[1:]:
            if isinstance(item, int):
                str_path += f"[{item}]"
            elif isinstance(item, str):
                str_path += f".{item}"
            else:
                raise TypeError(
                    f"Expected path elements to be strings or integers, but got {type(item)}"
                )
    return str_path


def toml_path_from_str(path: str) -> TomlPath:
    tokens = []
    for segment in path.split("."):
        # Split each segment by bracketed chunks, e.g. "key[1]" -> ["key", "[1]"]
        parts = re.split(r"(\[\d+\])", segment)
        for p in parts:
            if not p:  # Skip empty strings
                continue
            if p.startswith("[") and p.endswith("]"):
                tokens.append(int(p[1:-1]))  # Convert "[1]" to integer 1
            else:
                tokens.append(p)
    return tuple(tokens)


def create_toml_node(
    doc: dict[str, Any],
    path: tuple[Union[str, int], ...],
    value: object,
) -> None:
    """Set a toml node at a path that consists of a sequence of keys and integer indices.
    Intermediate containers that don't yet exist will be created along the way based on the types of
    the keys. Note that this does not support TOMLDocument objects, only plain dictionaries. The
    reason is that the correct type of container to insert at intermediate nodes is ambiguous for
    TOMLDocmuent objects.
    """
    import tomlkit

    if isinstance(doc, tomlkit.TOMLDocument):
        raise TypeError(
            "`create_toml_node` only works on the plain dictionary representation of a TOML document."
        )
    current: Any = doc
    for i, key in enumerate(path):
        is_final_key = i == len(path) - 1
        if isinstance(key, str):
            if not isinstance(current, dict):
                raise KeyError(f"Key '{key}' not found in path: {toml_path_to_str(path)}")
            elif is_final_key:
                current[key] = value
            elif key not in current:
                current[key] = _get_new_container_node(path[i + 1])
            current = current[key]
        elif isinstance(key, int):
            if not isinstance(current, list):
                raise KeyError(f"Index '{key}' not found in path: {toml_path_to_str(path)}")
            is_key_in_range = key >= 0 and key < len(current)
            is_append_key = key == len(current)
            if is_final_key and is_key_in_range:
                current[key] = value
            elif is_final_key and is_append_key:
                current.append(value)
            elif is_key_in_range:
                current = current[key]
            elif is_append_key:
                current.append(_get_new_container_node(path[i + 1]))
                current = current[key]
            else:
                raise KeyError(f"Key '{key}' not found in path: {toml_path_to_str(path)}")
        else:
            raise TypeError(f"Expected key to be a string or integer, but got {type(key)}")


def _get_new_container_node(
    representative_key: Union[int, str],
) -> Union[dict[str, Any], list[Any]]:
    return [] if isinstance(representative_key, int) else {}


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


@contextlib.contextmanager
def activate_venv(venv_path: Union[str, Path]) -> Iterator[None]:
    """Simulated activation of the passed in virtual environment for the current process."""
    venv_path = (Path(venv_path) if isinstance(venv_path, str) else venv_path).absolute()
    with environ(
        {
            "VIRTUAL_ENV": str(venv_path),
            "PATH": os.pathsep.join(
                [
                    str(venv_path / ("Scripts" if sys.platform == "win32" else "bin")),
                    os.getenv("PATH", ""),
                ]
            ),
        }
    ):
        yield
