import os
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

import click
from dagster_dg_core.config import DgWorkspaceScaffoldProjectOptions, modify_dg_toml_config
from dagster_dg_core.context import DgContext
from dagster_dg_core.utils import exit_with_error, get_toml_node, has_toml_node, set_toml_node
from dagster_shared.libraries import parse_package_version
from dagster_shared.scaffold import scaffold_subtree


def scaffold_workspace(
    path: Path,
    use_editable_dagster: bool,
) -> None:
    scaffold_subtree(
        path=path,
        name_placeholder="WORKSPACE_NAME_PLACEHOLDER",
        project_template_path=Path(
            os.path.join(os.path.dirname(__file__), "templates", "WORKSPACE_NAME_PLACEHOLDER")
        ),
        excludes=None,
        **get_dependencies_template_params(
            use_editable_dagster,
            scaffold_project_options=None,
            pypi_deps=_get_pypi_local_workspace_environment_deps(),
            # add create-dagster to editable installs so you can scaffold projects in the
            # workspace editable venv, since if you are installing editably you probably have
            # create-dagster installed in your current venv editably
            editable_deps=(
                EDITABLE_DAGSTER_DEPENDENCIES
                + EDITABLE_DAGSTER_DEV_DEPENDENCIES
                + ["create-dagster"]
            ),
            pypi_dev_deps=[],  # no dev extra
            editable_dev_deps=[],
        ),
    )

    if use_editable_dagster:
        with modify_dg_toml_config(path / "dg.toml") as toml:
            set_toml_node(toml, ("workspace", "scaffold_project_options"), {})
            set_toml_node(
                toml,
                ("workspace", "scaffold_project_options", "use_editable_dagster"),
                True if use_editable_dagster == "TRUE" else use_editable_dagster,
            )


def get_dependencies_template_params(
    use_editable_dagster: bool,
    scaffold_project_options: Optional[DgWorkspaceScaffoldProjectOptions],
    *,
    editable_deps: list[str],
    editable_dev_deps: list[str],
    pypi_deps: list[str],
    pypi_dev_deps: list[str],
) -> dict[str, str]:
    cli_options = DgWorkspaceScaffoldProjectOptions.get_raw_from_cli(use_editable_dagster)

    final_use_editable_dagster = cli_options.get(
        "use_editable_dagster",
        scaffold_project_options.use_editable_dagster if scaffold_project_options else None,
    )
    if final_use_editable_dagster:
        deps = editable_deps
        dev_deps = editable_dev_deps
        sources = _gather_dagster_packages(Path(_get_editable_dagster_from_env()))
    else:
        dev_deps = pypi_dev_deps
        deps = pypi_deps
        sources = []

    dependencies_str = _get_pyproject_toml_dependencies(deps)
    dev_dependencies_str = _get_pyproject_toml_dev_dependencies(dev_deps)
    uv_sources_str = _get_pyproject_toml_uv_sources(sources) if sources else ""

    return {
        "dependencies": dependencies_str,
        "dev_dependencies": dev_dependencies_str,
        "uv_sources": uv_sources_str,
    }


def _get_pypi_project_deps() -> list[str]:
    from create_dagster.version import __version__

    create_dagster_version = parse_package_version(__version__)
    if create_dagster_version.release[0] >= 1:
        # Pin scaffolded libraries to match create-dagster version
        return [f"dagster=={__version__}"]
    else:
        return ["dagster"]


def _get_pypi_local_workspace_environment_deps() -> list[str]:
    return _get_pypi_project_deps() + PYPI_DAGSTER_DEV_DEPENDENCIES


def scaffold_project(
    path: Path,
    dg_context: DgContext,
    use_editable_dagster: bool,
) -> None:
    import tomlkit
    import tomlkit.items

    click.echo(f"Creating a Dagster project at {path}.")

    scaffold_project_options = (
        dg_context.config.workspace.scaffold_project_options
        if dg_context.config.workspace
        else None
    )

    project_excludes = None
    if dg_context.is_in_workspace:
        project_excludes = [
            ".gitignore",
            "README.md.jinja",
        ]

    scaffold_subtree(
        path=path,
        name_placeholder="PROJECT_NAME_PLACEHOLDER",
        project_template_path=Path(
            os.path.join(os.path.dirname(__file__), "templates", "PROJECT_NAME_PLACEHOLDER")
        ),
        excludes=project_excludes,
        **get_dependencies_template_params(
            use_editable_dagster,
            scaffold_project_options,
            pypi_deps=_get_pypi_project_deps(),
            pypi_dev_deps=PYPI_DAGSTER_DEV_DEPENDENCIES,
            editable_deps=EDITABLE_DAGSTER_DEPENDENCIES,
            editable_dev_deps=EDITABLE_DAGSTER_DEV_DEPENDENCIES,
        ),
    )
    click.echo(f"Scaffolded files for Dagster project at {path}.")

    # Build the venv
    cl_dg_context = dg_context.with_root_path(path)

    # Update pyproject.toml
    if cl_dg_context.is_in_workspace:
        entry = {
            "path": str(cl_dg_context.root_path.relative_to(cl_dg_context.workspace_root_path)),
        }

        with modify_dg_toml_config(dg_context.config_file_path) as toml:
            if not has_toml_node(toml, ("workspace", "projects")):
                projects = tomlkit.aot()
                set_toml_node(toml, ("workspace", "projects"), projects)
                item = tomlkit.table()
            else:
                projects = get_toml_node(
                    toml,
                    ("workspace", "projects"),
                    (tomlkit.items.AoT, tomlkit.items.Array),
                )
                if isinstance(projects, tomlkit.items.Array):
                    item = tomlkit.inline_table()
                else:
                    item = tomlkit.table()

            # item.trivia.indent is the preceding whitespace-- this ensures there is always a blank
            # line before the new entry
            item.trivia.indent = item.trivia.indent + "\n"
            for key, value in entry.items():
                item[key] = value
            projects.append(item)


# Despite the fact that editable dependencies are resolved through tool.uv.sources, we need to set
# the dependencies themselves differently depending on whether we are using editable dagster or
# not. This is because `tool.uv.sources` only seems to apply to direct dependencies of the package,
# so any 2+-order Dagster dependency of our package needs to be listed as a direct dependency in the
# editable case. See: https://github.com/astral-sh/uv/issues/9446
EDITABLE_DAGSTER_DEPENDENCIES = [
    "dagster",
    "dagster-pipes",
    "dagster-shared",
    "dagster-test",  # we include dagster-test for testing purposes
]
EDITABLE_DAGSTER_DEV_DEPENDENCIES = [
    "dagster-webserver",
    "dagster-graphql",
    "dagster-dg-core",
    "dagster-dg-cli",
    "dagster-cloud-cli",
]


PYPI_DAGSTER_DEV_DEPENDENCIES = [
    "dagster-webserver",
    "dagster-dg-cli",
]


def _get_editable_dagster_from_env() -> str:
    if not os.environ.get("DAGSTER_GIT_REPO_DIR"):
        exit_with_error(
            "The `--use-editable-dagster` option "
            "requires the `DAGSTER_GIT_REPO_DIR` environment variable to be set."
        )
    return os.environ["DAGSTER_GIT_REPO_DIR"]


def _get_pyproject_toml_dependencies(deps: Sequence[str]) -> str:
    return "\n".join(
        [
            "dependencies = [",
            *[f'    "{dep}",' for dep in deps],
            "]",
        ]
    )


def _get_pyproject_toml_dev_dependencies(deps: Sequence[str]) -> str:
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
            *editable_dagster_root.glob("python_modules/libraries/create-dagster/setup.py"),
        )
    ]
