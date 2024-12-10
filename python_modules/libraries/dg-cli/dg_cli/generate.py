import os
import textwrap
from pathlib import Path
from typing import Optional, Tuple

import click

from dg_cli.utils import (
    camelcase,
    discover_git_root,
    execute_code_location_command,
    generate_subtree,
)


def generate_deployment(path: str) -> None:
    click.echo(f"Creating a Dagster deployment at {path}.")

    generate_subtree(
        path=path,
        name_placeholder="DEPLOYMENT_NAME_PLACEHOLDER",
        templates_path=os.path.join(
            os.path.dirname(__file__), "templates", "DEPLOYMENT_NAME_PLACEHOLDER"
        ),
    )


def generate_code_location(path: str, editable_dagster_root: Optional[str] = None) -> None:
    click.echo(f"Creating a Dagster code location at {path}.")

    # Temporarily we always set an editable dagster root. This is needed while the packages are not
    # published.
    editable_dagster_root = (
        editable_dagster_root
        or os.environ.get("DAGSTER_GIT_REPO_DIR")
        or discover_git_root(Path(__file__))
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


def generate_component_type(root_path: str, name: str) -> None:
    click.echo(f"Creating a Dagster component type at {root_path}/{name}.py.")

    generate_subtree(
        path=root_path,
        name_placeholder="COMPONENT_TYPE_NAME_PLACEHOLDER",
        templates_path=os.path.join(os.path.dirname(__file__), "templates", "COMPONENT_TYPE"),
        project_name=name,
        component_type_class_name=camelcase(name),
        component_type=name,
    )


def generate_component_instance(
    root_path: str,
    name: str,
    component_type: str,
    json_params: Optional[str],
    extra_args: Tuple[str, ...],
) -> None:
    click.echo(f"Creating a Dagster component instance at {root_path}/{name}.py.")

    component_instance_root_path = os.path.join(root_path, name)
    generate_subtree(
        path=component_instance_root_path,
        name_placeholder="COMPONENT_INSTANCE_NAME_PLACEHOLDER",
        templates_path=os.path.join(
            os.path.dirname(__file__), "templates", "COMPONENT_INSTANCE_NAME_PLACEHOLDER"
        ),
        project_name=name,
        component_type=component_type,
    )

    code_location_command = (
        "generate",
        "component",
        component_type,
        name,
        *([f"--json-params={json_params}"] if json_params else []),
        *(["--", *extra_args] if extra_args else []),
    )
    execute_code_location_command(Path(component_instance_root_path), code_location_command)
