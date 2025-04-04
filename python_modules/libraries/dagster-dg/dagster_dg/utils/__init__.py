import contextlib
import json
import os
import posixpath
import re
import subprocess
import sys
import textwrap
from collections.abc import Iterator, Mapping, Sequence
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Literal, Optional, TypeVar, Union, overload

import click
import jinja2
import tomlkit
from typer.rich_utils import rich_format_help
from typing_extensions import Never, TypeAlias

from dagster_dg.error import DgError
from dagster_dg.version import __version__ as dagster_version

# There is some weirdness concerning the availabilty of hashlib.HASH between different Python
# versions, so for nowe we avoid trying to import it and just alias the type to Any.
Hash: TypeAlias = Any

CLI_CONFIG_KEY = "config"


def is_windows() -> bool:
    return sys.platform == "win32"


def is_macos() -> bool:
    return sys.platform == "darwin"


def resolve_local_venv(start_path: Path) -> Optional[Path]:
    path = start_path
    while path != path.parent:
        venv_path = path / ".venv"
        if venv_path.exists():
            return venv_path
        path = path.parent
    return None


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


DEFAULT_FILE_EXCLUDE_PATTERNS: list[str] = [
    "__pycache__",
    ".pytest_cache",
    "*.egg-info",
    "*.cpython-*",
    ".DS_Store",
    ".ruff_cache",
    "tox.ini",
    ".gitkeep",  # dummy file that allows empty directories to be checked into git
]

PROJECT_NAME_PLACEHOLDER = "PROJECT_NAME_PLACEHOLDER"


# Copied from dagster._generate.generate
def scaffold_subtree(
    path: Path,
    excludes: Optional[list[str]] = None,
    name_placeholder: str = PROJECT_NAME_PLACEHOLDER,
    templates_path: str = PROJECT_NAME_PLACEHOLDER,
    project_name: Optional[str] = None,
    **other_template_vars: Any,
):
    """Renders templates for Dagster project."""
    excludes = (
        DEFAULT_FILE_EXCLUDE_PATTERNS if not excludes else DEFAULT_FILE_EXCLUDE_PATTERNS + excludes
    )

    normalized_path = os.path.normpath(path)
    project_name = project_name or os.path.basename(normalized_path).replace("-", "_")
    if not os.path.exists(normalized_path):
        os.makedirs(normalized_path, exist_ok=True)

    project_template_path = os.path.join(os.path.dirname(__file__), "templates", templates_path)
    loader = jinja2.FileSystemLoader(searchpath=project_template_path)
    env = jinja2.Environment(loader=loader)

    # merge custom skip_files with the default list
    for root, dirs, files in os.walk(project_template_path):
        # For each subdirectory in the source template, create a subdirectory in the destination.
        for dirname in dirs:
            src_dir_path = os.path.join(root, dirname)
            if _should_skip_file(src_dir_path, excludes):
                continue

            src_relative_dir_path = os.path.relpath(src_dir_path, project_template_path)
            dst_relative_dir_path = src_relative_dir_path.replace(
                name_placeholder,
                project_name,
                1,
            )
            dst_dir_path = os.path.join(normalized_path, dst_relative_dir_path)

            os.mkdir(dst_dir_path)

        # For each file in the source template, render a file in the destination.
        for filename in files:
            src_file_path = os.path.join(root, filename)
            if _should_skip_file(src_file_path, excludes):
                continue

            src_relative_file_path = os.path.relpath(src_file_path, project_template_path)
            dst_relative_file_path = src_relative_file_path.replace(
                name_placeholder,
                project_name,
                1,
            )
            dst_file_path = os.path.join(normalized_path, dst_relative_file_path)

            if dst_file_path.endswith(".jinja"):
                dst_file_path = dst_file_path[: -len(".jinja")]

            with open(dst_file_path, "w", encoding="utf8") as f:
                # Jinja template names must use the POSIX path separator "/".
                template_name = src_relative_file_path.replace(os.sep, posixpath.sep)
                template: jinja2.environment.Template = env.get_template(name=template_name)
                f.write(
                    template.render(
                        repo_name=project_name,  # deprecated
                        dagster_version=dagster_version,
                        project_name=project_name,
                        **other_template_vars,
                    )
                )
                f.write("\n")


def _should_skip_file(path: str, excludes: list[str] = DEFAULT_FILE_EXCLUDE_PATTERNS):
    """Given a file path `path` in a source template, returns whether or not the file should be skipped
    when generating destination files.

    Technically, `path` could also be a directory path that should be skipped.
    """
    for pattern in excludes:
        if pattern.lower() in path.lower():
            return True

    return False


@contextlib.contextmanager
def modify_toml(path: Path) -> Iterator[tomlkit.TOMLDocument]:
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
    toml_dict = load_toml_as_dict(path)
    yield toml_dict
    path.write_text(tomlkit.dumps(toml_dict))


def ensure_dagster_dg_tests_import() -> None:
    from dagster_dg import __file__ as dagster_dg_init_py

    dagster_dg_package_root = (Path(dagster_dg_init_py) / ".." / "..").resolve()
    assert (
        dagster_dg_package_root / "dagster_dg_tests"
    ).exists(), "Could not find dagster_dg_tests where expected"
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


def exit_with_error(error_message: str) -> Never:
    formatted_error_message = format_multiline_str(error_message)
    click.echo(click.style(formatted_error_message, fg="red"))
    sys.exit(1)


# ########################
# ##### ERROR MESSAGES
# ########################


def format_multiline_str(message: str) -> str:
    # width=10000 unwraps any hardwrapping
    dedented = textwrap.dedent(message).strip()
    paragraphs = [textwrap.fill(p, width=10000) for p in dedented.split("\n\n")]
    return "\n\n".join(paragraphs)


def generate_missing_component_type_error_message(component_key_str: str) -> str:
    return f"""
        No component type `{component_key_str}` is registered. Use 'dg list component-type'
        to see the registered component types in your environment. You may need to install a package
        that provides `{component_key_str}` into your environment.
    """


def generate_missing_dagster_components_in_local_venv_error_message(venv_path: str) -> str:
    return f"""
        Could not find the `dagster-components` executable in the virtual environment at {venv_path}.
        The `dagster-components` executable is necessary for `dg` to interface with Python environments
        containing Dagster definitions. Ensure that the virtual environment has the `dagster-components`
        package installed.
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

NOT_COMPONENT_LIBRARY_ERROR_MESSAGE = """
This command must be run inside a Dagster component library directory. Ensure that the nearest
pyproject.toml has an entry point defined under the `dagster_dg.library` group.
"""

MISSING_DAGSTER_COMPONENTS_ERROR_MESSAGE = """
Could not find the `dagster-components` executable on the system path.

The `dagster-components` executable is installed with the `dagster-components` PyPI package and is
necessary for `dg` to interface with Python environments containing Dagster definitions.
`dagster-components` is installed by default when a project is scaffolded by `dg`. However, if
you are using `dg` in a non-managed environment (either outside of a Dagster project or using the
`--no-use-dg-managed-environment` flag), you need to independently ensure `dagster-components` is
installed.
"""


def generate_tool_dg_cli_in_project_in_workspace_error_message(
    project_path: Path, workspace_path: Path
) -> str:
    return textwrap.dedent(f"""
        `tool.dg.cli` section detected in project `pyproject.toml` file at:
            {project_path}
        This project is inside of a workspace at:
            {workspace_path}
        """).lstrip() + format_multiline_str("""
        The `tool.dg.cli` section is ignored for project `pyproject.toml` files inside of a
        workspace. Any `tool.dg.cli` settings should be placed in the workspace config file.
        """)


# ########################
# ##### CUSTOM CLICK SUBCLASSES
# ########################

# Here we subclass click.Command and click.Group to customize the help output. We do this in order
# to visually separate global from command-specific options. The form of the output can be seen in
# dagster_dg_tests.test_custom_help_format.


class DgClickHelpMixin:
    def format_help(self, context: click.Context, formatter: click.HelpFormatter):
        """Customizes the help to include hierarchical usage."""
        if not isinstance(self, click.Command):
            raise ValueError("This mixin is only intended for use with click.Command instances.")

        # We use typer's rich_format_help to render our help output, despite the fact that we are
        # not using typer elsewhere in the app. Global options are separated from command-specific
        # options by setting the `rich_help_panel` attribute to "Global options" on our global options.
        rich_format_help(obj=self, ctx=context, markup_mode="rich")


class DgClickCommand(DgClickHelpMixin, click.Command): ...  # pyright: ignore[reportIncompatibleMethodOverride]


class DgClickGroup(DgClickHelpMixin, click.Group): ...  # pyright: ignore[reportIncompatibleMethodOverride]


# ########################
# ##### JSON SCHEMA
# ########################

_JSON_SCHEMA_TYPE_TO_CLICK_TYPE = {"string": str, "integer": int, "number": float, "boolean": bool}


def json_schema_property_to_click_option(
    key: str, field_info: Mapping[str, Any], required: bool
) -> click.Option:
    field_type = field_info.get("type", "string")
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
TomlDoc: TypeAlias = Union[tomlkit.TOMLDocument, dict[str, Any]]


def load_toml_as_dict(path: Path) -> dict[str, Any]:
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
