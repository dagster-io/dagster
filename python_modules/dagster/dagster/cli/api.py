from __future__ import print_function

import json
import sys

import click

from dagster.cli.load_handle import recon_pipeline_for_cli_args, recon_repo_for_cli_args
from dagster.cli.pipeline import pipeline_target_command, repository_target_argument
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.execution.api import execute_pipeline_iterator, execute_run_iterator
from dagster.core.host_representation import (
    external_pipeline_data_from_def,
    external_repository_data_from_def,
)
from dagster.core.instance import DagsterInstance
from dagster.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple
from dagster.serdes.ipc import ipc_write_stream

# Snapshot CLI


@click.command(name='repository', help='Return the snapshot for the given repository')
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
@click.option('--instance-ref')
@click.option('--mode')
def execute_pipeline_command(
    output_file, solid_subset, environment_dict, instance_ref, mode, **kwargs
):
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

        try:
            instance = DagsterInstance.from_ref(
                deserialize_json_to_dagster_namedtuple(instance_ref)
            )
        except:  # pylint: disable=bare-except
            stream.send_error(
                sys.exc_info(),
                message='Could not deserialize {json_string}'.format(json_string=instance_ref),
            )
            return

        for event in execute_pipeline_iterator(
            definition, environment_dict=environment_dict, mode=mode, instance=instance,
        ):
            stream.send(event)


def _subset(recon_pipeline, solid_subset):
    return (
        recon_pipeline.subset_for_execution(solid_subset.split(','))
        if solid_subset
        else recon_pipeline
    )


def _get_instance(stream, instance_ref_json):
    try:
        return DagsterInstance.from_ref(deserialize_json_to_dagster_namedtuple(instance_ref_json))

    except:  # pylint: disable=bare-except
        stream.send_error(
            sys.exc_info(),
            message='Could not deserialize instance-ref arg: {json_string}'.format(
                json_string=instance_ref_json
            ),
        )
        return


def _get_instance(stream, instance_ref_json):
    try:
        return DagsterInstance.from_ref(deserialize_json_to_dagster_namedtuple(instance_ref_json))

    except:  # pylint: disable=bare-except
        stream.send_error(
            sys.exc_info(),
            message='Could not deserialize instance-ref arg: {json_string}'.format(
                json_string=instance_ref_json
            ),
        )
        return


def _get_pipeline_run(stream, pipeline_run_json):
    try:
        return deserialize_json_to_dagster_namedtuple(pipeline_run_json)

    except:  # pylint: disable=bare-except
        stream.send_error(
            sys.exc_info(),
            message='Could not deserialize pipeline-run arg: {json_string}'.format(
                json_string=pipeline_run_json
            ),
        )
        return


def _get_recon_pipeline(stream, yaml_path, pipeline_run):
    try:
        recon_repo = ReconstructableRepository.from_yaml(yaml_path)
        return _subset(
            recon_repo.get_reconstructable_pipeline(pipeline_run.pipeline_name),
            pipeline_run.solid_subset,
        )

    except:  # pylint: disable=bare-except
        stream.send_error(
            sys.exc_info(),
            message='Could not load pipeline with yaml_path {path} and name {name}'.format(
                path=yaml_path, name=pipeline_run.pipeline_name
            ),
        )
        return


# Note: only allowing repository yaml for now until we stabilize
# how we want to communicate pipeline targets
@click.command(name='execute_run')
@click.argument('output_file', type=click.Path())
@click.option('--config-yaml', '-y')
@click.option('--pipeline-run')
@click.option('--instance-ref')
def execute_run_command(output_file, config_yaml, pipeline_run, instance_ref):
    return _execute_run_command_body(output_file, config_yaml, pipeline_run, instance_ref)


def _execute_run_command_body(output_file, config_yaml, pipeline_run_json, instance_ref_json):
    with ipc_write_stream(output_file) as stream:
        pipeline_run = _get_pipeline_run(stream, pipeline_run_json)
        if not pipeline_run:
            return

        instance = _get_instance(stream, instance_ref_json)
        if not instance:
            return

        recon_pipeline = _get_recon_pipeline(stream, config_yaml, pipeline_run)

        for event in execute_run_iterator(recon_pipeline, pipeline_run, instance):
            stream.send(event)


def create_api_cli_group():
    group = click.Group(name="api")
    group.add_command(snapshot_cli)
    group.add_command(execute_pipeline_command)
    group.add_command(execute_run_command)
    return group


api_cli = create_api_cli_group()
