import os
import subprocess
import textwrap
from pathlib import Path
from typing import Optional, Tuple

import click

from dagster_dg.context import CodeLocationDirectoryContext
from dagster_dg.utils import (
    camelcase,
    discover_git_root,
    execute_code_location_command,
    generate_subtree,
    get_uv_command_env,
    pushd,
)


def generate_deployment(path: Path) -> None:
    click.echo(f"Creating a Dagster deployment at {path}.")

    generate_subtree(
        path=path,
        name_placeholder="DEPLOYMENT_NAME_PLACEHOLDER",
        templates_path=os.path.join(
            os.path.dirname(__file__), "templates", "DEPLOYMENT_NAME_PLACEHOLDER"
        ),
    )


def generate_code_location(path: Path, editable_dagster_root: Optional[str] = None) -> None:
    click.echo(f"Creating a Dagster code location at {path}.")

    # Temporarily we always set an editable dagster root. This is needed while the packages are not
    # published.
    editable_dagster_root = (
        editable_dagster_root
        or os.environ.get("DAGSTER_GIT_REPO_DIR")
        or str(discover_git_root(Path(__file__)))
    )

    editable_dagster_uv_sources = textwrap.dedent(f"""
    [tool.uv.sources]
    dagster = {{ path = "{editable_dagster_root}/python_modules/dagster", editable = true }}
    dagster-graphql = {{ path = "{editable_dagster_root}/python_modules/dagster-graphql", editable = true }}
    dagster-pipes = {{ path = "{editable_dagster_root}/python_modules/dagster-pipes", editable = true }}
    dagster-webserver = {{ path = "{editable_dagster_root}/python_modules/dagster-webserver", editable = true }}
    dagster-components = {{ path = "{editable_dagster_root}/python_modules/libraries/dagster-components", editable = true }}
    dagster-embedded-elt = {{ path = "{editable_dagster_root}/python_modules/libraries/dagster-embedded-elt", editable = true }}
    dagster-dbt = {{ path = "{editable_dagster_root}/python_modules/libraries/dagster-dbt", editable = true }}
    """)

    if editable_dagster_root:
        uv_sources = editable_dagster_uv_sources
    else:
        uv_sources = editable_dagster_uv_sources

    generate_subtree(
        path=path,
        name_placeholder="CODE_LOCATION_NAME_PLACEHOLDER",
        templates_path=os.path.join(
            os.path.dirname(__file__), "templates", "CODE_LOCATION_NAME_PLACEHOLDER"
        ),
        uv_sources=uv_sources,
    )

    # Build the venv
    with pushd(path):
        subprocess.run(["uv", "sync"], check=True, env=get_uv_command_env())


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


def generate_component_instance(
    root_path: Path,
    name: str,
    component_type: str,
    json_params: Optional[str],
    extra_args: Tuple[str, ...],
) -> None:
    component_instance_root_path = root_path / name
    click.echo(f"Creating a Dagster component instance folder at {component_instance_root_path}.")
    os.makedirs(component_instance_root_path, exist_ok=True)
    code_location_command = (
        "generate",
        "component",
        component_type,
        name,
        *(["--json-params", json_params] if json_params else []),
        *(["--", *extra_args] if extra_args else []),
    )
    execute_code_location_command(Path(component_instance_root_path), code_location_command)
