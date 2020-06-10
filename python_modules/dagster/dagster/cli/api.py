from __future__ import print_function

import os
import sys
from collections import namedtuple

import click

from dagster import check
from dagster.cli.load_handle import recon_repo_for_cli_args
from dagster.cli.pipeline import legacy_repository_target_argument
from dagster.cli.workspace.autodiscovery import (
    loadable_targets_from_python_file,
    loadable_targets_from_python_module,
)
from dagster.core.definitions import ScheduleExecutionContext
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.errors import (
    DagsterInvalidSubsetError,
    DagsterSubprocessError,
    ScheduleExecutionError,
    PartitionScheduleExecutionError,
    user_code_error_boundary,
)
from dagster.core.events import EngineEventData
from dagster.core.execution.api import create_execution_plan, execute_run_iterator
from dagster.core.host_representation import (
    external_pipeline_data_from_def,
    external_repository_data_from_def,
)
from dagster.core.host_representation.external_data import (
    ExternalPartitionData,
    ExternalPipelineSubsetResult,
    ExternalRepositoryData,
    ExternalScheduleExecutionData,
)
from dagster.core.instance import DagsterInstance
from dagster.core.origin import PipelinePythonOrigin, RepositoryPythonOrigin
from dagster.core.snap.execution_plan_snapshot import (
    ExecutionPlanSnapshot,
    snapshot_from_execution_plan,
)
from dagster.serdes import deserialize_json_to_dagster_namedtuple, whitelist_for_serdes
from dagster.serdes.ipc import (
    ipc_write_stream,
    ipc_write_unary_response,
    read_unary_input,
    setup_interrupt_support,
)
from dagster.utils.error import serializable_error_info_from_exc_info
from dagster.utils.hosted_user_process import (
    recon_pipeline_from_origin,
    recon_repository_from_origin,
)

# Helpers


def get_external_pipeline_subset_result(recon_pipeline, solid_selection):
    check.inst_param(recon_pipeline, 'recon_pipeline', ReconstructablePipeline)

    if solid_selection:
        try:
            sub_pipeline = recon_pipeline.subset_for_execution(solid_selection)
            definition = sub_pipeline.get_definition()
        except DagsterInvalidSubsetError:
            return ExternalPipelineSubsetResult(
                success=False, error=serializable_error_info_from_exc_info(sys.exc_info())
            )
    else:
        definition = recon_pipeline.get_definition()

    external_pipeline_data = external_pipeline_data_from_def(definition)
    return ExternalPipelineSubsetResult(success=True, external_pipeline_data=external_pipeline_data)


@whitelist_for_serdes
class ListRepositoriesResponse(namedtuple('_ListRepositoriesResponse', 'repository_symbols')):
    def __new__(cls, repository_symbols):
        return super(ListRepositoriesResponse, cls).__new__(
            cls,
            repository_symbols=check.list_param(
                repository_symbols, 'repository_symbols', of_type=LoadableRepositorySymbol
            ),
        )


@whitelist_for_serdes
class LoadableRepositorySymbol(
    namedtuple('_LoadableRepositorySymbol', 'repository_name attribute')
):
    def __new__(cls, repository_name, attribute):
        return super(LoadableRepositorySymbol, cls).__new__(
            cls,
            repository_name=check.str_param(repository_name, 'repository_name'),
            attribute=check.str_param(attribute, 'attribute'),
        )


@whitelist_for_serdes
class ListRepositoriesInput(namedtuple('_ListRepositoriesInput', 'module_name python_file')):
    def __new__(cls, module_name, python_file):
        check.invariant(not (module_name and python_file), 'Must set only one')
        check.invariant(module_name or python_file, 'Must set at least one')
        return super(ListRepositoriesInput, cls).__new__(
            cls,
            module_name=check.opt_str_param(module_name, 'module_name'),
            python_file=check.opt_str_param(python_file, 'python_file'),
        )


def unary_api_cli_command(name, help_str, input_cls, output_cls):
    '''
    Use this to decorate synchronous api cli commands that take
    one object and return one object.
    '''
    check.str_param(name, 'name')
    check.str_param(help_str, 'help_str')
    check.type_param(input_cls, 'input_cls')
    check.type_param(output_cls, 'output_cls')

    def wrap(fn):
        @click.command(name=name, help=help_str)
        @click.argument('input_file', type=click.Path())
        @click.argument('output_file', type=click.Path())
        def command(input_file, output_file):
            args = check.inst(read_unary_input(input_file), input_cls)
            output = check.inst(fn(args), output_cls)
            ipc_write_unary_response(output_file, output)

        return command

    return wrap


@unary_api_cli_command(
    name='list_repositories',
    help_str='Return the snapshot for the given repository',
    input_cls=ListRepositoriesInput,
    output_cls=ListRepositoriesResponse,
)
def list_repositories_command(args):
    check.inst_param(args, 'args', ListRepositoriesInput)
    python_file, module_name = args.python_file, args.module_name
    loadable_targets = _get_loadable_targets(python_file, module_name)
    return ListRepositoriesResponse(
        [
            LoadableRepositorySymbol(
                attribute=lt.attribute, repository_name=lt.target_definition.name
            )
            for lt in loadable_targets
        ]
    )


def _get_loadable_targets(python_file, module_name):
    if python_file:
        return loadable_targets_from_python_file(python_file)
    elif module_name:
        return loadable_targets_from_python_module(module_name)
    else:
        check.failed('invalid')
    # Snapshot CLI


@unary_api_cli_command(
    name='repository',
    help_str=(
        'Return all repository symbols in a given python_file or module name. '
        'Used to bootstrap workspace creation process'
    ),
    input_cls=RepositoryPythonOrigin,
    output_cls=ExternalRepositoryData,
)
def repository_snapshot_command(repository_python_origin):

    recon_repo = recon_repository_from_origin(repository_python_origin)
    return external_repository_data_from_def(recon_repo.get_definition())


@whitelist_for_serdes
class PipelineSubsetSnapshotArgs(
    namedtuple('_PipelineSubsetSnapshotArgs', 'pipeline_origin solid_selection')
):
    def __new__(cls, pipeline_origin, solid_selection):
        return super(PipelineSubsetSnapshotArgs, cls).__new__(
            cls,
            pipeline_origin=check.inst_param(
                pipeline_origin, 'pipeline_origin', PipelinePythonOrigin
            ),
            solid_selection=check.list_param(solid_selection, 'solid_selection', of_type=str)
            if solid_selection
            else None,
        )


@unary_api_cli_command(
    name='pipeline_subset',
    help_str='Return ExternalPipelineSubsetResult for the given pipeline',
    input_cls=PipelineSubsetSnapshotArgs,
    output_cls=ExternalPipelineSubsetResult,
)
def pipeline_subset_snapshot_command(args):
    return get_external_pipeline_subset_result(
        recon_pipeline_from_origin(args.pipeline_origin), args.solid_selection
    )


@whitelist_for_serdes
class ExecutionPlanSnapshotArgs(
    namedtuple(
        '_ExecutionPlanSnapshotArgs',
        'pipeline_origin solid_selection environment_dict mode step_keys_to_execute snapshot_id',
    )
):
    def __new__(
        cls,
        pipeline_origin,
        solid_selection,
        environment_dict,
        mode,
        step_keys_to_execute,
        snapshot_id,
    ):
        return super(ExecutionPlanSnapshotArgs, cls).__new__(
            cls,
            pipeline_origin=check.inst_param(
                pipeline_origin, 'pipeline_origin', PipelinePythonOrigin
            ),
            solid_selection=check.opt_list_param(solid_selection, 'solid_selection', of_type=str),
            environment_dict=check.dict_param(environment_dict, 'environment_dict'),
            mode=check.str_param(mode, 'mode'),
            step_keys_to_execute=check.opt_list_param(
                step_keys_to_execute, 'step_keys_to_execute', of_type=str
            ),
            snapshot_id=check.str_param(snapshot_id, 'snapshot_id'),
        )


@unary_api_cli_command(
    name='execution_plan',
    help_str='Create an execution plan and return its snapshot',
    input_cls=ExecutionPlanSnapshotArgs,
    output_cls=ExecutionPlanSnapshot,
)
def execution_plan_snapshot_command(args):

    check.inst_param(args, 'args', ExecutionPlanSnapshotArgs)

    recon_pipeline = (
        recon_pipeline_from_origin(args.pipeline_origin).subset_for_execution(args.solid_selection)
        if args.solid_selection
        else recon_pipeline_from_origin(args.pipeline_origin)
    )

    return snapshot_from_execution_plan(
        create_execution_plan(
            pipeline=recon_pipeline,
            environment_dict=args.environment_dict,
            mode=args.mode,
            step_keys_to_execute=args.step_keys_to_execute,
        ),
        args.snapshot_id,
    )


@whitelist_for_serdes
class PartitionApiCommandArgs(
    namedtuple('_PartitionApiCommandArgs', 'repository_origin partition_set_name partition_name')
):
    pass


@unary_api_cli_command(
    name='partition',
    help_str='Return the config for a partition',
    input_cls=PartitionApiCommandArgs,
    output_cls=ExternalPartitionData,
)
def partition_data_command(args):
    check.inst_param(args, 'args', PartitionApiCommandArgs)
    recon_repo = recon_repository_from_origin(args.repository_origin)
    definition = recon_repo.get_definition()
    partition_set_def = definition.get_partition_set_def(args.partition_set_name)
    partition = partition_set_def.get_partition(args.partition_name)
    try:
        with user_code_error_boundary(
            PartitionScheduleExecutionError,
            lambda: 'Error occurred during the execution of user-provided partition functions for '
            'partition set {partition_set_name}'.format(partition_set_name=partition_set_def.name),
        ):
            run_config = partition_set_def.environment_dict_for_partition(partition)
            tags = partition_set_def.tags_for_partition(partition)
            return ExternalPartitionData(name=partition.name, tags=tags, run_config=run_config)
    except PartitionScheduleExecutionError:
        return ExternalPartitionData(
            name=partition.name, error=serializable_error_info_from_exc_info(sys.exc_info())
        )


@whitelist_for_serdes
class ScheduleExecutionDataCommandArgs(
    namedtuple('_ScheduleExecutionDataCommandArgs', 'repository_origin instance_ref schedule_name')
):
    pass


@unary_api_cli_command(
    name='schedule_config',
    help_str='Return the config for a schedule',
    input_cls=ScheduleExecutionDataCommandArgs,
    output_cls=ExternalScheduleExecutionData,
)
def schedule_execution_data_command(args):
    recon_repo = recon_repository_from_origin(args.repository_origin)
    definition = recon_repo.get_definition()
    schedule_def = definition.get_schedule_def(args.schedule_name)
    instance = DagsterInstance.from_ref(args.instance_ref)
    schedule_context = ScheduleExecutionContext(instance)
    try:
        with user_code_error_boundary(
            ScheduleExecutionError,
            lambda: 'Error occurred during the execution of environment_dict_fn for schedule '
            '{schedule_name}'.format(schedule_name=schedule_def.name),
        ):
            run_config = schedule_def.get_environment_dict(schedule_context)
            schedule_execution_data = ExternalScheduleExecutionData(run_config=run_config)
    except ScheduleExecutionError:
        schedule_execution_data = ExternalScheduleExecutionData(
            error=serializable_error_info_from_exc_info(sys.exc_info())
        )
    return schedule_execution_data


# Execution CLI


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


def _recon_pipeline(stream, recon_repo, pipeline_run):
    try:
        recon_pipeline = recon_repo.get_reconstructable_pipeline(pipeline_run.pipeline_name)
        return recon_pipeline.subset_for_execution_from_existing_pipeline(
            pipeline_run.solids_to_execute
        )

    except:  # pylint: disable=bare-except
        stream.send_error(
            sys.exc_info(),
            message='Could not load pipeline {name} from CLI args {repo_cli_args} for pipeline run {run_id}'.format(
                repo_cli_args=recon_repo.get_cli_args(),
                name=pipeline_run.pipeline_name,
                run_id=pipeline_run.run_id,
            ),
        )
        return


# Note: only allowing repository yaml for now until we stabilize
# how we want to communicate pipeline targets
@click.command(name='execute_run')
@click.argument('output_file', type=click.Path())
@legacy_repository_target_argument
@click.option('--pipeline-run-id')
@click.option('--instance-ref')
def execute_run_command(output_file, pipeline_run_id, instance_ref, **kwargs):
    recon_repo = recon_repo_for_cli_args(kwargs)

    return _execute_run_command_body(output_file, recon_repo, pipeline_run_id, instance_ref)


def _execute_run_command_body(
    output_file, recon_repo, pipeline_run_id, instance_ref_json,
):
    with ipc_write_stream(output_file) as stream:
        instance = _get_instance(stream, instance_ref_json)
        if not instance:
            return

        pipeline_run = instance.get_run_by_id(pipeline_run_id)

        pid = os.getpid()
        instance.report_engine_event(
            'Started process for pipeline (pid: {pid}).'.format(pid=pid),
            pipeline_run,
            EngineEventData.in_process(pid, marker_end='cli_api_subprocess_init'),
        )

        recon_pipeline = _recon_pipeline(stream, recon_repo, pipeline_run)

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
    group.add_command(execute_run_command)
    group.add_command(repository_snapshot_command)
    group.add_command(pipeline_subset_snapshot_command)
    group.add_command(execution_plan_snapshot_command)
    group.add_command(list_repositories_command)
    group.add_command(partition_data_command)
    group.add_command(schedule_execution_data_command)
    return group


api_cli = create_api_cli_group()
