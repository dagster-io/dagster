from collections import namedtuple
from enum import Enum

from dagster import check
from dagster.core.code_pointer import CodePointer
from dagster.core.instance.ref import InstanceRef
from dagster.core.origin import PipelineOrigin, PipelinePythonOrigin, RepositoryOrigin
from dagster.serdes import whitelist_for_serdes
from dagster.utils.error import SerializableErrorInfo


@whitelist_for_serdes
class ExecutionPlanSnapshotArgs(
    namedtuple(
        "_ExecutionPlanSnapshotArgs",
        "pipeline_origin solid_selection run_config mode step_keys_to_execute pipeline_snapshot_id",
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
            pipeline_origin=check.inst_param(pipeline_origin, "pipeline_origin", PipelineOrigin),
            solid_selection=check.opt_list_param(solid_selection, "solid_selection", of_type=str),
            run_config=check.dict_param(run_config, "run_config"),
            mode=check.str_param(mode, "mode"),
            step_keys_to_execute=check.opt_list_param(
                step_keys_to_execute, "step_keys_to_execute", of_type=str
            ),
            pipeline_snapshot_id=check.str_param(pipeline_snapshot_id, "pipeline_snapshot_id"),
        )


@whitelist_for_serdes
class ExecuteRunArgs(namedtuple("_ExecuteRunArgs", "pipeline_origin pipeline_run_id instance_ref")):
    def __new__(cls, pipeline_origin, pipeline_run_id, instance_ref):
        return super(ExecuteRunArgs, cls).__new__(
            cls,
            pipeline_origin=check.inst_param(pipeline_origin, "pipeline_origin", PipelineOrigin),
            pipeline_run_id=check.str_param(pipeline_run_id, "pipeline_run_id"),
            instance_ref=check.opt_inst_param(instance_ref, "instance_ref", InstanceRef),
        )


@whitelist_for_serdes
class ExecuteStepArgs(
    namedtuple(
        "_ExecuteStepArgs",
        "pipeline_origin pipeline_run_id instance_ref mode step_keys_to_execute run_config retries_dict",
    )
):
    def __new__(
        cls,
        pipeline_origin,
        pipeline_run_id,
        instance_ref=None,
        mode=None,
        step_keys_to_execute=None,
        run_config=None,
        retries_dict=None,
    ):
        return super(ExecuteStepArgs, cls).__new__(
            cls,
            pipeline_origin=check.inst_param(
                pipeline_origin, "pipeline_origin", PipelinePythonOrigin
            ),
            pipeline_run_id=check.str_param(pipeline_run_id, "pipeline_run_id"),
            instance_ref=check.opt_inst_param(instance_ref, "instance_ref", InstanceRef),
            mode=check.opt_str_param(mode, "mode"),
            step_keys_to_execute=check.opt_list_param(
                step_keys_to_execute, "step_keys_to_execute", of_type=str
            ),
            run_config=check.opt_dict_param(run_config, "run_config"),
            retries_dict=check.opt_dict_param(retries_dict, "retries_dict"),
        )


@whitelist_for_serdes
class LoadableRepositorySymbol(
    namedtuple("_LoadableRepositorySymbol", "repository_name attribute")
):
    def __new__(cls, repository_name, attribute):
        return super(LoadableRepositorySymbol, cls).__new__(
            cls,
            repository_name=check.str_param(repository_name, "repository_name"),
            attribute=check.str_param(attribute, "attribute"),
        )


@whitelist_for_serdes
class ListRepositoriesResponse(
    namedtuple(
        "_ListRepositoriesResponse",
        "repository_symbols executable_path repository_code_pointer_dict",
    )
):
    def __new__(
        cls, repository_symbols, executable_path=None, repository_code_pointer_dict=None,
    ):
        return super(ListRepositoriesResponse, cls).__new__(
            cls,
            repository_symbols=check.list_param(
                repository_symbols, "repository_symbols", of_type=LoadableRepositorySymbol
            ),
            # These are currently only used by the GRPC Repository Location, but
            # we will need to migrate the rest of the repository locations to use this.
            executable_path=check.opt_str_param(executable_path, "executable_path"),
            repository_code_pointer_dict=check.opt_dict_param(
                repository_code_pointer_dict,
                "repository_code_pointer_dict",
                key_type=str,
                value_type=CodePointer,
            ),
        )


@whitelist_for_serdes
class ListRepositoriesInput(
    namedtuple("_ListRepositoriesInput", "module_name python_file working_directory attribute")
):
    def __new__(cls, module_name, python_file, working_directory, attribute):
        check.invariant(not (module_name and python_file), "Must set only one")
        check.invariant(module_name or python_file, "Must set at least one")
        return super(ListRepositoriesInput, cls).__new__(
            cls,
            module_name=check.opt_str_param(module_name, "module_name"),
            python_file=check.opt_str_param(python_file, "python_file"),
            working_directory=check.opt_str_param(working_directory, "working_directory"),
            attribute=check.opt_str_param(attribute, "attribute"),
        )


@whitelist_for_serdes
class PartitionArgs(
    namedtuple("_PartitionArgs", "repository_origin partition_set_name partition_name")
):
    def __new__(cls, repository_origin, partition_set_name, partition_name):
        return super(PartitionArgs, cls).__new__(
            cls,
            repository_origin=check.inst_param(
                repository_origin, "repository_origin", RepositoryOrigin
            ),
            partition_set_name=check.str_param(partition_set_name, "partition_set_name"),
            partition_name=check.str_param(partition_name, "partition_name"),
        )


@whitelist_for_serdes
class PartitionNamesArgs(namedtuple("_PartitionNamesArgs", "repository_origin partition_set_name")):
    def __new__(cls, repository_origin, partition_set_name):
        return super(PartitionNamesArgs, cls).__new__(
            cls,
            repository_origin=check.inst_param(
                repository_origin, "repository_origin", RepositoryOrigin
            ),
            partition_set_name=check.str_param(partition_set_name, "partition_set_name"),
        )


@whitelist_for_serdes
class PartitionSetExecutionParamArgs(
    namedtuple(
        "_PartitionSetExecutionParamArgs", "repository_origin partition_set_name partition_names",
    )
):
    def __new__(cls, repository_origin, partition_set_name, partition_names):
        return super(PartitionSetExecutionParamArgs, cls).__new__(
            cls,
            repository_origin=check.inst_param(
                repository_origin, "repository_origin", RepositoryOrigin
            ),
            partition_set_name=check.str_param(partition_set_name, "partition_set_name"),
            partition_names=check.list_param(partition_names, "partition_names", of_type=str),
        )


@whitelist_for_serdes
class PipelineSubsetSnapshotArgs(
    namedtuple("_PipelineSubsetSnapshotArgs", "pipeline_origin solid_selection")
):
    def __new__(cls, pipeline_origin, solid_selection):
        return super(PipelineSubsetSnapshotArgs, cls).__new__(
            cls,
            pipeline_origin=check.inst_param(pipeline_origin, "pipeline_origin", PipelineOrigin),
            solid_selection=check.list_param(solid_selection, "solid_selection", of_type=str)
            if solid_selection
            else None,
        )


@whitelist_for_serdes
class ScheduleExecutionDataMode(Enum):
    # Just return the schedule data and tags, don't check whether we should excute the schedule or return it
    PREVIEW = "PREVIEW"

    # Return schedule data, tags, and whether we should execute the schedule
    LAUNCH_SCHEDULED_EXECUTION = "LAUNCH_SCHEDULED_EXECUTION"


@whitelist_for_serdes
class ExternalScheduleExecutionArgs(
    namedtuple(
        "_ExternalScheduleExecutionArgs",
        "repository_origin instance_ref schedule_name schedule_execution_data_mode",
    )
):
    def __new__(cls, repository_origin, instance_ref, schedule_name, schedule_execution_data_mode):
        return super(ExternalScheduleExecutionArgs, cls).__new__(
            cls,
            repository_origin=check.inst_param(
                repository_origin, "repository_origin", RepositoryOrigin
            ),
            instance_ref=check.inst_param(instance_ref, "instance_ref", InstanceRef),
            schedule_name=check.str_param(schedule_name, "schedule_name"),
            schedule_execution_data_mode=check.inst_param(
                schedule_execution_data_mode,
                "schedule_execution_data_mode",
                ScheduleExecutionDataMode,
            ),
        )


@whitelist_for_serdes
class ExternalTriggeredExecutionArgs(
    namedtuple("_ExternalTriggeredExecutionArgs", "repository_origin instance_ref trigger_name",)
):
    def __new__(cls, repository_origin, instance_ref, trigger_name):
        return super(ExternalTriggeredExecutionArgs, cls).__new__(
            cls,
            repository_origin=check.inst_param(
                repository_origin, "repository_origin", RepositoryOrigin
            ),
            instance_ref=check.inst_param(instance_ref, "instance_ref", InstanceRef),
            trigger_name=check.str_param(trigger_name, "trigger_name"),
        )


@whitelist_for_serdes
class ShutdownServerResult(namedtuple("_ShutdownServerResult", "success serializable_error_info")):
    def __new__(cls, success, serializable_error_info):
        return super(ShutdownServerResult, cls).__new__(
            cls,
            success=check.bool_param(success, "success"),
            serializable_error_info=check.opt_inst_param(
                serializable_error_info, "serializable_error_info", SerializableErrorInfo
            ),
        )


@whitelist_for_serdes
class CancelExecutionRequest(namedtuple("_CancelExecutionRequest", "run_id")):
    def __new__(cls, run_id):
        return super(CancelExecutionRequest, cls).__new__(
            cls, run_id=check.str_param(run_id, "run_id"),
        )


@whitelist_for_serdes
class CancelExecutionResult(
    namedtuple("_CancelExecutionResult", "success message serializable_error_info")
):
    def __new__(cls, success, message, serializable_error_info):
        return super(CancelExecutionResult, cls).__new__(
            cls,
            success=check.bool_param(success, "success"),
            message=check.opt_str_param(message, "message"),
            serializable_error_info=check.opt_inst_param(
                serializable_error_info, "serializable_error_info", SerializableErrorInfo
            ),
        )


@whitelist_for_serdes
class CanCancelExecutionRequest(namedtuple("_CanCancelExecutionRequest", "run_id")):
    def __new__(cls, run_id):
        return super(CanCancelExecutionRequest, cls).__new__(
            cls, run_id=check.str_param(run_id, "run_id"),
        )


@whitelist_for_serdes
class CanCancelExecutionResult(namedtuple("_CancelExecutionResult", "can_cancel")):
    def __new__(cls, can_cancel):
        return super(CanCancelExecutionResult, cls).__new__(
            cls, can_cancel=check.bool_param(can_cancel, "can_cancel"),
        )


@whitelist_for_serdes
class StartRunResult(namedtuple("_StartRunResult", "success message serializable_error_info")):
    def __new__(cls, success, message, serializable_error_info):
        return super(StartRunResult, cls).__new__(
            cls,
            success=check.bool_param(success, "success"),
            message=check.opt_str_param(message, "message"),
            serializable_error_info=check.opt_inst_param(
                serializable_error_info, "serializable_error_info", SerializableErrorInfo
            ),
        )


@whitelist_for_serdes
class GetCurrentImageResult(
    namedtuple("_GetCurrentImageResult", "current_image serializable_error_info")
):
    def __new__(cls, current_image, serializable_error_info):
        return super(GetCurrentImageResult, cls).__new__(
            cls,
            current_image=check.opt_str_param(current_image, "current_image"),
            serializable_error_info=check.opt_inst_param(
                serializable_error_info, "serializable_error_info", SerializableErrorInfo
            ),
        )
