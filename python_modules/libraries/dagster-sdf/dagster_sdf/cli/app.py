import os
import shutil
from pathlib import Path
from typing import Any

import typer
import yaml
from dagster._cli.project import check_if_pypi_package_conflict_exists
from jinja2 import Environment, FileSystemLoader
from rich.console import Console
from rich.syntax import Syntax
from typing_extensions import Annotated

from dagster_sdf.include import STARTER_PROJECT_PATH
from dagster_sdf.sdf_version import SDF_VERSION_UPPER_BOUND
from dagster_sdf.version import __version__ as dagster_sdf_version

app = typer.Typer(
    no_args_is_help=True,
    context_settings={
        "help_option_names": ["-h", "--help"],
    },
    help="CLI tools for working with Dagster and sdf.",
    add_completion=False,
)
workspace_app = typer.Typer(
    name="workspace",
    no_args_is_help=True,
    help="Commands for using an sdf workspace in Dagster.",
    add_completion=False,
)
app.add_typer(workspace_app)

console = Console()

SDF_WORKSPACE_YML_NAME = "workspace.sdf.yml"


def validate_dagster_workspace_name(workspace_name: str) -> str:
    if not workspace_name.isidentifier():
        raise typer.BadParameter(
            f"The workspace name `{workspace_name}` is not a valid sql identifier containing only"
            " letters, digits, or underscores. Please specify a valid project name."
        )

    return workspace_name


def validate_sdf_workspace_dir(sdf_workspace_dir: Path) -> Path:
    sdf_workspace_yaml_path = sdf_workspace_dir.joinpath(SDF_WORKSPACE_YML_NAME)

    if not sdf_workspace_yaml_path.exists():
        raise typer.BadParameter(
            f"{sdf_workspace_dir} does not contain a {SDF_WORKSPACE_YML_NAME} file. Please specify a"
            " valid path to an sdf workspace."
        )

    return sdf_workspace_dir


def find_workspace_block(documents: list) -> Any:
    for doc in documents:
        if "workspace" in doc:
            return doc["workspace"]
    return None


def copy_scaffold(
    workspace_name: str,
    dagster_project_dir: Path,
    sdf_workspace_dir: Path,
) -> None:
    sdf_workspace_yaml_path = sdf_workspace_dir.joinpath(SDF_WORKSPACE_YML_NAME)
    with sdf_workspace_yaml_path.open("rb") as file:
        sdf_workspace_yaml = list(yaml.safe_load_all(file))
    sdf_workspace_block = find_workspace_block(sdf_workspace_yaml)
    sdf_workspace_name: str = sdf_workspace_block["name"]

    shutil.copytree(
        src=STARTER_PROJECT_PATH,
        dst=dagster_project_dir,
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    dagster_project_dir.joinpath("__init__.py").unlink()

    sdf_workspace_dir_relative_path = Path(
        os.path.relpath(
            sdf_workspace_dir,
            start=dagster_project_dir.joinpath(workspace_name, "definitions.py"),
        )
    )
    sdf_workspace_dir_relative_path_parts = [
        f'"{part}"' for part in sdf_workspace_dir_relative_path.parts
    ]
    env = Environment(loader=FileSystemLoader(dagster_project_dir))

    for path in dagster_project_dir.glob("**/*"):
        if path.suffix == ".jinja":
            relative_path = path.relative_to(Path.cwd())
            destination_path = os.fspath(relative_path.parent.joinpath(relative_path.stem))
            template_path = path.relative_to(dagster_project_dir).as_posix()

            env.get_template(template_path).stream(
                sdf_workspace_dir_relative_path_parts=sdf_workspace_dir_relative_path_parts,
                sdf_workspace_name=f"{sdf_workspace_name}_project",
                sdf_assets_name=f"{sdf_workspace_name}_sdf_assets",
                sdf_version_upper_bound=SDF_VERSION_UPPER_BOUND,
                workspace_name=workspace_name,
            ).dump(destination_path)

            path.unlink()

    dagster_project_dir.joinpath("scaffold").rename(dagster_project_dir.joinpath(workspace_name))


def _check_and_error_on_package_conflicts(workspace_name: str) -> None:
    package_check_result = check_if_pypi_package_conflict_exists(workspace_name)
    if package_check_result.request_error_msg:
        console.print(
            f"An error occurred while checking if workspace name '{workspace_name}' conflicts with"
            f" an existing PyPI package: {package_check_result.request_error_msg}."
            " \n\nConflicting package names will cause import errors in your project if the"
            " existing PyPI package is included as a dependency in your scaffolded project. If"
            " desired, this check can be skipped by adding the `--ignore-package-conflict`"
            " flag."
        )
        raise typer.Exit(1)

    if package_check_result.conflict_exists:
        raise typer.BadParameter(
            f"The workspace name '{workspace_name}' conflicts with an existing PyPI package."
            " Conflicting package names will cause import errors in your project if the"
            " existing PyPI package is included as a dependency in your scaffolded project."
            " Please choose another name, or add the `--ignore-package-conflict` flag to"
            " bypass this check."
        )


@workspace_app.command(name="scaffold")
def project_scaffold_command(
    project_name: Annotated[
        str,
        typer.Option(
            default=...,
            callback=validate_dagster_workspace_name,
            show_default=False,
            prompt="Enter a name for your Dagster project (letters, digits, underscores)",
            help="The name of the Dagster project to initialize for your sdf workspace.",
        ),
    ],
    sdf_workspace_dir: Annotated[
        Path,
        typer.Option(
            default=...,
            callback=validate_sdf_workspace_dir,
            show_default=False,
            help=(
                "The path of your sdf workspace directory. This path must contain a workspace.sdf.yml"
                " file. By default, this command will assume that the current working directory"
                " contains an sdf workspace, but you can set a different directory by setting this"
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
            help="Controls whether the workspace name can conflict with an existing PyPI package.",
            is_flag=True,
            hidden=True,
        ),
    ] = False,
) -> None:
    """This command will initialize a new Dagster project and create directories and files that
    load assets from an existing sdf workspace.
    """
    if not ignore_package_conflict:
        _check_and_error_on_package_conflicts(project_name)

    console.print(
        f"Running with dagster-sdf version: [bold green]{dagster_sdf_version}[/bold green]."
    )
    console.print(
        f"Initializing Dagster project [bold green]{project_name}[/bold green] in the current"
        f" working directory for sdf workspace directory [bold green]{sdf_workspace_dir}[/bold green].",
    )

    dagster_project_dir = Path.cwd().joinpath(project_name)

    copy_scaffold(
        workspace_name=project_name,
        dagster_project_dir=dagster_project_dir,
        sdf_workspace_dir=sdf_workspace_dir,
    )

    dagster_dev_command = "DAGSTER_SDF_COMPILE_ON_LOAD=1 dagster dev"

    console.print(
        "Your Dagster project has been initialized. To view your sdf workspace in Dagster, run"
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


project_app_typer_click_object = typer.main.get_command(workspace_app)
