from __future__ import print_function

import json

import click

from dagster.cli.load_handle import recon_pipeline_for_cli_args, recon_repo_for_cli_args
from dagster.cli.pipeline import pipeline_target_command, repository_target_argument
from dagster.core.execution.api import execute_pipeline_iterator
from dagster.core.host_representation import (
    external_pipeline_data_from_def,
    external_repository_data_from_def,
)
from dagster.core.instance import DagsterInstance
from dagster.serdes import serialize_dagster_namedtuple
from dagster.serdes.ipc import ipc_write_stream

# Snapshot CLI


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


# Execution CLI


@click.command(name='execute_pipeline', help='Execute pipeline')
@pipeline_target_command
@click.argument('output_file', type=click.Path())
@click.option('--solid-subset', '-s', help="Comma-separated list of solids")
@click.option('--environment-dict')
@click.option('--mode')
def execute_pipeline_command(output_file, solid_subset, environment_dict, mode, **kwargs):
    '''
    This command might want to take a runId instead of current arguments

    1. Should take optional flags to determine where to store the log output
    2. Investigate python logging library to see what we can do there
    '''

    with ipc_write_stream(output_file) as stream:
        recon_pipeline = recon_pipeline_for_cli_args(kwargs)
        definition = recon_pipeline.get_definition()

        if solid_subset:
            definition = definition.subset_for_execution(solid_subset.split(","))

        # This can raise a ValueError, but this is caught by the broad-except
        # and the exception is serialized as a SerializableErrorInfo
        environment_dict = json.loads(environment_dict)

        instance = DagsterInstance.get()

        for event in execute_pipeline_iterator(
            definition, environment_dict=environment_dict, mode=mode, instance=instance,
        ):
            stream.send(event)


def create_api_cli_group():
    group = click.Group(name="api")
    group.add_command(snapshot_cli)
    group.add_command(execute_pipeline_command)
    return group


api_cli = create_api_cli_group()
