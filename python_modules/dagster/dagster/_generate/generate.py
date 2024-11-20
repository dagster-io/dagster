import os
import posixpath
from typing import Any, List, Optional, Type

import click
import jinja2

from dagster._components import Component
from dagster._utils import camelcase, pushd
from dagster.version import __version__ as dagster_version

DEFAULT_EXCLUDES: List[str] = [
    "__pycache__",
    ".pytest_cache",
    "*.egg-info",
    ".DS_Store",
    ".ruff_cache",
    "tox.ini",
    ".gitkeep",  # dummy file that allows empty directories to be checked into git
]

PROJECT_NAME_PLACEHOLDER = "PROJECT_NAME_PLACEHOLDER"


def generate_deployment(path: str) -> None:
    click.echo(f"Creating a Dagster deployment at {path}.")

    generate_project(
        path=path,
        name_placeholder="DEPLOYMENT_NAME_PLACEHOLDER",
        templates_path=os.path.join(
            os.path.dirname(__file__), "templates", "DEPLOYMENT_NAME_PLACEHOLDER"
        ),
    )


def generate_code_location(path: str) -> None:
    click.echo(f"Creating a Dagster code location at {path}.")

    generate_project(
        path=path,
        name_placeholder="CODE_LOCATION_NAME_PLACEHOLDER",
        templates_path=os.path.join(
            os.path.dirname(__file__), "templates", "CODE_LOCATION_NAME_PLACEHOLDER"
        ),
    )


def generate_component_type(root_path: str, name: str) -> None:
    click.echo(f"Creating a Dagster component type at {root_path}/{name}.py.")

    generate_project(
        path=root_path,
        name_placeholder="COMPONENT_TYPE_NAME_PLACEHOLDER",
        templates_path=os.path.join(os.path.dirname(__file__), "templates", "COMPONENT_TYPE"),
        project_name=name,
        component_type_class_name=camelcase(name),
    )


def generate_component_instance(root_path: str, name: str, component_type: Type[Component]) -> None:
    click.echo(f"Creating a Dagster component instance at {root_path}/{name}.py.")

    component_instance_root_path = os.path.join(root_path, name)
    os.mkdir(component_instance_root_path)
    with pushd(component_instance_root_path):
        component_type.generate_files()


def generate_repository(path: str):
    REPO_NAME_PLACEHOLDER = "REPO_NAME_PLACEHOLDER"

    click.echo(f"Creating a Dagster repository at {path}.")

    #
    generate_project(
        path=path,
        excludes=None,
        name_placeholder=REPO_NAME_PLACEHOLDER,
        templates_path=os.path.join(os.path.dirname(__file__), "templates", REPO_NAME_PLACEHOLDER),
    )

    click.echo(f"Generated files for Dagster repository in {path}.")


def generate_project(
    path: str,
    excludes: Optional[List[str]] = None,
    name_placeholder: str = PROJECT_NAME_PLACEHOLDER,
    templates_path: str = PROJECT_NAME_PLACEHOLDER,
    project_name: Optional[str] = None,
    **other_template_vars: Any,
):
    """Renders templates for Dagster project."""
    excludes = DEFAULT_EXCLUDES if not excludes else DEFAULT_EXCLUDES + excludes

    click.echo(f"Creating a Dagster project at {path}.")

    normalized_path = os.path.normpath(path)
    project_name = project_name or os.path.basename(normalized_path).replace("-", "_")
    if not os.path.exists(normalized_path):
        os.mkdir(normalized_path)

    project_template_path: str = os.path.join(
        os.path.dirname(__file__), "templates", templates_path
    )
    loader: jinja2.loaders.FileSystemLoader = jinja2.FileSystemLoader(
        searchpath=project_template_path
    )
    env: jinja2.environment.Environment = jinja2.Environment(loader=loader)

    # merge custom skip_files with the default list
    for root, dirs, files in os.walk(project_template_path):
        # For each subdirectory in the source template, create a subdirectory in the destination.
        for dirname in dirs:
            src_dir_path: str = os.path.join(root, dirname)
            if _should_skip_file(src_dir_path, excludes):
                continue

            src_relative_dir_path: str = os.path.relpath(src_dir_path, project_template_path)
            dst_relative_dir_path: str = src_relative_dir_path.replace(
                name_placeholder,
                project_name,
                1,
            )
            dst_dir_path: str = os.path.join(normalized_path, dst_relative_dir_path)

            os.mkdir(dst_dir_path)

        # For each file in the source template, render a file in the destination.
        for filename in files:
            src_file_path = os.path.join(root, filename)
            if _should_skip_file(src_file_path, excludes):
                continue

            src_relative_file_path: str = os.path.relpath(src_file_path, project_template_path)
            dst_relative_file_path: str = src_relative_file_path.replace(
                name_placeholder,
                project_name,
                1,
            )
            dst_file_path: str = os.path.join(normalized_path, dst_relative_file_path)

            if dst_file_path.endswith(".jinja"):
                dst_file_path = dst_file_path[: -len(".jinja")]

            with open(dst_file_path, "w", encoding="utf8") as f:
                # Jinja template names must use the POSIX path separator "/".
                template_name: str = src_relative_file_path.replace(os.sep, posixpath.sep)
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


def _should_skip_file(path: str, excludes: List[str] = DEFAULT_EXCLUDES):
    """Given a file path `path` in a source template, returns whether or not the file should be skipped
    when generating destination files.

    Technically, `path` could also be a directory path that should be skipped.
    """
    for pattern in excludes:
        if pattern.lower() in path.lower():
            return True

    return False
