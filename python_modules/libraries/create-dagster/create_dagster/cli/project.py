import contextlib
import os
import shutil
import subprocess
import sys
import textwrap
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Literal, Optional, Union

import click
from dagster_shared.scaffold import scaffold_subtree
from dagster_shared.toml import modify_toml, set_toml_node
from dagster_shared.utils import get_shortest_path_repr, get_venv_activation_cmd

# ########################
# ##### PROJECT
# ########################

CreateProjectPythonEnvironmentFlag = Literal["active", "uv_managed"]


def exit_with_error(error_message: str) -> None:
    click.echo(click.style(error_message, fg="red"))
    sys.exit(1)


def format_multiline_str(message: str) -> str:
    # width=10000 unwraps any hardwrapping
    dedented = textwrap.dedent(message).strip()
    paragraphs = [textwrap.fill(p, width=10000) for p in dedented.split("\n\n")]
    return "\n\n".join(paragraphs)


def strip_activated_venv_from_env_vars(env: Mapping[str, str]) -> Mapping[str, str]:
    return {k: v for k, v in env.items() if not k == "VIRTUAL_ENV"}


def is_uv_installed() -> bool:
    return shutil.which("uv") is not None


def _print_package_install_warning_message() -> None:
    pip_install_cmd = "pip install --editable ."
    uv_install_cmd = "uv sync"
    click.secho(
        format_multiline_str(
            f"""
            The environment used for your project must include an installation of your project
            package. Please run `{uv_install_cmd}` (for uv) or `{pip_install_cmd}` (for pip) before
            running `dg` commands against your project.
        """,
        ),
        fg="yellow",
    )


@contextlib.contextmanager
def pushd(path: Union[str, Path]) -> Iterator[None]:
    old_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_cwd)


def _ensure_uv_lock(path: Path) -> None:
    if not (path / "uv.lock").exists():
        _ensure_uv_sync(path)


def _ensure_uv_sync(path: Path) -> None:
    with pushd(path):
        if not (path / "uv.lock").exists():
            subprocess.check_output(
                ["uv", "sync"],
                env=strip_activated_venv_from_env_vars(os.environ),
            )


def _should_run_uv_sync(
    python_environment: CreateProjectPythonEnvironmentFlag,
    venv_path: Path,
    uv_sync_flag: Optional[bool],
) -> bool:
    # This already will have occurred during the scaffolding step
    if python_environment == "uv_managed" or uv_sync_flag is False:
        return False
    # This can force running `uv sync` even if a venv already exists
    elif uv_sync_flag is True:
        return True
    elif venv_path.exists():
        _print_package_install_warning_message()
        return False
    elif is_uv_installed():  # uv_sync_flag is unset (None)
        response = click.prompt(
            format_multiline_str("""
            Run uv sync? This will create the virtual environment you need to activate in
            order to work on this project. (y/n)
        """),
            default="y",
        ).lower()
        if response not in ("y", "n"):
            exit_with_error(f"Invalid response '{response}'. Please enter 'y' or 'n'.")
        if response == "n":
            _print_package_install_warning_message()
        return response == "y"
    else:
        return False


@click.command(name="project")
@click.argument("path", type=click.Path(exists=False, path_type=Path))
@click.option("--use-editable-dagster", is_flag=True)
@click.option("--python-environment", type=click.Choice(["active", "uv_managed"]), default="active")
@click.option(
    "--uv-sync/--no-uv-sync",
    is_flag=True,
    default=None,
    help="""
        Preemptively answer the "Run uv sync?" prompt presented after project initialization.
    """.strip(),
)
def project_command(
    path: Path,
    python_environment: CreateProjectPythonEnvironmentFlag,
    use_editable_dagster: bool = False,
    uv_sync: Optional[bool] = None,
) -> None:
    """Scaffold a new Dagster project at PATH. The name of the project will be the final component of PATH.

    "." may be passed as PATH to create the new project inside the existing working directory.

    Examples:
        dagster-create project PROJECT_NAME
            Scaffold a new project in new directory PROJECT_NAME. Automatically creates directory
            and parent directories.
        dagster-create project .
            Scaffold a new project in the CWD. The project name is taken from the last component of the CWD.

    Created projects will have the following structure:

    ├── src
    │   └── <project_name>
    │       ├── __init__.py
    │       ├── definitions.py
    │       ├── defs
    │       │   └── __init__.py
    │       └── lib
    │           └── __init__.py
    ├── tests
    │   └── __init__.py
    └── pyproject.toml

    The `src.<project_name>.defs` directory holds Python objects that can be targeted by the
    `dg scaffold` command or have dg-inspectable metadata. Custom component types in the project
    live in `src.<project_name>.lib`. These types can be created with `dg scaffold component`.
    """
    if python_environment == "uv_managed" and not is_uv_installed():
        exit_with_error("""
            uv is not installed. Please install uv to use the `--python-environment uv_managed` option.
            See https://docs.astral.sh/uv/getting-started/installation/.
        """)

    abs_path = path.resolve()
    if str(path) != "." and abs_path.exists():
        exit_with_error(f"A file or directory already exists at {abs_path}.")

    path = abs_path

    click.echo(f"Creating a Dagster project at {path}.")

    if use_editable_dagster:
        editable_dagster_root = (
            _get_editable_dagster_from_env()
            if use_editable_dagster is True
            else use_editable_dagster
        )
        deps = EDITABLE_DAGSTER_DEPENDENCIES
        dev_deps = EDITABLE_DAGSTER_DEV_DEPENDENCIES
        sources = _gather_dagster_packages(Path(editable_dagster_root))
    else:
        editable_dagster_root = None
        deps = PYPI_DAGSTER_DEPENDENCIES
        dev_deps = PYPI_DAGSTER_DEV_DEPENDENCIES
        sources = []

    dependencies_str = _get_pyproject_toml_dependencies(deps)
    dev_dependencies_str = _get_pyproject_toml_dev_dependencies(dev_deps)
    uv_sources_str = _get_pyproject_toml_uv_sources(sources) if sources else ""

    scaffold_subtree(
        path=path,
        name_placeholder="PROJECT_NAME_PLACEHOLDER",
        project_template_path=Path(
            os.path.join(os.path.dirname(__file__), "..", "templates", "PROJECT_NAME_PLACEHOLDER")
        ).resolve(),
        dependencies=dependencies_str,
        dev_dependencies=dev_dependencies_str,
        uv_sources=uv_sources_str,
    )
    click.echo(f"Scaffolded files for Dagster project at {path}.")

    if python_environment:
        with modify_toml(path / "pyproject.toml") as toml:
            python_environment_dict = (
                {"active": True} if python_environment == "active" else {"uv_managed": True}
            )
            used_key = next((k for k, v in python_environment_dict.items() if v), None)
            if used_key:
                set_toml_node(toml, ("project", "python_environment"), {})
                set_toml_node(
                    toml,
                    ("project", "python_environment", used_key),
                    python_environment_dict[used_key],
                )

    # Build the venv
    if python_environment == "uv_managed":
        _ensure_uv_lock(path)

    venv_path = path / ".venv"
    if _should_run_uv_sync(python_environment, venv_path, uv_sync):
        click.echo("Running `uv sync --group dev`...")
        with pushd(path):
            subprocess.run(["uv", "sync", "--group", "dev"], check=True)

        click.echo("\nuv.lock and virtual environment created.")
        display_venv_path = get_shortest_path_repr(venv_path)
        click.echo(
            f"""
            Run `{get_venv_activation_cmd(display_venv_path)}` to activate your project's virtual environment.
            """.strip()
        )


# Despite the fact that editable dependencies are resolved through tool.uv.sources, we need to set
# the dependencies themselves differently depending on whether we are using editable dagster or
# not. This is because `tool.uv.sources` only seems to apply to direct dependencies of the package,
# so any 2+-order Dagster dependency of our package needs to be listed as a direct dependency in the
# editable case. See: https://github.com/astral-sh/uv/issues/9446
EDITABLE_DAGSTER_DEPENDENCIES = (
    "dagster",
    "dagster-pipes",
    "dagster-shared",
    "dagster-test",  # we include dagster-test for testing purposes
)
EDITABLE_DAGSTER_DEV_DEPENDENCIES = (
    "dagster-webserver",
    "dagster-graphql",
    "dagster-dg",
    "dagster-cloud-cli",
)
PYPI_DAGSTER_DEPENDENCIES = ("dagster",)
PYPI_DAGSTER_DEV_DEPENDENCIES = (
    "dagster-webserver",
    "dagster-dg",
)


def _get_editable_dagster_from_env() -> str:
    if not os.environ.get("DAGSTER_GIT_REPO_DIR"):
        exit_with_error(
            "The `--use-editable-dagster` option "
            "requires the `DAGSTER_GIT_REPO_DIR` environment variable to be set."
        )
    return os.environ["DAGSTER_GIT_REPO_DIR"]


def _get_pyproject_toml_dependencies(deps: tuple[str, ...]) -> str:
    return "\n".join(
        [
            "dependencies = [",
            *[f'    "{dep}",' for dep in deps],
            "]",
        ]
    )


def _get_pyproject_toml_dev_dependencies(deps: tuple[str, ...]) -> str:
    return "\n".join(
        [
            "dev = [",
            *[f'    "{dep}",' for dep in deps],
            "]",
        ]
    )


def _get_pyproject_toml_uv_sources(lib_paths: list[Path]) -> str:
    lib_lines = [f"{path.name} = {{ path = '{path}', editable = true }}" for path in lib_paths]
    return "\n".join(
        [
            "[tool.uv.sources]",
            *lib_lines,
        ]
    )


def _gather_dagster_packages(editable_dagster_root: Path) -> list[Path]:
    return [
        p.parent
        for p in (
            *editable_dagster_root.glob("python_modules/dagster*/setup.py"),
            *editable_dagster_root.glob("python_modules/libraries/dagster*/setup.py"),
        )
    ]


DEFAULT_WORKSPACE_NAME = "dagster-workspace"


@click.command(name="workspace")
@click.argument("name", type=str, default=DEFAULT_WORKSPACE_NAME)
@click.option("--use-editable-dagster", is_flag=True)
def workspace_command(
    name: str,
    use_editable_dagster: bool = False,
):
    """Initialize a new Dagster workspace.

    Examples:
        dg scaffold workspace WORKSPACE_NAME
            Scaffold a new workspace in new directory WORKSPACE_NAME. Automatically creates directory
            and parent directories.
        dg scaffold workspace .
            Scaffold a new workspace in the CWD. The workspace name is the last component of the CWD.

    The scaffolded workspace folder has the following structure:

    ├── <workspace_name>
    │   ├── projects
    |   |   └── <Dagster projects go here>
    │   └── dg.toml

    """
    new_workspace_path = Path.cwd() if name == "." else Path.cwd() / name
    if name != "." and new_workspace_path.exists():
        exit_with_error(f"Folder already exists at {new_workspace_path}.")

    scaffold_subtree(
        path=new_workspace_path,
        name_placeholder="WORKSPACE_NAME_PLACEHOLDER",
        project_template_path=Path(
            os.path.join(os.path.dirname(__file__), "..", "templates", "WORKSPACE_NAME_PLACEHOLDER")
        ).resolve(),
    )
    click.echo(f"Scaffolded files for Dagster workspace at {new_workspace_path}.")
    return new_workspace_path
