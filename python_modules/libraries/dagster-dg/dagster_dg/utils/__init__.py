import contextlib
import importlib.util
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import textwrap
from collections.abc import Iterable, Iterator, Mapping, Sequence
from fnmatch import fnmatch
from importlib.machinery import ModuleSpec
from pathlib import Path
from typing import Any, Optional, TypeVar, Union

import click
import jinja2
import tomlkit
import tomlkit.items
from typer.rich_utils import rich_format_help
from typing_extensions import Never, TypeAlias

from dagster_dg.error import DgError
from dagster_dg.version import __version__ as dagster_version

# There is some weirdness concerning the availabilty of hashlib.HASH between different Python
# versions, so for nowe we avoid trying to import it and just alias the type to Any.
Hash: TypeAlias = Any

CLI_CONFIG_KEY = "config"


# Temporarily places a path at the front of sys.path, ensuring that any modules in that path are
# importable.
@contextlib.contextmanager
def ensure_loadable_path(path: Path) -> Iterator[None]:
    orig_path = sys.path.copy()
    sys.path.insert(0, str(path))
    try:
        yield
    finally:
        sys.path = orig_path


def is_package_installed(package_name: str) -> bool:
    try:
        return bool(importlib.util.find_spec(package_name))
    except ModuleNotFoundError:
        return False


def _get_spec_for_module(module_name: str) -> ModuleSpec:
    spec = importlib.util.find_spec(module_name)
    if not spec:
        raise DgError(f"Cannot find module: {module_name}")
    return spec


def get_path_for_module(module_name: str) -> str:
    spec = _get_spec_for_module(module_name)
    file_path = spec.origin
    if not file_path:
        raise DgError(f"Cannot find file path for module: {module_name}")
    return file_path


def get_path_for_package(package_name: str) -> str:
    spec = _get_spec_for_module(package_name)
    submodule_search_locations = spec.submodule_search_locations
    if not submodule_search_locations:
        raise DgError(f"Package does not have any locations for submodules: {package_name}")
    return submodule_search_locations[0]


def is_valid_json(value: str) -> bool:
    try:
        json.loads(value)
        return True
    except json.JSONDecodeError:
        return False


def is_executable_available(command: str) -> bool:
    return bool(shutil.which(command)) or bool(get_uv_run_executable_path(command))


# uv commands should be executed in an environment with no pre-existing VIRTUAL_ENV set. If this
# variable is set (common during development) and does not match the venv resolved by uv, it prints
# undesireable warnings.
def get_uv_command_env() -> Mapping[str, str]:
    return {k: v for k, v in os.environ.items() if not k == "VIRTUAL_ENV"}


def discover_git_root(path: Path) -> Path:
    while path != path.parent:
        if (path / ".git").exists():
            return path
        path = path.parent
    raise ValueError("Could not find git root")


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
        os.mkdir(normalized_path)

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

    click.echo(f"Scaffolded files for Dagster project in {path}.")


def _should_skip_file(path: str, excludes: list[str] = DEFAULT_FILE_EXCLUDE_PATTERNS):
    """Given a file path `path` in a source template, returns whether or not the file should be skipped
    when generating destination files.

    Technically, `path` could also be a directory path that should be skipped.
    """
    for pattern in excludes:
        if pattern.lower() in path.lower():
            return True

    return False


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
) -> None:
    for root, dirs, files in os.walk(path):
        for name in dirs + files:
            if any(fnmatch(name, pattern) for pattern in excludes):
                continue
            if includes and not any(fnmatch(name, pattern) for pattern in includes):
                continue
            filepath = os.path.join(root, name)
            hash_file_metadata(hasher, filepath)


def hash_file_metadata(hasher: Hash, path: Union[str, Path]) -> None:
    stat = os.stat(path=path)
    hasher.update(str(path).encode())
    hasher.update(str(stat.st_mtime).encode())  # Last modified time
    hasher.update(str(stat.st_size).encode())  # File size


T = TypeVar("T")


def not_none(value: Optional[T]) -> T:
    if value is None:
        raise DgError("Expected non-none value.")
    return value


def exit_with_error(error_message: str) -> Never:
    formatted_error_message = _format_error_message(error_message)
    click.echo(click.style(formatted_error_message, fg="red"))
    sys.exit(1)


def _format_error_message(message: str) -> str:
    # width=10000 unwraps any hardwrapping
    return textwrap.dedent(textwrap.fill(message, width=10000))


def generate_missing_component_type_error_message(component_key_str: str) -> str:
    return f"""
        No component type `{component_key_str}` is registered. Use 'dg component-type list'
        to see the registered component types in your environment. You may need to install a package
        that provides `{component_key_str}` into your environment.
    """


NOT_DEPLOYMENT_ERROR_MESSAGE = """
This command must be run inside a Dagster deployment directory. Ensure that there is a
`pyproject.toml` file with `tool.dg.is_deployment = true` set in the root deployment directory.
"""


NOT_CODE_LOCATION_ERROR_MESSAGE = """
This command must be run inside a Dagster code location directory. Ensure that the nearest
pyproject.toml has `tool.dg.is_code_location = true` set.
"""

NOT_COMPONENT_LIBRARY_ERROR_MESSAGE = """
This command must be run inside a Dagster component library directory. Ensure that the nearest
pyproject.toml has `tool.dg.is_component_lib = true` set.
"""


MISSING_DAGSTER_COMPONENTS_ERROR_MESSAGE = """
Could not find the `dagster-components` executable on the system path.

The `dagster-components` executable is installed with the `dagster-components` PyPI package and is
necessary for `dg` to interface with Python environments containing Dagster definitions.
`dagster-components` is installed by default when a code location is scaffolded by `dg`. However, if
you are using `dg` in a non-managed environment (either outside of a code location or using the
`--no-use-dg-managed-environment` flag), you need to independently ensure `dagster-components` is
installed.
"""

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


class DgClickCommand(DgClickHelpMixin, click.Command): ...


class DgClickGroup(DgClickHelpMixin, click.Group): ...


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


def get_toml_value(doc: tomlkit.TOMLDocument, path: Iterable[str], expected_type: type[T]) -> T:
    """Given a tomlkit-parsed document/table (`doc`),retrieve the nested value at `path` and ensure
    it is of type `expected_type`. Returns the value if so, or raises a KeyError / TypeError if not.
    """
    current: Any = doc
    for key in path:
        # If current is not a table/dict or doesn't have the key, error out
        if not isinstance(current, dict) or key not in current:
            raise KeyError(f"Key '{key}' not found in path: {'.'.join(path)}")
        current = current[key]

    # Finally, ensure the found value is of the expected type
    if not isinstance(current, expected_type):
        raise TypeError(
            f"Expected '{'.'.join(path)}' to be {expected_type.__name__}, "
            f"but got {type(current).__name__} instead."
        )
    return current


def set_toml_value(doc: tomlkit.TOMLDocument, path: Iterable[str], value: object) -> None:
    """Given a tomlkit-parsed document/table (`doc`),set a nested value at `path` to `value`. Raises
    an error if the leading keys do not already lead to a dictionary.
    """
    path_list = list(path)
    inner_dict = get_toml_value(doc, path_list[:-1], dict)
    inner_dict[path_list[-1]] = value


def get_executable_path(executable_name: str) -> Optional[str]:
    return shutil.which(executable_name)


def get_uv_run_executable_path(executable_name: str) -> Optional[str]:
    uv_run_cmd = ["uv", "run", "which", executable_name]
    try:
        return subprocess.check_output(uv_run_cmd).decode("utf-8").strip()
    except (subprocess.CalledProcessError, NotADirectoryError):
        return None
