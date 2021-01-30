"""
This module contains data objects meant to be serialized between
host processes and user processes. They should contain no
business logic or clever indexing. Use the classes in external.py
for that.
"""

from collections import namedtuple

from dagster import check
from dagster.core.definitions import (
    JobDefinition,
    JobType,
    PartitionSetDefinition,
    PipelineDefinition,
    PresetDefinition,
    RepositoryDefinition,
    ScheduleDefinition,
)
from dagster.core.definitions.job import RunRequest, SkipReason
from dagster.core.definitions.partition import PartitionScheduleDefinition
from dagster.core.snap import PipelineSnapshot
from dagster.serdes import whitelist_for_serdes
from dagster.utils.error import SerializableErrorInfo


@whitelist_for_serdes
class ExternalRepositoryData(
    namedtuple(
        "_ExternalRepositoryData",
        "name external_pipeline_datas external_schedule_datas external_partition_set_datas external_executable_datas external_job_datas",
    )
):
    def __new__(
        cls,
        name,
        external_pipeline_datas,
        external_schedule_datas,
        external_partition_set_datas,
        external_executable_datas=None,
        external_job_datas=None,
    ):
        return super(ExternalRepositoryData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            external_pipeline_datas=check.list_param(
                external_pipeline_datas, "external_pipeline_datas", of_type=ExternalPipelineData
            ),
            external_schedule_datas=check.list_param(
                external_schedule_datas, "external_schedule_datas", of_type=ExternalScheduleData
            ),
            external_partition_set_datas=check.list_param(
                external_partition_set_datas,
                "external_partition_set_datas",
                of_type=ExternalPartitionSetData,
            ),
            external_executable_datas=check.opt_list_param(
                external_executable_datas, "external_executable_datas"
            ),
            external_job_datas=check.opt_list_param(
                external_job_datas,
                "external_job_datas",
                of_type=(ExternalScheduleData, ExternalSensorData, ExternalJobData),
            ),
        )

    def get_pipeline_snapshot(self, name):
        check.str_param(name, "name")

        for external_pipeline_data in self.external_pipeline_datas:
            if external_pipeline_data.name == name:
                return external_pipeline_data.pipeline_snapshot

        check.failed("Could not find pipeline snapshot named " + name)

    def get_external_pipeline_data(self, name):
        check.str_param(name, "name")

        for external_pipeline_data in self.external_pipeline_datas:
            if external_pipeline_data.name == name:
                return external_pipeline_data

        check.failed("Could not find external pipeline data named " + name)

    def get_external_schedule_data(self, name):
        check.str_param(name, "name")

        for external_schedule_data in self.external_schedule_datas:
            if external_schedule_data.name == name:
                return external_schedule_data

        check.failed("Could not find external schedule data named " + name)

    def get_external_partition_set_data(self, name):
        check.str_param(name, "name")

        for external_partition_set_data in self.external_partition_set_datas:
            if external_partition_set_data.name == name:
                return external_partition_set_data

        check.failed("Could not find external partition set data named " + name)

    def get_external_job_data(self, name):
        check.str_param(name, "name")

        for external_job_data in self.external_job_datas:
            if external_job_data.name == name:
                return external_job_data

        check.failed("Could not find job data named " + name)


@whitelist_for_serdes
class ExternalPipelineSubsetResult(
    namedtuple("_ExternalPipelineSubsetResult", "success error external_pipeline_data")
):
    def __new__(cls, success, error=None, external_pipeline_data=None):
        return super(ExternalPipelineSubsetResult, cls).__new__(
            cls,
            success=check.bool_param(success, "success"),
            error=check.opt_inst_param(error, "error", SerializableErrorInfo),
            external_pipeline_data=check.opt_inst_param(
                external_pipeline_data, "external_pipeline_data", ExternalPipelineData
            ),
        )


@whitelist_for_serdes
class ExternalPipelineData(
    namedtuple(
        "_ExternalPipelineData", "name pipeline_snapshot active_presets parent_pipeline_snapshot"
    )
):
    def __new__(cls, name, pipeline_snapshot, active_presets, parent_pipeline_snapshot):
        return super(ExternalPipelineData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            pipeline_snapshot=check.inst_param(
                pipeline_snapshot, "pipeline_snapshot", PipelineSnapshot
            ),
            parent_pipeline_snapshot=check.opt_inst_param(
                parent_pipeline_snapshot, "parent_pipeline_snapshot", PipelineSnapshot
            ),
            active_presets=check.list_param(
                active_presets, "active_presets", of_type=ExternalPresetData
            ),
        )


@whitelist_for_serdes
class ExternalPresetData(
    namedtuple("_ExternalPresetData", "name run_config solid_selection mode tags")
):
    def __new__(cls, name, run_config, solid_selection, mode, tags):
        return super(ExternalPresetData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            run_config=check.opt_dict_param(run_config, "run_config"),
            solid_selection=check.opt_nullable_list_param(
                solid_selection, "solid_selection", of_type=str
            ),
            mode=check.str_param(mode, "mode"),
            tags=check.opt_dict_param(tags, "tags"),
        )


@whitelist_for_serdes
class ExternalScheduleData(
    namedtuple(
        "_ExternalScheduleData",
        "name cron_schedule pipeline_name solid_selection mode environment_vars partition_set_name execution_timezone",
    )
):
    def __new__(
        cls,
        name,
        cron_schedule,
        pipeline_name,
        solid_selection,
        mode,
        environment_vars,
        partition_set_name,
        execution_timezone,
    ):
        return super(ExternalScheduleData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            cron_schedule=check.str_param(cron_schedule, "cron_schedule"),
            pipeline_name=check.str_param(pipeline_name, "pipeline_name"),
            solid_selection=check.opt_nullable_list_param(solid_selection, "solid_selection", str),
            mode=check.opt_str_param(mode, "mode"),
            environment_vars=check.opt_dict_param(environment_vars, "environment_vars"),
            partition_set_name=check.opt_str_param(partition_set_name, "partition_set_name"),
            execution_timezone=check.opt_str_param(execution_timezone, "execution_timezone"),
        )

    @property
    def job_type(self):
        return JobType.SCHEDULE


@whitelist_for_serdes
class ExternalScheduleExecutionData(
    namedtuple("_ExternalScheduleExecutionData", "run_requests skip_message")
):
    def __new__(cls, run_requests=None, skip_message=None):
        return super(ExternalScheduleExecutionData, cls).__new__(
            cls,
            run_requests=check.opt_list_param(run_requests, "run_requests", RunRequest),
            skip_message=check.opt_str_param(skip_message, "skip_message"),
        )

    @staticmethod
    def from_execution_data(execution_data):
        check.opt_list_param(execution_data, "execution_data", (SkipReason, RunRequest))
        return ExternalScheduleExecutionData(
            run_requests=[datum for datum in execution_data if isinstance(datum, RunRequest)],
            skip_message=execution_data[0].skip_message
            if execution_data and isinstance(execution_data[0], SkipReason)
            else None,
        )


@whitelist_for_serdes
class ExternalScheduleExecutionErrorData(
    namedtuple("_ExternalScheduleExecutionErrorData", "error")
):
    def __new__(cls, error):
        return super(ExternalScheduleExecutionErrorData, cls).__new__(
            cls, error=check.opt_inst_param(error, "error", SerializableErrorInfo),
        )


@whitelist_for_serdes
class ExternalSensorData(
    namedtuple("_ExternalSensorData", "name pipeline_name solid_selection mode min_interval")
):
    def __new__(cls, name, pipeline_name, solid_selection, mode, min_interval=None):
        return super(ExternalSensorData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            pipeline_name=check.str_param(pipeline_name, "pipeline_name"),
            solid_selection=check.opt_nullable_list_param(solid_selection, "solid_selection", str),
            mode=check.opt_str_param(mode, "mode"),
            min_interval=check.opt_int_param(min_interval, "min_interval"),
        )

    @property
    def job_type(self):
        return JobType.SENSOR


# DEPRECATED, see https://github.com/dagster-io/dagster/issues/3644 for removal
@whitelist_for_serdes
class ExternalJobData(
    namedtuple("_ExternalJobData", "name job_type pipeline_name solid_selection mode")
):
    def __new__(
        cls, name, job_type, pipeline_name, solid_selection, mode,
    ):
        return super(ExternalJobData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            job_type=check.inst_param(job_type, "job_type", JobType),
            pipeline_name=check.str_param(pipeline_name, "pipeline_name"),
            solid_selection=check.opt_nullable_list_param(solid_selection, "solid_selection", str),
            mode=check.opt_str_param(mode, "mode"),
        )


@whitelist_for_serdes
class ExternalSensorExecutionData(
    namedtuple("_ExternalSensorExecutionData", "run_requests skip_message")
):
    def __new__(cls, run_requests=None, skip_message=None):
        check.opt_list_param(run_requests, "run_requests", RunRequest)
        check.opt_str_param(skip_message, "skip_message")
        check.invariant(
            not (run_requests and skip_message), "Found both skip data and run request data"
        )
        return super(ExternalSensorExecutionData, cls).__new__(
            cls, run_requests=run_requests, skip_message=skip_message,
        )

    @staticmethod
    def from_execution_data(tick_data):
        check.opt_list_param(tick_data, "tick_data", (SkipReason, RunRequest))
        return ExternalSensorExecutionData(
            run_requests=[datum for datum in tick_data if isinstance(datum, RunRequest)],
            skip_message=tick_data[0].skip_message
            if tick_data and isinstance(tick_data[0], SkipReason)
            else None,
        )


@whitelist_for_serdes
class ExternalSensorExecutionErrorData(namedtuple("_ExternalSensorExecutionErrorData", "error")):
    def __new__(cls, error):
        return super(ExternalSensorExecutionErrorData, cls).__new__(
            cls, error=check.opt_inst_param(error, "error", SerializableErrorInfo),
        )


@whitelist_for_serdes
class ExternalExecutionParamsData(namedtuple("_ExternalExecutionParamsData", "run_config tags")):
    def __new__(cls, run_config=None, tags=None):
        return super(ExternalExecutionParamsData, cls).__new__(
            cls,
            run_config=check.opt_dict_param(run_config, "run_config"),
            tags=check.opt_dict_param(tags, "tags", key_type=str, value_type=str),
        )


@whitelist_for_serdes
class ExternalExecutionParamsErrorData(namedtuple("_ExternalExecutionParamsErrorData", "error")):
    def __new__(cls, error):
        return super(ExternalExecutionParamsErrorData, cls).__new__(
            cls, error=check.opt_inst_param(error, "error", SerializableErrorInfo),
        )


@whitelist_for_serdes
class ExternalPartitionSetData(
    namedtuple("_ExternalPartitionSetData", "name pipeline_name solid_selection mode")
):
    def __new__(cls, name, pipeline_name, solid_selection, mode):
        return super(ExternalPartitionSetData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            pipeline_name=check.str_param(pipeline_name, "pipeline_name"),
            solid_selection=check.opt_nullable_list_param(solid_selection, "solid_selection", str),
            mode=check.opt_str_param(mode, "mode"),
        )


@whitelist_for_serdes
class ExternalPartitionNamesData(namedtuple("_ExternalPartitionNamesData", "partition_names")):
    def __new__(cls, partition_names=None):
        return super(ExternalPartitionNamesData, cls).__new__(
            cls, partition_names=check.opt_list_param(partition_names, "partition_names", str),
        )


@whitelist_for_serdes
class ExternalPartitionConfigData(namedtuple("_ExternalPartitionConfigData", "name run_config")):
    def __new__(cls, name, run_config=None):
        return super(ExternalPartitionConfigData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            run_config=check.opt_dict_param(run_config, "run_config"),
        )


@whitelist_for_serdes
class ExternalPartitionTagsData(namedtuple("_ExternalPartitionTagsData", "name tags")):
    def __new__(cls, name, tags=None):
        return super(ExternalPartitionTagsData, cls).__new__(
            cls, name=check.str_param(name, "name"), tags=check.opt_dict_param(tags, "tags"),
        )


@whitelist_for_serdes
class ExternalPartitionExecutionParamData(
    namedtuple("_ExternalPartitionExecutionParamData", "name tags run_config")
):
    def __new__(cls, name, tags, run_config):
        return super(ExternalPartitionExecutionParamData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            tags=check.dict_param(tags, "tags"),
            run_config=check.opt_dict_param(run_config, "run_config"),
        )


@whitelist_for_serdes
class ExternalPartitionSetExecutionParamData(
    namedtuple("_ExternalPartitionSetExecutionParamData", "partition_data")
):
    def __new__(cls, partition_data):
        return super(ExternalPartitionSetExecutionParamData, cls).__new__(
            cls,
            partition_data=check.list_param(
                partition_data, "partition_data", of_type=ExternalPartitionExecutionParamData
            ),
        )


@whitelist_for_serdes
class ExternalPartitionExecutionErrorData(
    namedtuple("_ExternalPartitionExecutionErrorData", "error")
):
    def __new__(cls, error):
        return super(ExternalPartitionExecutionErrorData, cls).__new__(
            cls, error=check.opt_inst_param(error, "error", SerializableErrorInfo),
        )


def external_repository_data_from_def(repository_def):
    check.inst_param(repository_def, "repository_def", RepositoryDefinition)

    return ExternalRepositoryData(
        name=repository_def.name,
        external_pipeline_datas=sorted(
            list(map(external_pipeline_data_from_def, repository_def.get_all_pipelines())),
            key=lambda pd: pd.name,
        ),
        external_schedule_datas=sorted(
            list(map(external_schedule_data_from_def, repository_def.schedule_defs)),
            key=lambda sd: sd.name,
        ),
        external_partition_set_datas=sorted(
            list(map(external_partition_set_data_from_def, repository_def.partition_set_defs)),
            key=lambda psd: psd.name,
        ),
        external_job_datas=sorted(
            list(map(external_job_from_def, repository_def.job_defs)), key=lambda job: job.name,
        ),
    )


def external_pipeline_data_from_def(pipeline_def):
    check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
    return ExternalPipelineData(
        name=pipeline_def.name,
        pipeline_snapshot=pipeline_def.get_pipeline_snapshot(),
        parent_pipeline_snapshot=pipeline_def.get_parent_pipeline_snapshot(),
        active_presets=sorted(
            list(map(external_preset_data_from_def, pipeline_def.preset_defs)),
            key=lambda pd: pd.name,
        ),
    )


def external_schedule_data_from_def(schedule_def):
    check.inst_param(schedule_def, "schedule_def", ScheduleDefinition)
    return ExternalScheduleData(
        name=schedule_def.name,
        cron_schedule=schedule_def.cron_schedule,
        pipeline_name=schedule_def.pipeline_name,
        solid_selection=schedule_def.solid_selection,
        mode=schedule_def.mode,
        environment_vars=schedule_def.environment_vars,
        partition_set_name=schedule_def.get_partition_set().name
        if isinstance(schedule_def, PartitionScheduleDefinition)
        else None,
        execution_timezone=schedule_def.execution_timezone,
    )


def external_partition_set_data_from_def(partition_set_def):
    check.inst_param(partition_set_def, "partition_set_def", PartitionSetDefinition)
    return ExternalPartitionSetData(
        name=partition_set_def.name,
        pipeline_name=partition_set_def.pipeline_name,
        solid_selection=partition_set_def.solid_selection,
        mode=partition_set_def.mode,
    )


def external_job_from_def(job_def):
    check.inst_param(job_def, "job_def", JobDefinition)
    if isinstance(job_def, ScheduleDefinition):
        return external_schedule_data_from_def(job_def)
    else:
        return external_sensor_data_from_def(job_def)


def external_sensor_data_from_def(sensor_def):
    return ExternalSensorData(
        name=sensor_def.name,
        pipeline_name=sensor_def.pipeline_name,
        solid_selection=sensor_def.solid_selection,
        mode=sensor_def.mode,
        min_interval=sensor_def.minimum_interval_seconds,
    )


def external_preset_data_from_def(preset_def):
    check.inst_param(preset_def, "preset_def", PresetDefinition)
    return ExternalPresetData(
        name=preset_def.name,
        run_config=preset_def.run_config,
        solid_selection=preset_def.solid_selection,
        mode=preset_def.mode,
        tags=preset_def.tags,
    )
