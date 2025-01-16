import json
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Optional

import click

from dagster_dg.component import RemoteComponentRegistry
from dagster_dg.context import DgContext
from dagster_dg.utils import camelcase, scaffold_subtree

# ########################
# ##### DEPLOYMENT
# ########################


def scaffold_deployment(path: Path, dg_context: DgContext) -> None:
    click.echo(f"Creating a Dagster deployment at {path}.")

    scaffold_subtree(
        path=path,
        name_placeholder="DEPLOYMENT_NAME_PLACEHOLDER",
        templates_path=os.path.join(
            os.path.dirname(__file__), "templates", "DEPLOYMENT_NAME_PLACEHOLDER"
        ),
    )


# ########################
# ##### CODE LOCATION
# ########################

# Despite the fact that editable dependencies are resolved through tool.uv.sources, we need to set
# the dependencies themselves differently depending on whether we are using editable dagster or
# not. This is because `tool.uv.sources` only seems to apply to direct dependencies of the package,
# so any 2+-order Dagster dependency of our package needs to be listed as a direct dependency in the
# editable case.
EDITABLE_DAGSTER_DEPENDENCIES = (
    "dagster",
    "dagster-pipes",
    "dagster-components",
)
EDITABLE_DAGSTER_DEV_DEPENDENCIES = ("dagster-webserver", "dagster-graphql")
PYPI_DAGSTER_DEPENDENCIES = ("dagster-components",)
PYPI_DAGSTER_DEV_DEPENDENCIES = ("dagster-webserver",)


def get_pyproject_toml_dependencies(use_editable_dagster: bool) -> str:
    deps = EDITABLE_DAGSTER_DEPENDENCIES if use_editable_dagster else PYPI_DAGSTER_DEPENDENCIES
    return "\n".join(
        [
            "dependencies = [",
            *[f'    "{dep}",' for dep in deps],
            "]",
        ]
    )


def get_pyproject_toml_dev_dependencies(use_editable_dagster: bool) -> str:
    deps = (
        EDITABLE_DAGSTER_DEV_DEPENDENCIES if use_editable_dagster else PYPI_DAGSTER_DEV_DEPENDENCIES
    )
    return "\n".join(
        [
            "dev = [",
            *[f'    "{dep}",' for dep in deps],
            "]",
        ]
    )


def get_pyproject_toml_uv_sources(editable_dagster_root: Path) -> str:
    lib_lines = [
        f'{path.name} = {{ path = "{path}", editable = true }}'
        for path in _gather_dagster_packages(editable_dagster_root)
    ]
    return "\n".join(
        [
            "[tool.uv.sources]",
            *lib_lines,
        ]
    )


def _gather_dagster_packages(editable_dagster_root: Path) -> Sequence[Path]:
    return [
        p.parent
        for p in (
            *editable_dagster_root.glob("python_modules/dagster*/setup.py"),
            *editable_dagster_root.glob("python_modules/libraries/dagster*/setup.py"),
        )
    ]


def scaffold_code_location(
    path: Path,
    dg_context: DgContext,
    editable_dagster_root: Optional[str] = None,
    skip_venv: bool = False,
) -> None:
    click.echo(f"Creating a Dagster code location at {path}.")

    dependencies = get_pyproject_toml_dependencies(use_editable_dagster=bool(editable_dagster_root))
    dev_dependencies = get_pyproject_toml_dev_dependencies(
        use_editable_dagster=bool(editable_dagster_root)
    )
    uv_sources = (
        get_pyproject_toml_uv_sources(Path(editable_dagster_root)) if editable_dagster_root else ""
    )

    scaffold_subtree(
        path=path,
        name_placeholder="CODE_LOCATION_NAME_PLACEHOLDER",
        templates_path=os.path.join(
            os.path.dirname(__file__), "templates", "CODE_LOCATION_NAME_PLACEHOLDER"
        ),
        dependencies=dependencies,
        dev_dependencies=dev_dependencies,
        uv_sources=uv_sources,
    )

    # Build the venv
    cl_dg_context = dg_context.with_root_path(path)
    if cl_dg_context.config.use_dg_managed_environment and not skip_venv:
        cl_dg_context.ensure_uv_lock()
        RemoteComponentRegistry.from_dg_context(cl_dg_context)  # Populate the cache


# ########################
# ##### COMPONENT TYPE
# ########################


def scaffold_component_type(dg_context: DgContext, name: str) -> None:
    root_path = Path(dg_context.components_lib_path)
    click.echo(f"Creating a Dagster component type at {root_path}/{name}.py.")

    scaffold_subtree(
        path=root_path,
        name_placeholder="COMPONENT_TYPE_NAME_PLACEHOLDER",
        templates_path=os.path.join(os.path.dirname(__file__), "templates", "COMPONENT_TYPE"),
        project_name=name,
        component_type_class_name=camelcase(name),
        name=name,
    )

    with open(root_path / "__init__.py", "a") as f:
        f.write(f"from {dg_context.components_lib_package_name}.{name} import {camelcase(name)}\n")


# ########################
# ##### COMPONENT INSTANCE
# ########################


def scaffold_component_instance(
    root_path: Path,
    name: str,
    component_type: str,
    scaffold_params: Optional[Mapping[str, Any]],
    dg_context: "DgContext",
) -> None:
    component_instance_root_path = root_path / name
    click.echo(f"Creating a Dagster component instance folder at {component_instance_root_path}.")
    os.makedirs(component_instance_root_path, exist_ok=True)
    code_location_command = [
        "scaffold",
        "component",
        component_type,
        name,
        *(["--json-params", json.dumps(scaffold_params)] if scaffold_params else []),
    ]
    dg_context.external_components_command(code_location_command)
