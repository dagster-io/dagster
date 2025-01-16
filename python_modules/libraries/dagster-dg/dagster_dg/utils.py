import contextlib
import importlib.util
import json
import os
import posixpath
import re
import sys
from collections.abc import Iterator, Mapping, Sequence
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Optional, TypeVar, Union

import click
import jinja2
from click.formatting import HelpFormatter
from typing_extensions import TypeAlias

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
    return bool(importlib.util.find_spec(package_name))


def get_path_for_package(package_name: str) -> str:
    spec = importlib.util.find_spec(package_name)
    if not spec:
        raise DgError(f"Cannot find package: {package_name}")
    # file_path = spec.origin
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


_DEFAULT_EXCLUDES: list[str] = [
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
    excludes = _DEFAULT_EXCLUDES if not excludes else _DEFAULT_EXCLUDES + excludes

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
                        code_location_name=project_name,
                        dagster_version=dagster_version,
                        project_name=project_name,
                        **other_template_vars,
                    )
                )
                f.write("\n")

    click.echo(f"Scaffolded files for Dagster project in {path}.")


def _should_skip_file(path: str, excludes: list[str] = _DEFAULT_EXCLUDES):
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


def hash_directory_metadata(hasher: Hash, path: Union[str, Path]) -> None:
    for root, dirs, files in os.walk(path):
        for name in dirs + files:
            if any(fnmatch(name, pattern) for pattern in _DEFAULT_EXCLUDES):
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


def exit_with_error(error_message: str) -> None:
    click.echo(click.style(error_message, fg="red"))
    sys.exit(1)


# ########################
# ##### CUSTOM CLICK SUBCLASSES
# ########################

# Here we subclass click.Command and click.Group to customize the help output. We do this in order
# to visually separate global from command-specific options. The form of the output can be seen in
# dagster_dg_tests.test_custom_help_format.


class DgClickHelpMixin:
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._commands: list[str] = []

    def format_help(self, context: click.Context, formatter: click.HelpFormatter):
        """Customizes the help to include hierarchical usage."""
        if not isinstance(self, click.Command):
            raise ValueError("This mixin is only intended for use with click.Command instances.")
        self.format_usage(context, formatter)
        self.format_help_text(context, formatter)
        if isinstance(self, click.MultiCommand):
            self.format_commands(context, formatter)
        self.format_options(context, formatter)

    def get_partitioned_opts(
        self, ctx: click.Context
    ) -> tuple[Sequence[click.Parameter], Sequence[click.Parameter]]:
        from dagster_dg.cli.global_options import GLOBAL_OPTIONS

        if not isinstance(self, click.Command):
            raise ValueError("This mixin is only intended for use with click.Command instances.")

        # Filter out arguments
        opts = [p for p in self.get_params(ctx) if p.get_help_record(ctx) is not None]
        command_opts = [opt for opt in opts if opt.name not in GLOBAL_OPTIONS]
        global_opts = [opt for opt in self.get_params(ctx) if opt.name in GLOBAL_OPTIONS]
        return command_opts, global_opts

    def format_options(self, ctx: click.Context, formatter: HelpFormatter) -> None:
        """Writes all the options into the formatter if they exist."""
        if not isinstance(self, click.Command):
            raise ValueError("This mixin is only intended for use with click.Command instances.")

        # Filter out arguments
        command_opts, global_opts = self.get_partitioned_opts(ctx)

        if command_opts:
            records = [not_none(p.get_help_record(ctx)) for p in command_opts]
            with formatter.section("Options"):
                formatter.write_dl(records)

        if global_opts:
            with formatter.section("Global options"):
                records = [not_none(p.get_help_record(ctx)) for p in global_opts]
                formatter.write_dl(records)


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
