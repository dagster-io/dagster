import click

from ..version import __version__
from .pipeline import create_pipeline_cli


def create_dagster_cli():
    @click.group(commands={'pipeline': create_pipeline_cli()})
    @click.version_option(version=__version__)
    def group():
        pass

    return group


def main():
    cli = create_dagster_cli()
    cli(obj={})  # pylint:disable=E1123
