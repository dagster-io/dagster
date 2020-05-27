from __future__ import print_function

import os
import sys

import click

from dagster import check
from dagster.cli.load_handle import recon_pipeline_for_cli_args, recon_repo_for_cli_args
from dagster.cli.pipeline import pipeline_target_command, repository_target_argument
from dagster.core.definitions.reconstructable import (
    ReconstructablePipeline,
    ReconstructableRepository,
)
from dagster.core.errors import DagsterSubprocessError
from dagster.core.events import EngineEventData
from dagster.core.execution.api import execute_run_iterator
from dagster.core.host_representation import (
    external_pipeline_data_from_def,
    external_repository_data_from_def,
)
from dagster.core.instance import DagsterInstance
from dagster.serdes import deserialize_json_to_dagster_namedtuple
from dagster.serdes.ipc import ipc_write_stream, ipc_write_unary_response, setup_interrupt_support
from dagster.utils.error import serializable_error_info_from_exc_info

# Snapshot CLI


@click.command(name='repository', help='Return the snapshot for the given repository')
@click.argument('output_file', type=click.Path())
@repository_target_argument
def repository_snapshot_command(output_file, **kwargs):
    recon_repo = recon_repo_for_cli_args(kwargs)
    definition = recon_repo.get_definition()
    ipc_write_unary_response(output_file, external_repository_data_from_def(definition))


@click.command(name='pipeline', help='Return the snapshot for the given pipeline')
@click.argument('output_file', type=click.Path())
@repository_target_argument
@pipeline_target_command
@click.option('--solid-subset', '-s', help="Comma-separated list of solids")
def pipeline_snapshot_command(output_file, solid_subset, **kwargs):
    recon_pipeline = recon_pipeline_for_cli_args(kwargs)
    definition = recon_pipeline.get_definition()

    if solid_subset:
        definition = definition.subset_for_execution(solid_subset.split(","))

    ipc_write_unary_response(output_file, external_pipeline_data_from_def(definition))


def create_snapshot_cli_group():
    group = click.Group(name="snapshot")
    group.add_command(repository_snapshot_command)
    group.add_command(pipeline_snapshot_command)
    return group


snapshot_cli = create_snapshot_cli_group()


# Execution CLI


def _subset(recon_pipeline, solid_subset):
    check.inst_param(recon_pipeline, 'recon_pipeline', ReconstructablePipeline)
    check.opt_list_param(solid_subset, 'solid_subset', of_type=str)
    return recon_pipeline.subset_for_execution(solid_subset) if solid_subset else recon_pipeline


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
        instance = _get_instance(stream, instance_ref_json)
        if not instance:
            return

        pipeline_run = _get_pipeline_run(stream, pipeline_run_json)
        if not pipeline_run:
            return

        pid = os.getpid()
        instance.report_engine_event(
            'Started process for pipeline (pid: {pid}).'.format(pid=pid),
            pipeline_run,
            EngineEventData.in_process(pid, marker_end='cli_api_subprocess_init'),
        )

        recon_pipeline = _get_recon_pipeline(stream, config_yaml, pipeline_run)
        if not recon_pipeline:
            return

        # Perform setup so that termination of the execution will unwind and report to the
        # instance correctly
        setup_interrupt_support()

        try:

            for event in execute_run_iterator(recon_pipeline, pipeline_run, instance):
                stream.send(event)

        except DagsterSubprocessError as err:
            if not all(
                [
                    err_info.cls_name == 'KeyboardInterrupt'
                    for err_info in err.subprocess_error_infos
                ]
            ):
                instance.report_engine_event(
                    'An exception was thrown during execution that is likely a framework error, '
                    'rather than an error in user code.',
                    pipeline_run,
                    EngineEventData.engine_error(
                        serializable_error_info_from_exc_info(sys.exc_info())
                    ),
                )
        except Exception:  # pylint: disable=broad-except
            instance.report_engine_event(
                'An exception was thrown during execution that is likely a framework error, '
                'rather than an error in user code.',
                pipeline_run,
                EngineEventData.engine_error(serializable_error_info_from_exc_info(sys.exc_info())),
            )
        finally:
            instance.report_engine_event(
                'Process for pipeline exited (pid: {pid}).'.format(pid=pid), pipeline_run,
            )


def create_api_cli_group():
    group = click.Group(name="api")
    group.add_command(snapshot_cli)
    group.add_command(execute_run_command)
    return group


api_cli = create_api_cli_group()
