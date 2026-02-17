from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Optional

import dagster._check as check
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.run_config import RunConfig, convert_config_input
from dagster._core.definitions.schedule_definition import ScheduleDefinition
from dagster._core.definitions.sensor_definition import SensorDefinition
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition
from dagster._core.errors import DagsterInvariantViolationError
from dagster._record import replace

if TYPE_CHECKING:
    from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult
    from dagster._core.instance import DagsterInstance

from dagster._core.definitions.definitions_class import Definitions


def get_job_from_defs(
    name: str, defs: Definitions
) -> Optional[JobDefinition | UnresolvedAssetJobDefinition]:
    """Get the job from the definitions by its name."""
    return next(
        iter(job for job in (defs.jobs or []) if job.name == name),
        None,
    )


def has_job_defs_attached(sensor_def: SensorDefinition) -> bool:
    return any(target.has_job_def for target in sensor_def.targets)


def definitions_execute_job_in_process(
    *,
    defs: Definitions,
    job_name: str,
    instance: Optional["DagsterInstance"] = None,
    run_config: Optional[Mapping[str, Any] | RunConfig] = None,
    tags: Optional[Mapping[str, str]] = None,
) -> "ExecuteInProcessResult":
    """This was originally on Definitions as execute_job_in_process but was only used in 4 tests, so we
    moved it here on 2025-05-27 in order to reduce the surface area of the Definitions class.
    """
    from dagster._core.definitions.job_base import RepoBackedJob
    from dagster._core.execution.execute_in_process import core_execute_in_process, merge_run_tags

    run_config = check.opt_mapping_param(convert_config_input(run_config), "run_config")
    job = check.not_none(get_job_from_defs(job_name, defs))
    if isinstance(job, UnresolvedAssetJobDefinition):
        raise DagsterInvariantViolationError(
            "Cannot execute an unresolved asset job. Please resolve the job by calling "
            "`resolve_to_job` on the job definition."
        )

    job_def = job.as_ephemeral_job(
        resource_defs={},
        input_values={},
    )
    new_job_list = [job for job in (defs.jobs or []) if job.name != job_name] + [job_def]
    schedules = [
        schedule.with_updated_job(job_def)
        if isinstance(schedule, ScheduleDefinition)
        and schedule.target.has_job_def
        and schedule.job.name == job_name
        else schedule
        for schedule in (defs.schedules or [])
    ]
    sensors = []
    for sensor in defs.sensors or []:
        if has_job_defs_attached(sensor) and any(job.name == job_name for job in sensor.jobs):
            sensors.append(
                sensor.with_updated_jobs(
                    [job for job in sensor.jobs if job.name != job_name] + [job_def]
                )
            )
        else:
            sensors.append(sensor)
    new_defs_obj = replace(defs, jobs=new_job_list, schedules=schedules, sensors=sensors)
    resolved_repo = new_defs_obj.get_repository_def()
    wrapped_job = RepoBackedJob(job_name=job_name, repository_def=resolved_repo)
    return core_execute_in_process(
        job=wrapped_job,
        run_config=run_config,
        instance=instance,
        output_capturing_enabled=True,
        raise_on_error=True,
        run_tags=merge_run_tags(
            job_def=job_def,
            partition_key=None,
            tags=tags,
            asset_selection=None,
            instance=instance,
            run_config=run_config,
        ),
    )
