import os
import shutil
from pathlib import Path
from typing import Any, Dict

import typer
import yaml
from dagster._cli.project import check_if_pypi_package_conflict_exists
from dbt.version import __version__ as dbt_version
from jinja2 import Environment, FileSystemLoader
from packaging import version
from rich.console import Console
from rich.syntax import Syntax
from typing_extensions import Annotated

from ..include import STARTER_PROJECT_PATH
from ..version import __version__ as dagster_dbt_version

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
    help="Commands to initialize a new Dagster project with an existing dbt project.",
    add_completion=False,
)
app.add_typer(project_app)

DBT_PROJECT_YML_NAME = "dbt_project.yml"
DBT_PROFILES_YML_NAME = "profiles.yml"


def validate_dagster_project_name(project_name: str) -> str:
    if not project_name.isidentifier():
        raise typer.BadParameter(
            "The project name must be a valid Python identifier containing only letters, digits, or"
            " underscores."
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
    use_dbt_project_package_data_dir: bool,
) -> None:
    shutil.copytree(src=STARTER_PROJECT_PATH, dst=dagster_project_dir)
    dagster_project_dir.joinpath("__init__.py").unlink()

    dbt_project_yaml_path = dbt_project_dir.joinpath(DBT_PROJECT_YML_NAME)
    dbt_project_yaml: Dict[str, Any] = yaml.safe_load(dbt_project_yaml_path.read_bytes())
    dbt_project_name: str = dbt_project_yaml["name"]

    dbt_profiles_path = dbt_project_dir.joinpath(DBT_PROFILES_YML_NAME)
    dbt_profiles_yaml: Dict[str, Any] = yaml.safe_load(dbt_profiles_path.read_bytes())

    # Remove config from profiles.yml
    dbt_profiles_yaml.pop("config", None)

    dbt_adapter_packages = [
        dbt_adapter_pypi_package_for_target_type(target["type"])
        for profile in dbt_profiles_yaml.values()
        for target in profile["outputs"].values()
    ]

    if use_dbt_project_package_data_dir:
        dbt_project_dir = dagster_project_dir.joinpath("dbt-project")

    dbt_project_dir_relative_path = Path(
        os.path.relpath(
            dbt_project_dir,
            start=dagster_project_dir.joinpath(project_name, "definitions.py"),
        )
    )
    dbt_project_dir_relative_path_parts = [
        f'"{part}"' for part in dbt_project_dir_relative_path.parts
    ]

    dbt_parse_command = ['"parse"']
    if version.parse(dbt_version) < version.parse("1.5.0"):
        dbt_parse_command += ['"--write-manifest"']

    env = Environment(loader=FileSystemLoader(dagster_project_dir))

    for path in dagster_project_dir.glob("**/*"):
        if path.suffix == ".jinja":
            relative_path = path.relative_to(Path.cwd())
            destination_path = os.fspath(relative_path.parent.joinpath(relative_path.stem))
            template_path = path.relative_to(dagster_project_dir).as_posix()

            env.get_template(template_path).stream(
                dbt_project_dir_relative_path_parts=dbt_project_dir_relative_path_parts,
                dbt_project_name=dbt_project_name,
                dbt_parse_command=dbt_parse_command,
                dbt_assets_name=f"{dbt_project_name}_dbt_assets",
                dbt_adapter_packages=dbt_adapter_packages,
                project_name=project_name,
                use_dbt_project_package_data_dir=use_dbt_project_package_data_dir,
            ).dump(destination_path)

            path.unlink()

    dagster_project_dir.joinpath("scaffold").rename(dagster_project_dir.joinpath(project_name))


def _check_and_error_on_package_conflicts(project_name: str) -> None:
    package_check_result = check_if_pypi_package_conflict_exists(project_name)
    if package_check_result.request_error_msg:
        typer.echo(
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
    use_dbt_project_package_data_dir: Annotated[
        bool,
        typer.Option(
            default=...,
            help="Controls whether the dbt project package data directory is used.",
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

    console = Console()
    console.print(
        f"Running with dagster-dbt version: [bold green]{dagster_dbt_version}[/bold green]."
    )
    console.print(
        f"Initializing Dagster project [bold green]{project_name}[/bold green] in the current"
        f" working directory for dbt project directory [bold green]{dbt_project_dir}[/bold green]"
    )

    dagster_project_dir = Path.cwd().joinpath(project_name)

    copy_scaffold(
        project_name=project_name,
        dagster_project_dir=dagster_project_dir,
        dbt_project_dir=dbt_project_dir,
        use_dbt_project_package_data_dir=use_dbt_project_package_data_dir,
    )

    console.print(
        "Your Dagster project has been initialized. To view your dbt project in Dagster, run"
        " the following commands:",
        Syntax(
            code="\n".join(
                [
                    f"cd '{dagster_project_dir}'",
                    "DAGSTER_DBT_PARSE_PROJECT_ON_LOAD=1 dagster dev",
                ]
            ),
            lexer="bash",
            padding=1,
        ),
    )


project_app_typer_click_object = typer.main.get_command(project_app)
