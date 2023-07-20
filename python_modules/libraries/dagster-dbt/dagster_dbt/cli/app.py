import os
import shutil
from pathlib import Path
from typing import Any, Dict

import typer
import yaml
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
project_app = typer.Typer(no_args_is_help=True)
app.add_typer(
    project_app,
    name="project",
    help="Commands to initialize a new Dagster project with an existing dbt project.",
)

DBT_PROJECT_YML_NAME = "dbt_project.yml"


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


def copy_scaffold(
    project_name: str,
    dagster_project_dir: Path,
    dbt_project_dir: Path,
) -> None:
    shutil.copytree(src=STARTER_PROJECT_PATH, dst=dagster_project_dir)
    dagster_project_dir.joinpath("__init__.py").unlink()

    dbt_project_yaml_path = dbt_project_dir.joinpath(DBT_PROJECT_YML_NAME)
    with dbt_project_yaml_path.open() as fd:
        dbt_project_yaml: Dict[str, Any] = yaml.safe_load(fd)
        dbt_project_name: str = dbt_project_yaml["name"]

    dbt_project_dir_relative_path = Path(
        os.path.relpath(
            dbt_project_dir,
            start=dagster_project_dir.joinpath(project_name),
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
            template_path = os.fspath(path.relative_to(dagster_project_dir))

            env.get_template(template_path).stream(
                dbt_project_dir_relative_path_parts=dbt_project_dir_relative_path_parts,
                dbt_project_name=dbt_project_name,
                dbt_parse_command=dbt_parse_command,
                dbt_assets_name=f"{dbt_project_name}_dbt_assets",
                project_name=project_name,
            ).dump(destination_path)

            path.unlink()

    dagster_project_dir.joinpath("scaffold").rename(dagster_project_dir.joinpath(project_name))


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
            is_eager=True,
            help=(
                "The path of your dbt project directory. By default, we use the current"
                " working directory."
            ),
            exists=True,
            file_okay=False,
            dir_okay=True,
            writable=True,
            resolve_path=True,
        ),
    ] = Path.cwd(),
) -> None:
    """This command will initialize a new Dagster project and create directories and files that
    load assets from an existing dbt project.
    """
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
    )

    console.print(
        (
            "Your Dagster project has been initialized. To view your dbt project in Dagster, run"
            " the following commands:"
        ),
        Syntax(
            code="\n".join(
                [
                    f"cd '{dbt_project_dir}' \\",
                    "  && dbt parse --target-path target \\",
                    f"  && cd '{dagster_project_dir}' \\",
                    "  && dagster dev",
                ]
            ),
            lexer="bash",
            padding=1,
        ),
    )
