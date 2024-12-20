import json
import os
import subprocess
import textwrap
from pathlib import Path
from typing import Any, Mapping, Optional

import click

from dagster_dg.context import CodeLocationDirectoryContext, DgContext
from dagster_dg.utils import (
    camelcase,
    execute_code_location_command,
    generate_subtree,
    get_uv_command_env,
    pushd,
)

# ########################
# ##### DEPLOYMENT
# ########################


def generate_deployment(path: Path) -> None:
    click.echo(f"Creating a Dagster deployment at {path}.")

    generate_subtree(
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


def get_pyproject_toml_uv_sources(editable_dagster_root: str) -> str:
    return textwrap.dedent(f"""
        [tool.uv.sources]
        dagster = {{ path = "{editable_dagster_root}/python_modules/dagster", editable = true }}
        dagster-graphql = {{ path = "{editable_dagster_root}/python_modules/dagster-graphql", editable = true }}
        dagster-pipes = {{ path = "{editable_dagster_root}/python_modules/dagster-pipes", editable = true }}
        dagster-webserver = {{ path = "{editable_dagster_root}/python_modules/dagster-webserver", editable = true }}
        dagster-components = {{ path = "{editable_dagster_root}/python_modules/libraries/dagster-components", editable = true }}
        dagster-embedded-elt = {{ path = "{editable_dagster_root}/python_modules/libraries/dagster-embedded-elt", editable = true }}
        dagster-dbt = {{ path = "{editable_dagster_root}/python_modules/libraries/dagster-dbt", editable = true }}
    """)


def generate_code_location(path: Path, editable_dagster_root: Optional[str] = None) -> None:
    click.echo(f"Creating a Dagster code location at {path}.")

    dependencies = get_pyproject_toml_dependencies(use_editable_dagster=bool(editable_dagster_root))
    dev_dependencies = get_pyproject_toml_dev_dependencies(
        use_editable_dagster=bool(editable_dagster_root)
    )
    uv_sources = (
        get_pyproject_toml_uv_sources(editable_dagster_root) if editable_dagster_root else ""
    )

    generate_subtree(
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
    with pushd(path):
        subprocess.run(["uv", "sync"], check=True, env=get_uv_command_env())


# ########################
# ##### COMPONENT TYPE
# ########################


def generate_component_type(context: CodeLocationDirectoryContext, name: str) -> None:
    root_path = Path(context.local_component_types_root_path)
    click.echo(f"Creating a Dagster component type at {root_path}/{name}.py.")

    generate_subtree(
        path=root_path,
        name_placeholder="COMPONENT_TYPE_NAME_PLACEHOLDER",
        templates_path=os.path.join(os.path.dirname(__file__), "templates", "COMPONENT_TYPE"),
        project_name=name,
        component_type_class_name=camelcase(name),
        component_type=name,
    )

    with open(root_path / "__init__.py", "a") as f:
        f.write(
            f"from {context.local_component_types_root_module_name}.{name} import {camelcase(name)}\n"
        )


# ########################
# ##### COMPONENT INSTANCE
# ########################


def generate_component_instance(
    root_path: Path,
    name: str,
    component_type: str,
    generate_params: Optional[Mapping[str, Any]],
    dg_context: "DgContext",
) -> None:
    component_instance_root_path = root_path / name
    click.echo(f"Creating a Dagster component instance folder at {component_instance_root_path}.")
    os.makedirs(component_instance_root_path, exist_ok=True)
    code_location_command = (
        "generate",
        "component",
        component_type,
        name,
        *(["--json-params", json.dumps(generate_params)] if generate_params else []),
    )
    execute_code_location_command(
        Path(component_instance_root_path),
        code_location_command,
        dg_context,
    )
