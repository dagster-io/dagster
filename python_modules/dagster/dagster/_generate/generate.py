import os
import posixpath

import click
import jinja2

from dagster.version import __version__ as dagster_version

IGNORE_PATTERN_LIST = ["__pycache__", ".pytest_cache", "*.egg-info", ".DS_Store", "tox.ini"]


def generate_repository(path: str):
    REPO_NAME_PLACEHOLDER = "REPO_NAME_PLACEHOLDER"

    click.echo(f"Creating a Dagster repository at {path}.")

    # Step 1: Generate files for Dagster repository
    _generate_files_from_template(
        path=path,
        name_placeholder=REPO_NAME_PLACEHOLDER,
        project_template_path=os.path.join(
            os.path.dirname(__file__), "templates", REPO_NAME_PLACEHOLDER
        ),
    )

    click.echo(f"Generated files for Dagster repository in {path}.")


def generate_code_location(path: str):
    CODE_LOCATION_NAME_PLACEHOLDER = "CODE_LOCATION_NAME_PLACEHOLDER"

    click.echo(f"Creating a Dagster code location at {path}.")

    # Step 1: Generate files for Dagster code location including pyproject.toml, setup.py
    _generate_files_from_template(
        path=path,
        name_placeholder=CODE_LOCATION_NAME_PLACEHOLDER,
        project_template_path=os.path.join(
            os.path.dirname(__file__), "templates", CODE_LOCATION_NAME_PLACEHOLDER
        ),
    )

    click.echo(f"Generated files for Dagster code location in {path}.")


def generate_project(path: str):
    PROJECT_NAME_PLACEHOLDER = "PROJECT_NAME_PLACEHOLDER"

    click.echo(f"Creating a Dagster project at {path}.")

    # Step 1: Generate files for Dagster code location
    generate_code_location(path)

    # Step 2: Generate project-level files, e.g. README
    _generate_files_from_template(
        path=path,
        name_placeholder=PROJECT_NAME_PLACEHOLDER,
        project_template_path=os.path.join(
            os.path.dirname(__file__), "templates", PROJECT_NAME_PLACEHOLDER
        ),
        skip_mkdir=True,
    )

    click.echo(f"Generated files for Dagster project in {path}.")


def _generate_files_from_template(
    path: str, name_placeholder: str, project_template_path: str, skip_mkdir: bool = False
):
    normalized_path = os.path.normpath(path)
    code_location_name = os.path.basename(normalized_path).replace("-", "_")

    if not skip_mkdir:  # skip if the dir is created by previous command
        os.mkdir(normalized_path)

    loader = jinja2.FileSystemLoader(searchpath=project_template_path)
    env = jinja2.Environment(loader=loader)

    for root, dirs, files in os.walk(project_template_path):
        # For each subdirectory in the source template, create a subdirectory in the destination.
        for dirname in dirs:
            src_dir_path = os.path.join(root, dirname)
            if _should_skip_file(src_dir_path):
                continue

            src_relative_dir_path = os.path.relpath(src_dir_path, project_template_path)
            dst_relative_dir_path = src_relative_dir_path.replace(
                name_placeholder,
                code_location_name,
                1,
            )
            dst_dir_path = os.path.join(normalized_path, dst_relative_dir_path)

            os.mkdir(dst_dir_path)

        # For each file in the source template, render a file in the destination.
        for filename in files:
            src_file_path = os.path.join(root, filename)
            if _should_skip_file(src_file_path):
                continue

            src_relative_file_path = os.path.relpath(src_file_path, project_template_path)
            dst_relative_file_path = src_relative_file_path.replace(
                name_placeholder,
                code_location_name,
                1,
            )
            dst_file_path = os.path.join(normalized_path, dst_relative_file_path)

            if dst_file_path.endswith(".tmpl"):
                dst_file_path = dst_file_path[: -len(".tmpl")]

            with open(dst_file_path, "w", encoding="utf8") as f:
                # Jinja template names must use the POSIX path separator "/".
                template_name = src_relative_file_path.replace(os.sep, posixpath.sep)
                template = env.get_template(name=template_name)
                f.write(
                    template.render(
                        repo_name=code_location_name,  # deprecated
                        code_location_name=code_location_name,
                        dagster_version=dagster_version,
                    )
                )
                f.write("\n")


def _should_skip_file(path):
    """
    Given a file path `path` in a source template, returns whether or not the file should be skipped
    when generating destination files.

    Technically, `path` could also be a directory path that should be skipped.
    """
    for pattern in IGNORE_PATTERN_LIST:
        if pattern in path:
            return True

    return False
