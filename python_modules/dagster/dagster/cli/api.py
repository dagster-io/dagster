from __future__ import print_function

import os
import sys
import time
from collections import namedtuple
from contextlib import contextmanager

import click

from dagster import check, seven
from dagster.cli.workspace.autodiscovery import (
    loadable_targets_from_python_file,
    loadable_targets_from_python_module,
)
from dagster.cli.workspace.cli_target import (
    get_reconstructable_repository_from_origin_kwargs,
    origin_target_argument,
)
from dagster.core.definitions import ScheduleExecutionContext
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.errors import (
    DagsterInvalidConfigError,
    DagsterInvalidSubsetError,
    DagsterLaunchFailedError,
    DagsterSubprocessError,
    DagsterUserCodeExecutionError,
    PartitionExecutionError,
    ScheduleExecutionError,
    user_code_error_boundary,
)
from dagster.core.events import EngineEventData
from dagster.core.execution.api import create_execution_plan, execute_run_iterator
from dagster.core.host_representation import (
    InProcessRepositoryLocation,
    external_pipeline_data_from_def,
    external_repository_data_from_def,
)
from dagster.core.host_representation.external_data import (
    ExternalPartitionConfigData,
    ExternalPartitionExecutionErrorData,
    ExternalPartitionNamesData,
    ExternalPartitionTagsData,
    ExternalPipelineSubsetResult,
    ExternalRepositoryData,
    ExternalScheduleExecutionData,
    ExternalScheduleExecutionErrorData,
)
from dagster.core.instance import DagsterInstance
from dagster.core.origin import PipelinePythonOrigin, RepositoryPythonOrigin
from dagster.core.scheduler import (
    ScheduleTickData,
    ScheduleTickStatus,
    ScheduledExecutionFailed,
    ScheduledExecutionSkipped,
    ScheduledExecutionSuccess,
)
from dagster.core.snap.execution_plan_snapshot import (
    ExecutionPlanSnapshot,
    snapshot_from_execution_plan,
)
from dagster.core.storage.tags import check_tags
from dagster.grpc import DagsterGrpcServer
from dagster.serdes import whitelist_for_serdes
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
from dagster.utils.merger import merge_dicts

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
    check.inst_param(output_cls, 'output_cls', (tuple, check.type_types))

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
    help_str=(
        '[INTERNAL] Return the snapshot for the given repository. This is an internal utility. '
        'Users should generally not invoke this command interactively.'
    ),
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
        '[INTERNAL] Return all repository symbols in a given python_file or module name. '
        'Used to bootstrap workspace creation process. This is an internal utility. Users should '
        'generally not invoke this command interactively.'
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
    help_str=(
        '[INTERNAL] Return ExternalPipelineSubsetResult for the given pipeline. This is an '
        'internal utility. Users should generally not invoke this command interactively.'
    ),
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
        'pipeline_origin solid_selection run_config mode step_keys_to_execute pipeline_snapshot_id',
    )
):
    def __new__(
        cls,
        pipeline_origin,
        solid_selection,
        run_config,
        mode,
        step_keys_to_execute,
        pipeline_snapshot_id,
    ):
        return super(ExecutionPlanSnapshotArgs, cls).__new__(
            cls,
            pipeline_origin=check.inst_param(
                pipeline_origin, 'pipeline_origin', PipelinePythonOrigin
            ),
            solid_selection=check.opt_list_param(solid_selection, 'solid_selection', of_type=str),
            run_config=check.dict_param(run_config, 'run_config'),
            mode=check.str_param(mode, 'mode'),
            step_keys_to_execute=check.opt_list_param(
                step_keys_to_execute, 'step_keys_to_execute', of_type=str
            ),
            pipeline_snapshot_id=check.str_param(pipeline_snapshot_id, 'pipeline_snapshot_id'),
        )


@unary_api_cli_command(
    name='execution_plan',
    help_str=(
        '[INTERNAL] Create an execution plan and return its snapshot. This is an internal utility. '
        'Users should generally not invoke this command interactively.'
    ),
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
            run_config=args.run_config,
            mode=args.mode,
            step_keys_to_execute=args.step_keys_to_execute,
        ),
        args.pipeline_snapshot_id,
    )


@whitelist_for_serdes
class PartitionApiCommandArgs(
    namedtuple('_PartitionApiCommandArgs', 'repository_origin partition_set_name partition_name')
):
    pass


@unary_api_cli_command(
    name='partition_config',
    help_str=(
        '[INTERNAL] Return the config for a partition. This is an internal utility. Users should '
        'generally not invoke this command interactively.'
    ),
    input_cls=PartitionApiCommandArgs,
    output_cls=(ExternalPartitionConfigData, ExternalPartitionExecutionErrorData),
)
def partition_config_command(args):
    check.inst_param(args, 'args', PartitionApiCommandArgs)
    recon_repo = recon_repository_from_origin(args.repository_origin)
    definition = recon_repo.get_definition()
    partition_set_def = definition.get_partition_set_def(args.partition_set_name)
    partition = partition_set_def.get_partition(args.partition_name)
    try:
        with user_code_error_boundary(
            PartitionExecutionError,
            lambda: 'Error occurred during the evaluation of the `run_config_for_partition` '
            'function for partition set {partition_set_name}'.format(
                partition_set_name=partition_set_def.name
            ),
        ):
            run_config = partition_set_def.run_config_for_partition(partition)
            return ExternalPartitionConfigData(name=partition.name, run_config=run_config)
    except PartitionExecutionError:
        return ExternalPartitionExecutionErrorData(
            serializable_error_info_from_exc_info(sys.exc_info())
        )


@unary_api_cli_command(
    name='partition_tags',
    help_str=(
        '[INTERNAL] Return the tags for a partition. This is an internal utility. Users should '
        'generally not invoke this command interactively.'
    ),
    input_cls=PartitionApiCommandArgs,
    output_cls=(ExternalPartitionTagsData, ExternalPartitionExecutionErrorData),
)
def partition_tags_command(args):
    check.inst_param(args, 'args', PartitionApiCommandArgs)
    recon_repo = recon_repository_from_origin(args.repository_origin)
    definition = recon_repo.get_definition()
    partition_set_def = definition.get_partition_set_def(args.partition_set_name)
    partition = partition_set_def.get_partition(args.partition_name)
    try:
        with user_code_error_boundary(
            PartitionExecutionError,
            lambda: 'Error occurred during the evaluation of the `tags_for_partition` function for '
            'partition set {partition_set_name}'.format(partition_set_name=partition_set_def.name),
        ):
            tags = partition_set_def.tags_for_partition(partition)
            return ExternalPartitionTagsData(name=partition.name, tags=tags)
    except PartitionExecutionError:
        return ExternalPartitionExecutionErrorData(
            serializable_error_info_from_exc_info(sys.exc_info())
        )


@whitelist_for_serdes
class PartitionNamesApiCommandArgs(
    namedtuple('_PartitionNamesApiCommandArgs', 'repository_origin partition_set_name')
):
    pass


@unary_api_cli_command(
    name='partition_names',
    help_str=(
        '[INTERNAL] Return the partition names for a partition set . This is an internal utility. '
        'Users should generally not invoke this command interactively.'
    ),
    input_cls=PartitionNamesApiCommandArgs,
    output_cls=(ExternalPartitionNamesData, ExternalPartitionExecutionErrorData),
)
def partition_names_command(args):
    check.inst_param(args, 'args', PartitionNamesApiCommandArgs)
    recon_repo = recon_repository_from_origin(args.repository_origin)
    definition = recon_repo.get_definition()
    partition_set_def = definition.get_partition_set_def(args.partition_set_name)
    try:
        with user_code_error_boundary(
            PartitionExecutionError,
            lambda: 'Error occurred during the execution of the partition generation function for '
            'partition set {partition_set_name}'.format(partition_set_name=partition_set_def.name),
        ):
            return ExternalPartitionNamesData(
                partition_names=partition_set_def.get_partition_names()
            )
    except PartitionExecutionError:
        return ExternalPartitionExecutionErrorData(
            serializable_error_info_from_exc_info(sys.exc_info())
        )


@whitelist_for_serdes
class ScheduleExecutionDataCommandArgs(
    namedtuple('_ScheduleExecutionDataCommandArgs', 'repository_origin instance_ref schedule_name')
):
    pass


@unary_api_cli_command(
    name='schedule_config',
    help_str=(
        '[INTERNAL] Return the config for a schedule. This is an internal utility. Users should '
        'generally not invoke this command interactively.'
    ),
    input_cls=ScheduleExecutionDataCommandArgs,
    output_cls=(ExternalScheduleExecutionData, ExternalScheduleExecutionErrorData),
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
            lambda: 'Error occurred during the execution of run_config_fn for schedule '
            '{schedule_name}'.format(schedule_name=schedule_def.name),
        ):
            run_config = schedule_def.get_run_config(schedule_context)
            return ExternalScheduleExecutionData(run_config=run_config)
    except ScheduleExecutionError:
        return ExternalScheduleExecutionErrorData(
            serializable_error_info_from_exc_info(sys.exc_info())
        )


# Execution CLI


@whitelist_for_serdes
class ExecuteRunArgs(namedtuple('_ExecuteRunArgs', 'pipeline_origin pipeline_run_id instance_ref')):
    pass


@whitelist_for_serdes
class ExecuteRunArgsLoadComplete(namedtuple('_ExecuteRunArgsLoadComplete', '')):
    pass


@click.command(
    name='execute_run',
    help=(
        '[INTERNAL] This is an internal utility. Users should generally not invoke this command '
        'interactively.'
    ),
)
@click.argument('input_file', type=click.Path())
@click.argument('output_file', type=click.Path())
def execute_run_command(input_file, output_file):
    args = check.inst(read_unary_input(input_file), ExecuteRunArgs)
    recon_pipeline = recon_pipeline_from_origin(args.pipeline_origin)

    return _execute_run_command_body(
        output_file, recon_pipeline, args.pipeline_run_id, args.instance_ref,
    )


def _execute_run_command_body(output_file, recon_pipeline, pipeline_run_id, instance_ref):
    with ipc_write_stream(output_file) as stream:

        # we need to send but the fact that we have loaded the args so the calling
        # process knows it is safe to clean up the temp input file
        stream.send(ExecuteRunArgsLoadComplete())

        instance = DagsterInstance.from_ref(instance_ref)
        pipeline_run = instance.get_run_by_id(pipeline_run_id)

        pid = os.getpid()
        instance.report_engine_event(
            'Started process for pipeline (pid: {pid}).'.format(pid=pid),
            pipeline_run,
            EngineEventData.in_process(pid, marker_end='cli_api_subprocess_init'),
        )

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


class _ScheduleTickHolder:
    def __init__(self, tick, instance):
        self._tick = tick
        self._instance = instance
        self._set = False

    def update_with_status(self, status, **kwargs):
        self._tick = self._tick.with_status(status=status, **kwargs)

    def write(self):
        self._instance.update_schedule_tick(self._tick)


@contextmanager
def _schedule_tick_state(instance, tick_data):
    tick = instance.create_schedule_tick(tick_data)
    holder = _ScheduleTickHolder(tick=tick, instance=instance)
    try:
        yield holder
    except Exception:  # pylint: disable=broad-except
        error_data = serializable_error_info_from_exc_info(sys.exc_info())
        holder.update_with_status(ScheduleTickStatus.FAILURE, error=error_data)
        raise
    finally:
        holder.write()


@click.command(name='grpc', help='Serve the Dagster inter-process API over GRPC')
@click.option('--port', '-p', type=click.INT, required=False)
@click.option('--socket', '-f', type=click.Path(), required=False)
@click.option('--host', '-h', type=click.STRING, required=False, default='localhost')
def grpc_command(port=None, socket=None, host='localhost'):
    if seven.IS_WINDOWS and port is None:
        raise click.UsageError(
            'You must pass a valid --port/-p on Windows: --socket/-f not supported.'
        )
    if not (port or socket and not (port and socket)):
        raise click.UsageError('You must pass one and only one of --port/-p or --socket/-f.')

    server = DagsterGrpcServer(port=port, socket=socket, host=host)
    server.serve()


###################################################################################################
# WARNING: these cli args are encoded in cron, so are not safely changed without migration
###################################################################################################
@click.command(
    name='launch_scheduled_execution',
    help=(
        '[INTERNAL] This is an internal utility. Users should generally not invoke this command '
        'interactively.'
    ),
)
@click.argument('output_file', type=click.Path())
@origin_target_argument
@click.option('--schedule_name')
def launch_scheduled_execution(output_file, schedule_name, **kwargs):
    with ipc_write_stream(output_file) as stream:
        instance = DagsterInstance.get()

        recon_repo = get_reconstructable_repository_from_origin_kwargs(kwargs)
        schedule = recon_repo.get_reconstructable_schedule(schedule_name)

        # open the tick scope before we call get_definition to make sure
        # load errors are stored in DB
        with _schedule_tick_state(
            instance,
            ScheduleTickData(
                schedule_origin_id=schedule.get_origin_id(),
                schedule_name=schedule_name,
                timestamp=time.time(),
                cron_schedule=None,  # not yet loaded
                status=ScheduleTickStatus.STARTED,
            ),
        ) as tick:

            schedule_def = schedule.get_definition()

            tick.update_with_status(
                status=ScheduleTickStatus.STARTED, cron_schedule=schedule_def.cron_schedule,
            )

            pipeline = recon_repo.get_reconstructable_pipeline(
                schedule_def.pipeline_name
            ).subset_for_execution(schedule_def.solid_selection)

            _launch_scheduled_execution(instance, schedule_def, pipeline, tick, stream)


def _launch_scheduled_execution(instance, schedule_def, pipeline, tick, stream):
    pipeline_def = pipeline.get_definition()

    # Run should_execute and halt if it returns False
    schedule_context = ScheduleExecutionContext(instance)
    with user_code_error_boundary(
        ScheduleExecutionError,
        lambda: 'Error occurred during the execution of should_execute for schedule '
        '{schedule_name}'.format(schedule_name=schedule_def.name),
    ):
        should_execute = schedule_def.should_execute(schedule_context)

    if not should_execute:
        # Update tick to skipped state and return
        tick.update_with_status(ScheduleTickStatus.SKIPPED)
        stream.send(ScheduledExecutionSkipped())
        return

    errors = []

    run_config = {}
    schedule_tags = {}
    try:
        with user_code_error_boundary(
            ScheduleExecutionError,
            lambda: 'Error occurred during the execution of run_config_fn for schedule '
            '{schedule_name}'.format(schedule_name=schedule_def.name),
        ):
            run_config = schedule_def.get_run_config(schedule_context)
    except DagsterUserCodeExecutionError:
        error_data = serializable_error_info_from_exc_info(sys.exc_info())
        errors.append(error_data)

    try:
        with user_code_error_boundary(
            ScheduleExecutionError,
            lambda: 'Error occurred during the execution of tags_fn for schedule '
            '{schedule_name}'.format(schedule_name=schedule_def.name),
        ):
            schedule_tags = schedule_def.get_tags(schedule_context)
    except DagsterUserCodeExecutionError:
        error_data = serializable_error_info_from_exc_info(sys.exc_info())
        errors.append(error_data)

    pipeline_tags = pipeline_def.tags or {}
    check_tags(pipeline_tags, 'pipeline_tags')
    tags = merge_dicts(pipeline_tags, schedule_tags)

    mode = schedule_def.mode

    execution_plan_snapshot = None
    try:
        execution_plan = create_execution_plan(pipeline_def, run_config=run_config, mode=mode,)
        execution_plan_snapshot = snapshot_from_execution_plan(
            execution_plan, pipeline_def.get_pipeline_snapshot_id()
        )
    except DagsterInvalidConfigError:
        error_data = serializable_error_info_from_exc_info(sys.exc_info())
        errors.append(error_data)

    # Enter the run in the DB with the information we have
    possibly_invalid_pipeline_run = instance.create_run(
        pipeline_name=schedule_def.pipeline_name,
        run_id=None,
        run_config=run_config,
        mode=mode,
        solids_to_execute=pipeline.solids_to_execute,
        step_keys_to_execute=None,
        solid_selection=pipeline.solid_selection,
        status=None,
        root_run_id=None,
        parent_run_id=None,
        tags=tags,
        pipeline_snapshot=pipeline_def.get_pipeline_snapshot(),
        execution_plan_snapshot=execution_plan_snapshot,
        parent_pipeline_snapshot=pipeline_def.get_parent_pipeline_snapshot(),
    )

    tick.update_with_status(ScheduleTickStatus.SUCCESS, run_id=possibly_invalid_pipeline_run.run_id)

    # If there were errors, inject them into the event log and fail the run
    if len(errors) > 0:
        for error in errors:
            instance.report_engine_event(
                error.message, possibly_invalid_pipeline_run, EngineEventData.engine_error(error),
            )
        instance.report_run_failed(possibly_invalid_pipeline_run)
        stream.send(
            ScheduledExecutionFailed(run_id=possibly_invalid_pipeline_run.run_id, errors=errors)
        )
        return

    # Otherwise the run should be valid so lets launch it

    # Need an ExternalPipeline to launch so make one here
    recon_repo = pipeline.get_reconstructable_repository()
    repo_location = InProcessRepositoryLocation(recon_repo)
    external_pipeline = repo_location.get_repository(
        recon_repo.get_definition().name
    ).get_full_external_pipeline(pipeline_def.name)

    try:
        launched_run = instance.launch_run(possibly_invalid_pipeline_run.run_id, external_pipeline)
    except DagsterLaunchFailedError:
        error = serializable_error_info_from_exc_info(sys.exc_info())
        instance.report_engine_event(
            error.message, possibly_invalid_pipeline_run, EngineEventData.engine_error(error),
        )
        instance.report_run_failed(possibly_invalid_pipeline_run)
        stream.send(
            ScheduledExecutionFailed(run_id=possibly_invalid_pipeline_run.run_id, errors=[error])
        )
        return

    stream.send(ScheduledExecutionSuccess(run_id=launched_run.run_id))
    return


def create_api_cli_group():
    group = click.Group(
        name='api',
        help=(
            '[INTERNAL] These commands are intended to support internal use cases. Users should '
            'generally not invoke these commands interactively.'
        ),
    )
    group.add_command(execute_run_command)
    group.add_command(repository_snapshot_command)
    group.add_command(pipeline_subset_snapshot_command)
    group.add_command(execution_plan_snapshot_command)
    group.add_command(list_repositories_command)
    group.add_command(partition_config_command)
    group.add_command(partition_tags_command)
    group.add_command(partition_names_command)
    group.add_command(schedule_execution_data_command)
    group.add_command(launch_scheduled_execution)
    group.add_command(grpc_command)
    return group


api_cli = create_api_cli_group()
