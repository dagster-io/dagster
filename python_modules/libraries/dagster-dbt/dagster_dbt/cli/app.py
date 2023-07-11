import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

import typer
import yaml
from rich.console import Console
from rich.syntax import Syntax
from typing_extensions import Annotated

from ..include import STARTER_PROJECT_PATH
from ..version import __version__

app = typer.Typer(
    no_args_is_help=True,
    help="CLI tools for working with Dagster and dbt.",
    context_settings={
        "help_option_names": ["-h", "--help"],
    },
)
project_app = typer.Typer(no_args_is_help=True)
app.add_typer(
    project_app,
    name="project",
    help="Commands to initialize a new Dagster project with dbt.",
)

DBT_PROJECT_YML_NAME = "dbt_project.yml"
DAGSTER_DBT_PROJECT_DIR_NAME = "dagster"


def validate_dagster_project_name(ctx: typer.Context, project_name: Optional[str]) -> str:
    dbt_project_dir: Path = ctx.params["dbt_project_dir"]

    dbt_project_yaml_path = dbt_project_dir.joinpath(DBT_PROJECT_YML_NAME)
    with dbt_project_yaml_path.open() as fd:
        dbt_project_yaml = yaml.safe_load(fd)
        dbt_project_name: str = dbt_project_yaml["name"]

    project_name = project_name or dbt_project_name

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


@project_app.command(name="scaffold")
def project_scaffold_command(
    project_name: Annotated[
        Optional[str],
        typer.Option(
            default=...,
            show_default=False,
            help=(
                "The name of the Dagster project to initialize for your dbt project. By default, we"
                " use the name of your dbt project."
            ),
            callback=validate_dagster_project_name,
        ),
    ] = None,
    dbt_project_dir: Annotated[
        Path,
        typer.Option(
            default=...,
            help=(
                "The path of your dbt project directory. By default, we use the current"
                " working directory."
            ),
            callback=validate_dbt_project_dir,
            is_eager=True,
            exists=True,
            file_okay=False,
            dir_okay=True,
            writable=True,
            resolve_path=True,
        ),
    ] = Path.cwd(),
    generate_dbt_manifest: Annotated[
        bool,
        typer.Option(
            default=...,
            help="Create the dbt manifest.",
        ),
    ] = True,
) -> None:
    """This command will initialize a new Dagster project by creating directories and files that
    that loads assets from an existing dbt project.
    """
    console = Console()
    console.print(f"Running with dagster-dbt version: [bold green]{__version__}[/bold green].")

    console.print(
        f"Initializing Dagster project [bold green]{project_name}[/bold green] in dbt"
        f" project directory [bold green]{dbt_project_dir}[/bold green]"
    )

    dagster_dbt_project_dir = dbt_project_dir.joinpath(DAGSTER_DBT_PROJECT_DIR_NAME)

    shutil.copytree(src=STARTER_PROJECT_PATH, dst=dagster_dbt_project_dir)
    dagster_dbt_project_dir.joinpath("__init__.py").unlink()

    if generate_dbt_manifest:
        dbt_target_path = "target"
        dbt_manifest_target_path = dbt_project_dir.joinpath(dbt_target_path)
        with console.status(
            f"Generating dbt manifest in [bold green]{dbt_manifest_target_path}[/bold green]"
        ) as status:
            process = subprocess.Popen(
                [
                    "dbt",
                    "parse",
                    "--target-path",
                    dbt_target_path,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env={
                    **os.environ.copy(),
                    "DBT_LOG_FORMAT": "json",
                },
                cwd=dbt_project_dir,
            )

            for raw_line in process.stdout or []:
                log: str = raw_line.decode().strip()
                try:
                    raw_event: Dict[str, Any] = json.loads(log)
                    message = raw_event["info"]["msg"]

                    console.print(message)
                except:
                    console.print(log)

            process.wait()

            status.update("Finished generating dbt manifest.")

    console.print(
        "Your Dagster project has been initialized. To view your dbt project in Dagster, run"
        " the following commands:"
    )
    console.print(
        Syntax(
            code="\n".join(
                [
                    f"cd {dagster_dbt_project_dir}",
                    "dagster dev",
                ]
            ),
            lexer="bash",
            line_numbers=True,
            highlight_lines={1, 2},
            padding=1,
        )
    )
