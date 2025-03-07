import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional

import click

from dagster_dg.component import RemoteComponentRegistry
from dagster_dg.config import discover_workspace_root
from dagster_dg.context import DgContext
from dagster_dg.utils import exit_with_error, scaffold_subtree

# ########################
# ##### WORKSPACE
# ########################


def scaffold_workspace(
    workspace_name: str,
) -> Path:
    # Can't create a workspace that is a child of another workspace
    new_workspace_path = Path.cwd() / workspace_name
    existing_workspace_path = discover_workspace_root(new_workspace_path)
    if existing_workspace_path:
        exit_with_error(
            f"Workspace already exists at {existing_workspace_path}.  Run `dg scaffold project` to add a new project to that workspace."
        )
    elif new_workspace_path.exists():
        exit_with_error(f"Folder already exists at {new_workspace_path}.")

    scaffold_subtree(
        path=new_workspace_path,
        name_placeholder="WORKSPACE_NAME_PLACEHOLDER",
        templates_path=os.path.join(
            os.path.dirname(__file__), "templates", "WORKSPACE_NAME_PLACEHOLDER"
        ),
        project_name=workspace_name,
    )
    click.echo(f"Scaffolded files for Dagster workspace at {new_workspace_path}.")
    return new_workspace_path


# ########################
# ##### PROJECT
# ########################


def scaffold_project(
    path: Path,
    dg_context: DgContext,
    use_editable_dagster: Optional[str],
    use_editable_components_package_only: Optional[str],
    skip_venv: bool = False,
    populate_cache: bool = True,
) -> None:
    click.echo(f"Creating a Dagster project at {path}.")

    if use_editable_dagster and use_editable_components_package_only:
        exit_with_error(
            "Cannot specify both --use-editable-dagster and --use-editable-components-package-only."
        )
    elif use_editable_dagster:
        editable_dagster_root = (
            _get_editable_dagster_from_env()
            if use_editable_dagster == "TRUE"
            else use_editable_dagster
        )
        deps = EDITABLE_DAGSTER_DEPENDENCIES
        dev_deps = EDITABLE_DAGSTER_DEV_DEPENDENCIES
        sources = _gather_dagster_packages(Path(editable_dagster_root))
    elif use_editable_components_package_only:
        editable_dagster_root = (
            _get_editable_dagster_from_env()
            if use_editable_components_package_only == "TRUE"
            else use_editable_components_package_only
        )
        deps = EDITABLE_COMPONENTS_ONLY_DEPENDENCIES
        dev_deps = EDITABLE_COMPONENTS_ONLY_DEV_DEPENDENCIES
        sources = [
            x
            for x in _gather_dagster_packages(Path(editable_dagster_root))
            if x.name in ("dagster-components", "dagster-test")
        ]
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
        templates_path=os.path.join(
            os.path.dirname(__file__), "templates", "PROJECT_NAME_PLACEHOLDER"
        ),
        dependencies=dependencies_str,
        dev_dependencies=dev_dependencies_str,
        uv_sources=uv_sources_str,
    )
    click.echo(f"Scaffolded files for Dagster project at {path}.")

    # Build the venv
    cl_dg_context = dg_context.with_root_path(path)
    if cl_dg_context.use_dg_managed_environment and not skip_venv:
        cl_dg_context.ensure_uv_lock()
        if populate_cache:
            RemoteComponentRegistry.from_dg_context(cl_dg_context)  # Populate the cache


# Despite the fact that editable dependencies are resolved through tool.uv.sources, we need to set
# the dependencies themselves differently depending on whether we are using editable dagster or
# not. This is because `tool.uv.sources` only seems to apply to direct dependencies of the package,
# so any 2+-order Dagster dependency of our package needs to be listed as a direct dependency in the
# editable case. See: https://github.com/astral-sh/uv/issues/9446
EDITABLE_DAGSTER_DEPENDENCIES = (
    "dagster",
    "dagster-pipes",
    "dagster-components",
    "dagster-test[components]",  # we include dagster-test for testing purposes
)
EDITABLE_COMPONENTS_ONLY_DEPENDENCIES = ("dagster-components", "dagster-test[components]")
EDITABLE_DAGSTER_DEV_DEPENDENCIES = ("dagster-webserver", "dagster-graphql")
EDITABLE_COMPONENTS_ONLY_DEV_DEPENDENCIES = ("dagster-webserver",)
PYPI_DAGSTER_DEPENDENCIES = ("dagster-components",)
PYPI_DAGSTER_DEV_DEPENDENCIES = ("dagster-webserver",)


def _get_editable_dagster_from_env() -> str:
    if not os.environ.get("DAGSTER_GIT_REPO_DIR"):
        exit_with_error(
            "The `--use-editable-dagster` and `--use-editable-components-package-only` options, when used as flags,"
            " require the `DAGSTER_GIT_REPO_DIR` environment variable to be set."
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


# ########################
# ##### COMPONENT TYPE
# ########################


def scaffold_component_type(dg_context: DgContext, class_name: str, module_name: str) -> None:
    root_path = Path(dg_context.default_component_library_path)
    click.echo(f"Creating a Dagster component type at {root_path}/{module_name}.py.")

    scaffold_subtree(
        path=root_path,
        name_placeholder="COMPONENT_TYPE_NAME_PLACEHOLDER",
        templates_path=str(Path(__file__).parent / "templates" / "COMPONENT_TYPE"),
        project_name=module_name,
        name=class_name,
    )

    with open(root_path / "__init__.py", "a") as f:
        f.write(
            f"from {dg_context.default_component_library_module_name}.{module_name} import {class_name}\n"
        )

    click.echo(f"Scaffolded files for Dagster component type at {root_path}/{module_name}.py.")


# ########################
# ##### COMPONENT INSTANCE
# ########################


def scaffold_component_instance(
    path: Path,
    component_type: str,
    scaffold_params: Optional[Mapping[str, Any]],
    dg_context: "DgContext",
) -> None:
    click.echo(f"Creating a Dagster component instance folder at {path}.")
    os.makedirs(path, exist_ok=True)
    scaffold_command = [
        "scaffold",
        "component",
        component_type,
        str(path),
        *(["--json-params", json.dumps(scaffold_params)] if scaffold_params else []),
    ]
    dg_context.external_components_command(scaffold_command)
