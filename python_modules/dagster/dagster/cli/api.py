from __future__ import print_function

import click

from dagster.cli.load_handle import recon_pipeline_for_cli_args, recon_repo_for_cli_args
from dagster.cli.pipeline import pipeline_target_command, repository_target_argument
from dagster.core.host_representation import (
    external_pipeline_data_from_def,
    external_repository_data_from_def,
)
from dagster.serdes import serialize_dagster_namedtuple


@click.command(name='repository', help='Return the snapshot for the given repositoy')
@repository_target_argument
def repository_snapshot_command(**kwargs):
    recon_repo = recon_repo_for_cli_args(kwargs)
    definition = recon_repo.get_definition()

    active_data = external_repository_data_from_def(definition)
    click.echo(serialize_dagster_namedtuple(active_data))


@click.command(name='pipeline', help='Return the snapshot for the given pipeline')
@pipeline_target_command
@click.option('--solid-subset', '-s', help="Comma-separated list of solids")
def pipeline_snapshot_command(solid_subset, **kwargs):
    recon_pipeline = recon_pipeline_for_cli_args(kwargs)
    definition = recon_pipeline.get_definition()

    if solid_subset:
        definition = definition.subset_for_execution(solid_subset.split(","))

    active_data = external_pipeline_data_from_def(definition)
    click.echo(serialize_dagster_namedtuple(active_data))


def create_snapshot_cli_group():
    group = click.Group(name="snapshot")
    group.add_command(repository_snapshot_command)
    group.add_command(pipeline_snapshot_command)
    return group


snapshot_cli = create_snapshot_cli_group()


def create_api_cli_group():
    group = click.Group(name="api")
    group.add_command(snapshot_cli)
    return group


api_cli = create_api_cli_group()
