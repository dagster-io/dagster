from collections import namedtuple

from dagster import check
from dagster.core.instance.ref import InstanceRef
from dagster.core.origin import PipelinePythonOrigin, RepositoryPythonOrigin
from dagster.serdes import whitelist_for_serdes


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


@whitelist_for_serdes
class ExecuteRunArgs(namedtuple('_ExecuteRunArgs', 'pipeline_origin pipeline_run_id instance_ref')):
    def __new__(cls, pipeline_origin, pipeline_run_id, instance_ref):
        return super(ExecuteRunArgs, cls).__new__(
            cls,
            pipeline_origin=check.inst_param(
                pipeline_origin, 'pipeline_origin', PipelinePythonOrigin
            ),
            pipeline_run_id=check.str_param(pipeline_run_id, 'pipeline_run_id'),
            instance_ref=check.inst_param(instance_ref, 'instance_ref', InstanceRef),
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
class ListRepositoriesArgs(
    namedtuple('_ListRepositoriesArgs', 'module_name python_file working_directory')
):
    def __new__(cls, module_name, python_file, working_directory):
        check.invariant(not (module_name and python_file), 'Must set only one')
        check.invariant(module_name or python_file, 'Must set at least one')
        return super(ListRepositoriesArgs, cls).__new__(
            cls,
            module_name=check.opt_str_param(module_name, 'module_name'),
            python_file=check.opt_str_param(python_file, 'python_file'),
            working_directory=check.opt_str_param(working_directory, 'working_directory'),
        )


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
class ListRepositoriesInput(
    namedtuple('_ListRepositoriesInput', 'module_name python_file working_directory')
):
    def __new__(cls, module_name, python_file, working_directory):
        check.invariant(not (module_name and python_file), 'Must set only one')
        check.invariant(module_name or python_file, 'Must set at least one')
        return super(ListRepositoriesInput, cls).__new__(
            cls,
            module_name=check.opt_str_param(module_name, 'module_name'),
            python_file=check.opt_str_param(python_file, 'python_file'),
            working_directory=check.opt_str_param(working_directory, 'working_directory'),
        )


@whitelist_for_serdes
class PartitionArgs(
    namedtuple('_PartitionArgs', 'repository_origin partition_set_name partition_name')
):
    def __new__(cls, repository_origin, partition_set_name, partition_name):
        return super(PartitionArgs, cls).__new__(
            cls,
            repository_origin=check.inst_param(
                repository_origin, 'repository_origin', RepositoryPythonOrigin
            ),
            partition_set_name=check.str_param(partition_set_name, 'partition_set_name'),
            partition_name=check.str_param(partition_name, 'partition_name'),
        )


@whitelist_for_serdes
class PartitionNamesArgs(namedtuple('_PartitionNamesArgs', 'repository_origin partition_set_name')):
    def __new__(cls, repository_origin, partition_set_name):
        return super(PartitionNamesArgs, cls).__new__(
            cls,
            repository_origin=check.inst_param(
                repository_origin, 'repository_origin', RepositoryPythonOrigin
            ),
            partition_set_name=check.str_param(partition_set_name, 'partition_set_name'),
        )


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


@whitelist_for_serdes
class ExternalScheduleExecutionArgs(
    namedtuple('_ExternalScheduleExecutionArgs', 'repository_origin instance_ref schedule_name')
):
    def __new__(cls, repository_origin, instance_ref, schedule_name):
        return super(ExternalScheduleExecutionArgs, cls).__new__(
            cls,
            repository_origin=check.inst_param(
                repository_origin, 'repository_origin', RepositoryPythonOrigin
            ),
            instance_ref=check.inst_param(instance_ref, 'instance_ref', InstanceRef),
            schedule_name=check.str_param(schedule_name, 'schedule_name'),
        )
