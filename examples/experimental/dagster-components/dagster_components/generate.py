import os
from typing import Type

import click
from dagster._generate.generate import generate_project
from dagster._utils import camelcase, pushd

from dagster_components.core.component import Component


def generate_deployment(path: str) -> None:
    click.echo(f"Creating a Dagster deployment at {path}.")

    generate_project(
        path=path,
        name_placeholder="DEPLOYMENT_NAME_PLACEHOLDER",
        templates_path=os.path.join(
            os.path.dirname(__file__), "templates", "DEPLOYMENT_NAME_PLACEHOLDER"
        ),
    )


def generate_code_location(path: str) -> None:
    click.echo(f"Creating a Dagster code location at {path}.")

    generate_project(
        path=path,
        name_placeholder="CODE_LOCATION_NAME_PLACEHOLDER",
        templates_path=os.path.join(
            os.path.dirname(__file__), "templates", "CODE_LOCATION_NAME_PLACEHOLDER"
        ),
    )


def generate_component_type(root_path: str, name: str) -> None:
    click.echo(f"Creating a Dagster component type at {root_path}/{name}.py.")

    generate_project(
        path=root_path,
        name_placeholder="COMPONENT_TYPE_NAME_PLACEHOLDER",
        templates_path=os.path.join(os.path.dirname(__file__), "templates", "COMPONENT_TYPE"),
        project_name=name,
        component_type_class_name=camelcase(name),
    )


def generate_component_instance(root_path: str, name: str, component_type: Type[Component]) -> None:
    click.echo(f"Creating a Dagster component instance at {root_path}/{name}.py.")

    component_instance_root_path = os.path.join(root_path, name)
    generate_project(
        path=component_instance_root_path,
        name_placeholder="COMPONENT_INSTANCE_NAME_PLACEHOLDER",
        templates_path=os.path.join(
            os.path.dirname(__file__), "templates", "COMPONENT_INSTANCE_NAME_PLACEHOLDER"
        ),
        project_name=name,
        component_type=component_type.registered_name(),
    )
    with pushd(component_instance_root_path):
        component_type.generate_files()
