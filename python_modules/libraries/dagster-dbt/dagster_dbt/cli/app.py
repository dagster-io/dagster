import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any

import typer
import yaml
from dagster._cli.project import check_if_pypi_package_conflict_exists
from dagster._core.code_pointer import load_python_file
from dagster._core.definitions.module_loaders.load_assets_from_modules import (
    find_objects_in_module_of_types,
)
from jinja2 import Environment, FileSystemLoader
from rich.console import Console
from rich.syntax import Syntax

from dagster_dbt.dbt_core_version import DBT_CORE_VERSION_UPPER_BOUND
from dagster_dbt.dbt_project import DbtProject
from dagster_dbt.include import STARTER_PROJECT_PATH
from dagster_dbt.version import __version__ as dagster_dbt_version

if TYPE_CHECKING:
    from collections.abc import Iterator

app = typer.Typer(
    no_args_is_help=True,
    context_settings={
        "help_option_names": ["-h", "--help"],
    },
    help="CLI tools for working with Dagster and dbt.",
    add_completion=False,
)
project_app = typer.Typer(
    name="project",
    no_args_is_help=True,
    help="Commands for using a dbt project in Dagster.",
    add_completion=False,
)
app.add_typer(project_app)

console = Console()

DBT_PROJECT_YML_NAME = "dbt_project.yml"
DBT_PROFILES_YML_NAME = "profiles.yml"


def validate_dagster_project_name(project_name: str) -> str:
    if not project_name.isidentifier():
        raise typer.BadParameter(
            f"The project name `{project_name}` is not a valid Python identifier containing only"
            " letters, digits, or underscores. Please specify a valid project name."
        )

    return project_name


def validate_dbt_project_dir(dbt_project_dir: Path) -> Path:
    dbt_project_yaml_path = dbt_project_dir.joinpath(DBT_PROJECT_YML_NAME)

    if not dbt_project_yaml_path.exists():
        raise typer.BadParameter(
            f"{dbt_project_dir} does not contain a {DBT_PROJECT_YML_NAME} file. Please specify a"
            " valid path to a dbt project."
        )

    return dbt_project_dir


def find_dbt_profiles_path(dbt_project_dir: Path) -> Path:
    dot_dbt_dir = Path.home().joinpath(".dbt")

    candidate_dbt_profiles_paths = [
        # profiles.yml in project directory
        dbt_project_dir.joinpath(DBT_PROFILES_YML_NAME),
        # profiles.yml in ~/.dbt
        dot_dbt_dir.joinpath(DBT_PROFILES_YML_NAME),
    ]
    existing_profiles_paths = [path for path in candidate_dbt_profiles_paths if path.exists()]

    if not existing_profiles_paths:
        console.print(
            f"A {DBT_PROFILES_YML_NAME} file was not found in either {dbt_project_dir} or "
            f"{dot_dbt_dir}. Please ensure that a valid {DBT_PROFILES_YML_NAME} exists in your "
            "environment."
        )
        raise typer.Exit(1)

    dbt_profiles_path, *_ = existing_profiles_paths

    console.print(
        f"Using {DBT_PROFILES_YML_NAME} found in [bold green]{dbt_profiles_path}[/bold green]."
    )

    return dbt_profiles_path


def dbt_adapter_pypi_package_for_target_type(target_type: str) -> str:
    """See https://docs.getdbt.com/docs/connect-adapters for a list of dbt adapter packages."""
    custom_pypi_package_by_target_type = {
        "athena": "dbt-athena-adapter",
        "layer": "dbt-layer-bigquery",
    }
    dbt_adapter_pypi_package = custom_pypi_package_by_target_type.get(
        target_type, f"dbt-{target_type}"
    )

    return dbt_adapter_pypi_package


def copy_scaffold(
    project_name: str,
    dagster_project_dir: Path,
    dbt_project_dir: Path,
    use_experimental_dbt_state: bool,
) -> None:
    dbt_project_yaml_path = dbt_project_dir.joinpath(DBT_PROJECT_YML_NAME)
    dbt_project_yaml: dict[str, Any] = yaml.safe_load(dbt_project_yaml_path.read_bytes())
    dbt_project_name: str = dbt_project_yaml["name"]

    dbt_profiles_path = find_dbt_profiles_path(dbt_project_dir=dbt_project_dir)
    dbt_profiles_yaml: dict[str, Any] = yaml.safe_load(dbt_profiles_path.read_bytes())

    # Remove config from profiles.yml
    dbt_profiles_yaml.pop("config", None)

    dbt_adapter_packages = [
        dbt_adapter_pypi_package_for_target_type(target["type"])
        for profile in dbt_profiles_yaml.values()
        for target in profile["outputs"].values()
    ]

    shutil.copytree(
        src=STARTER_PROJECT_PATH,
        dst=dagster_project_dir,
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    dagster_project_dir.joinpath("__init__.py").unlink()

    dbt_project_dir_relative_path = Path(
        os.path.relpath(
            dbt_project_dir,
            start=dagster_project_dir.joinpath(project_name, "definitions.py"),
        )
    )
    dbt_project_dir_relative_path_parts = [
        f'"{part}"' for part in dbt_project_dir_relative_path.parts
    ]
    dbt_parse_command = ['"--quiet", "parse"']

    env = Environment(loader=FileSystemLoader(dagster_project_dir))

    for path in dagster_project_dir.glob("**/*"):
        if path.suffix == ".jinja":
            relative_path = path.relative_to(Path.cwd())
            destination_path = os.fspath(relative_path.parent.joinpath(relative_path.stem))
            template_path = path.relative_to(dagster_project_dir).as_posix()

            env.get_template(template_path).stream(
                dbt_project_dir_relative_path_parts=dbt_project_dir_relative_path_parts,
                dbt_project_name=f"{dbt_project_name}_project",
                dbt_parse_command=dbt_parse_command,
                dbt_assets_name=f"{dbt_project_name}_dbt_assets",
                dbt_adapter_packages=dbt_adapter_packages,
                dbt_core_version_upper_bound=DBT_CORE_VERSION_UPPER_BOUND,
                project_name=project_name,
                use_experimental_dbt_state=use_experimental_dbt_state,
            ).dump(destination_path)

            path.unlink()

    dagster_project_dir.joinpath("scaffold").rename(dagster_project_dir.joinpath(project_name))


def _check_and_error_on_package_conflicts(project_name: str) -> None:
    package_check_result = check_if_pypi_package_conflict_exists(project_name)
    if package_check_result.request_error_msg:
        console.print(
            f"An error occurred while checking if project name '{project_name}' conflicts with"
            f" an existing PyPI package: {package_check_result.request_error_msg}."
            " \n\nConflicting package names will cause import errors in your project if the"
            " existing PyPI package is included as a dependency in your scaffolded project. If"
            " desired, this check can be skipped by adding the `--ignore-package-conflict`"
            " flag."
        )
        raise typer.Exit(1)

    if package_check_result.conflict_exists:
        raise typer.BadParameter(
            f"The project name '{project_name}' conflicts with an existing PyPI package."
            " Conflicting package names will cause import errors in your project if the"
            " existing PyPI package is included as a dependency in your scaffolded project."
            " Please choose another name, or add the `--ignore-package-conflict` flag to"
            " bypass this check."
        )


@project_app.command(name="scaffold")
def project_scaffold_command(
    project_name: Annotated[
        str,
        typer.Option(
            default=...,
            callback=validate_dagster_project_name,
            show_default=False,
            prompt="Enter a name for your Dagster project (letters, digits, underscores)",
            help="The name of the Dagster project to initialize for your dbt project.",
        ),
    ],
    dbt_project_dir: Annotated[
        Path,
        typer.Option(
            default=...,
            callback=validate_dbt_project_dir,
            show_default=False,
            help=(
                "The path of your dbt project directory. This path must contain a dbt_project.yml"
                " file. By default, this command will assume that the current working directory"
                " contains a dbt project, but you can set a different directory by setting this"
                " option."
            ),
            exists=True,
            file_okay=False,
            dir_okay=True,
            writable=True,
            resolve_path=True,
        ),
    ] = Path.cwd(),
    ignore_package_conflict: Annotated[
        bool,
        typer.Option(
            default=...,
            help="Controls whether the project name can conflict with an existing PyPI package.",
            is_flag=True,
            hidden=True,
        ),
    ] = False,
    use_experimental_dbt_state: Annotated[
        bool,
        typer.Option(
            default=...,
            help="Controls whether `DbtProject` is used with dbt state.",
            is_flag=True,
            hidden=True,
        ),
    ] = False,
) -> None:
    """This command will initialize a new Dagster project and create directories and files that
    load assets from an existing dbt project.
    """
    if not ignore_package_conflict:
        _check_and_error_on_package_conflicts(project_name)

    console.print(
        f"Running with dagster-dbt version: [bold green]{dagster_dbt_version}[/bold green]."
    )
    console.print(
        f"Initializing Dagster project [bold green]{project_name}[/bold green] in the current"
        f" working directory for dbt project directory [bold green]{dbt_project_dir}[/bold green].",
    )

    dagster_project_dir = Path.cwd().joinpath(project_name)

    copy_scaffold(
        project_name=project_name,
        dagster_project_dir=dagster_project_dir,
        dbt_project_dir=dbt_project_dir,
        use_experimental_dbt_state=use_experimental_dbt_state,
    )

    dagster_dev_command = "dagster dev"

    console.print(
        "Your Dagster project has been initialized. To view your dbt project in Dagster, run"
        " the following commands:",
        Syntax(
            code="\n".join(
                [
                    f"cd '{dagster_project_dir}'",
                    dagster_dev_command,
                ]
            ),
            lexer="bash",
            padding=1,
        ),
    )


def prepare_and_package(project: DbtProject) -> None:
    """A method that can be called as part of the deployment process."""
    if project.preparer:
        console.print(
            f"Preparing project [bold green]{project.project_dir}[/bold green] for deployment with [bold green]{project.preparer.prepare.__qualname__}[/bold green]."
        )
        project.preparer.prepare(project)
        console.print("Project preparation complete.")

    if project.packaged_project_dir:
        sync_project_to_packaged_dir(project)


def sync_project_to_packaged_dir(
    project: DbtProject,
) -> None:
    """Sync a `DbtProject`s `project_dir` directory to its `packaged_project_dir`."""
    if project.packaged_project_dir is None:
        raise Exception(
            "sync_project_to_packaged_dir should only be called if `packaged_project_dir` is set."
        )

    console.print(
        "Syncing project to package data directory"
        f" [bold green]{project.packaged_project_dir}[/bold green]."
    )
    if project.packaged_project_dir.exists():
        console.print(
            f"Removing existing contents at [bold red]{project.packaged_project_dir}[/bold red]."
        )
        shutil.rmtree(project.packaged_project_dir)

    # Determine if the package data dir is within the project dir, and ignore
    # that path if so.
    rel_path = Path(os.path.relpath(project.packaged_project_dir, project.project_dir))
    rel_ignore = ""
    if len(rel_path.parts) > 0 and rel_path.parts[0] != "..":
        rel_ignore = rel_path.parts[0]

    console.print(
        f"Copying [bold green]{project.project_dir}[/bold green] to"
        f" [bold green]{project.packaged_project_dir}[/bold green]."
    )
    shutil.copytree(
        src=project.project_dir,
        dst=project.packaged_project_dir,
        ignore=shutil.ignore_patterns(
            "*.git*",
            "*partial_parse.msgpack",
            rel_ignore,
        ),
    )
    console.print("Sync complete.")


@project_app.command(name="prepare-for-deployment", hidden=True)
@project_app.command(name="prepare-and-package")
def project_prepare_and_package_command(
    file: Annotated[
        str,
        typer.Option(
            help="The file containing DbtProject definitions to prepare.",
        ),
    ],
) -> None:
    """This command will invoke ``prepare_and_package`` on :py:class:`DbtProject` found in the target module or file.
    Note that this command runs `dbt deps` and `dbt parse`.
    """
    console.print(
        f"Running with dagster-dbt version: [bold green]{dagster_dbt_version}[/bold green]."
    )

    contents = load_python_file(file, working_directory=None)
    dbt_projects: Iterator[DbtProject] = find_objects_in_module_of_types(contents, types=DbtProject)
    for project in dbt_projects:
        prepare_and_package(project)


project_app_typer_click_object = typer.main.get_command(project_app)
