import click

from .pipeline import create_pipeline_cli


def create_dagster_cli():
    group = click.Group()
    group.add_command(create_pipeline_cli())
    return group
