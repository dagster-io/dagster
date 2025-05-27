from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional, Union

import dagster._check as check
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.schedule_definition import ScheduleDefinition
from dagster._core.definitions.sensor_definition import SensorDefinition
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition
from dagster._core.errors import DagsterInvariantViolationError
from dagster._record import replace

if TYPE_CHECKING:
    from dagster._core.definitions.run_config import RunConfig
    from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult
    from dagster._core.instance import DagsterInstance

from dagster._core.definitions.definitions_class import Definitions


def get_job_from_defs(
    name: str, defs: Definitions
) -> Optional[Union[JobDefinition, UnresolvedAssetJobDefinition]]:
    """Get the job from the definitions by its name."""
    return next(
        iter(job for job in (defs.jobs or []) if job.name == name),
        None,
    )


def has_job_defs_attached(sensor_def: SensorDefinition) -> bool:
    return any(target.has_job_def for target in sensor_def.targets)


def definitions_execute_job_in_process(
    definitions: Definitions,
    job_name: str,
    run_config: Optional[Union[Mapping[str, Any], "RunConfig"]] = None,
    instance: Optional["DagsterInstance"] = None,
    partition_key: Optional[str] = None,
    raise_on_error: bool = True,
    op_selection: Optional[Sequence[str]] = None,
    asset_selection: Optional[Sequence[AssetKey]] = None,
    run_id: Optional[str] = None,
    input_values: Optional[Mapping[str, object]] = None,
    tags: Optional[Mapping[str, str]] = None,
    resources: Optional[Mapping[str, object]] = None,
) -> "ExecuteInProcessResult":
    from dagster._core.definitions.job_base import RepoBackedJob
    from dagster._core.execution.execute_in_process import (
        core_execute_in_process,
        merge_run_tags,
        type_check_and_normalize_args,
    )

    run_config, op_selection, asset_selection, resource_defs, partition_key, input_values = (
        type_check_and_normalize_args(
            run_config=run_config,
            partition_key=partition_key,
            op_selection=op_selection,
            asset_selection=asset_selection,
            input_values=input_values,
            resources=resources,
        )
    )
    job = check.not_none(get_job_from_defs(job_name, definitions))
    if isinstance(job, UnresolvedAssetJobDefinition):
        raise DagsterInvariantViolationError(
            "Cannot execute an unresolved asset job. Please resolve the job by calling "
            "`resolve_to_job` on the job definition."
        )

    job_def = job.as_ephemeral_job(
        resource_defs=resource_defs,
        input_values=check.opt_mapping_param(
            input_values, "input_values", key_type=str, value_type=object
        ),
        op_selection=op_selection,
        asset_selection=asset_selection,
    )
    new_job_list = [job for job in (definitions.jobs or []) if job.name != job_name] + [job_def]
    schedules = [
        schedule.with_updated_job(job_def)
        if isinstance(schedule, ScheduleDefinition)
        and schedule.target.has_job_def
        and schedule.job.name == job_name
        else schedule
        for schedule in (definitions.schedules or [])
    ]
    sensors = []
    for sensor in definitions.sensors or []:
        if has_job_defs_attached(sensor) and any(job.name == job_name for job in sensor.jobs):
            sensors.append(
                sensor.with_updated_jobs(
                    [job for job in sensor.jobs if job.name != job_name] + [job_def]
                )
            )
        else:
            sensors.append(sensor)
    new_defs_obj = replace(definitions, jobs=new_job_list, schedules=schedules, sensors=sensors)
    resolved_repo = new_defs_obj.get_repository_def()
    wrapped_job = RepoBackedJob(job_name=job_name, repository_def=resolved_repo)
    return core_execute_in_process(
        job=wrapped_job,
        run_config=run_config,
        instance=instance,
        output_capturing_enabled=True,
        raise_on_error=raise_on_error,
        run_tags=merge_run_tags(
            job_def=job_def,
            partition_key=partition_key,
            tags=tags,
            asset_selection=asset_selection,
            instance=instance,
            run_config=run_config,
        ),
        run_id=run_id,
        asset_selection=frozenset(asset_selection),
    )
