import contextlib
import os
import posixpath
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Final, Iterator, List, Mapping, Optional, Sequence, Union

import click
import jinja2

from dagster_dg.version import __version__ as dagster_version

CLI_BUILTIN_COMPONENT_LIB_KEY = "builtin_component_lib"
DEFAULT_BUILTIN_COMPONENT_LIB: Final = "dagster_components"


_CODE_LOCATION_COMMAND_PREFIX: Final = ["uv", "run", "dagster-components"]


def execute_code_location_command(
    path: Path, cmd: Sequence[str], builtin_component_lib: Optional[str] = None
) -> str:
    full_cmd = [
        *_CODE_LOCATION_COMMAND_PREFIX,
        *(["--builtin-component-lib", builtin_component_lib] if builtin_component_lib else []),
        *cmd,
    ]
    with pushd(path):
        result = subprocess.run(
            full_cmd, stdout=subprocess.PIPE, env=get_uv_command_env(), check=True
        )
        return result.stdout.decode("utf-8")


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


_DEFAULT_EXCLUDES: List[str] = [
    "__pycache__",
    ".pytest_cache",
    "*.egg-info",
    ".DS_Store",
    ".ruff_cache",
    "tox.ini",
    ".gitkeep",  # dummy file that allows empty directories to be checked into git
]

PROJECT_NAME_PLACEHOLDER = "PROJECT_NAME_PLACEHOLDER"


# Copied from dagster._generate.generate
def generate_subtree(
    path: Path,
    excludes: Optional[List[str]] = None,
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

    click.echo(f"Generated files for Dagster project in {path}.")


def _should_skip_file(path: str, excludes: List[str] = _DEFAULT_EXCLUDES):
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
