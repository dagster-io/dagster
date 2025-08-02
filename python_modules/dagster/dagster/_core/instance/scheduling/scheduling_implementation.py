"""Business logic functions for scheduling operations moved from DagsterInstance."""

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Optional, cast

import yaml

import dagster._check as check
from dagster._core.instance.config import get_default_tick_retention_settings
from dagster._time import get_current_timestamp

if TYPE_CHECKING:
    from dagster._core.definitions.run_request import InstigatorType
    from dagster._core.execution.backfill import (
        BulkActionsFilter,
        BulkActionStatus,
        PartitionBackfill,
    )
    from dagster._core.instance.scheduling.scheduling_instance_ops import SchedulingInstanceOps
    from dagster._core.remote_representation.external import RemoteSchedule, RemoteSensor
    from dagster._core.scheduler import SchedulerDebugInfo
    from dagster._core.scheduler.instigation import InstigatorState, InstigatorStatus
    from dagster._core.storage.schedules.base import TickStatus


def start_schedule(
    ops: "SchedulingInstanceOps", remote_schedule: "RemoteSchedule"
) -> "InstigatorState":
    """Start schedule - moved from DagsterInstance.start_schedule()."""
    return ops.scheduler.start_schedule(ops.instance, remote_schedule)  # type: ignore


def stop_schedule(
    ops: "SchedulingInstanceOps",
    schedule_origin_id: str,
    schedule_selector_id: str,
    remote_schedule: Optional["RemoteSchedule"],
) -> "InstigatorState":
    """Stop schedule - moved from DagsterInstance.stop_schedule()."""
    return ops.scheduler.stop_schedule(  # type: ignore
        ops.instance, schedule_origin_id, schedule_selector_id, remote_schedule
    )


def reset_schedule(
    ops: "SchedulingInstanceOps", remote_schedule: "RemoteSchedule"
) -> "InstigatorState":
    """Reset schedule - moved from DagsterInstance.reset_schedule()."""
    return ops.scheduler.reset_schedule(ops.instance, remote_schedule)  # type: ignore


def scheduler_debug_info(ops: "SchedulingInstanceOps") -> "SchedulerDebugInfo":
    """Get scheduler debug info - moved from DagsterInstance.scheduler_debug_info()."""
    from dagster._core.definitions.run_request import InstigatorType
    from dagster._core.scheduler import SchedulerDebugInfo

    errors = []

    schedules: list[str] = []
    for schedule_state in ops.all_instigator_state(instigator_type=InstigatorType.SCHEDULE):
        schedule_info: Mapping[str, Mapping[str, object]] = {
            schedule_state.instigator_name: {
                "status": schedule_state.status.value,
                "cron_schedule": schedule_state.instigator_data.cron_schedule,  # type: ignore
                "schedule_origin_id": schedule_state.instigator_origin_id,
                "repository_origin_id": schedule_state.repository_origin_id,
            }
        }

        schedules.append(yaml.safe_dump(schedule_info, default_flow_style=False))

    return SchedulerDebugInfo(
        scheduler_config_info=ops.info_str_for_component("Scheduler", ops.scheduler),
        scheduler_info=ops.scheduler.debug_info(),  # type: ignore
        schedule_storage=schedules,
        errors=errors,
    )


def start_sensor(ops: "SchedulingInstanceOps", remote_sensor: "RemoteSensor") -> "InstigatorState":
    """Start sensor - moved from DagsterInstance.start_sensor()."""
    from dagster._core.definitions.run_request import InstigatorType
    from dagster._core.scheduler.instigation import (
        InstigatorState,
        InstigatorStatus,
        SensorInstigatorData,
    )

    stored_state = ops.get_instigator_state(
        remote_sensor.get_remote_origin_id(), remote_sensor.selector_id
    )

    computed_state = remote_sensor.get_current_instigator_state(stored_state)
    if computed_state.is_running:
        return computed_state

    if not stored_state:
        return ops.add_instigator_state(
            InstigatorState(
                remote_sensor.get_remote_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
                SensorInstigatorData(
                    min_interval=remote_sensor.min_interval_seconds,
                    last_sensor_start_timestamp=get_current_timestamp(),
                    sensor_type=remote_sensor.sensor_type,
                ),
            )
        )
    else:
        data = cast("SensorInstigatorData", stored_state.instigator_data)
        return ops.update_instigator_state(
            stored_state.with_status(InstigatorStatus.RUNNING).with_data(
                data.with_sensor_start_timestamp(get_current_timestamp())
            )
        )


def stop_sensor(
    ops: "SchedulingInstanceOps",
    instigator_origin_id: str,
    selector_id: str,
    remote_sensor: Optional["RemoteSensor"],
) -> "InstigatorState":
    """Stop sensor - moved from DagsterInstance.stop_sensor()."""
    from dagster._core.definitions.run_request import InstigatorType
    from dagster._core.scheduler.instigation import (
        InstigatorState,
        InstigatorStatus,
        SensorInstigatorData,
    )

    stored_state = ops.get_instigator_state(instigator_origin_id, selector_id)
    computed_state: InstigatorState
    if remote_sensor:
        computed_state = remote_sensor.get_current_instigator_state(stored_state)
    else:
        computed_state = check.not_none(stored_state)

    if not computed_state.is_running:
        return computed_state

    if not stored_state:
        assert remote_sensor
        return ops.add_instigator_state(
            InstigatorState(
                remote_sensor.get_remote_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.STOPPED,
                SensorInstigatorData(
                    min_interval=remote_sensor.min_interval_seconds,
                    sensor_type=remote_sensor.sensor_type,
                ),
            )
        )
    else:
        return ops.update_instigator_state(stored_state.with_status(InstigatorStatus.STOPPED))


def reset_sensor(ops: "SchedulingInstanceOps", remote_sensor: "RemoteSensor") -> "InstigatorState":
    """Reset sensor - moved from DagsterInstance.reset_sensor()."""
    from dagster._core.definitions.run_request import InstigatorType
    from dagster._core.scheduler.instigation import (
        InstigatorState,
        InstigatorStatus,
        SensorInstigatorData,
    )

    stored_state = ops.get_instigator_state(
        remote_sensor.get_remote_origin_id(), remote_sensor.selector_id
    )
    new_status = InstigatorStatus.DECLARED_IN_CODE

    if not stored_state:
        new_instigator_data = SensorInstigatorData(
            min_interval=remote_sensor.min_interval_seconds,
            sensor_type=remote_sensor.sensor_type,
        )

        reset_state = ops.add_instigator_state(
            state=InstigatorState(
                remote_sensor.get_remote_origin(),
                InstigatorType.SENSOR,
                new_status,
                new_instigator_data,
            )
        )
    else:
        reset_state = ops.update_instigator_state(state=stored_state.with_status(new_status))

    return reset_state


def all_instigator_state(
    ops: "SchedulingInstanceOps",
    repository_origin_id: Optional[str] = None,
    repository_selector_id: Optional[str] = None,
    instigator_type: Optional["InstigatorType"] = None,
    instigator_statuses: Optional[set["InstigatorStatus"]] = None,
):
    """Get all instigator states - moved from DagsterInstance.all_instigator_state()."""
    if not ops.schedule_storage:
        check.failed("Schedule storage not available")
    return ops.schedule_storage.all_instigator_state(
        repository_origin_id,
        repository_selector_id,
        instigator_type,
        instigator_statuses,
    )


def get_instigator_state(
    ops: "SchedulingInstanceOps", origin_id: str, selector_id: str
) -> Optional["InstigatorState"]:
    """Get instigator state - moved from DagsterInstance.get_instigator_state()."""
    if not ops.schedule_storage:
        check.failed("Schedule storage not available")
    return ops.schedule_storage.get_instigator_state(origin_id, selector_id)


def add_instigator_state(
    ops: "SchedulingInstanceOps", state: "InstigatorState"
) -> "InstigatorState":
    """Add instigator state - moved from DagsterInstance.add_instigator_state()."""
    if not ops.schedule_storage:
        check.failed("Schedule storage not available")
    return ops.schedule_storage.add_instigator_state(state)


def update_instigator_state(
    ops: "SchedulingInstanceOps", state: "InstigatorState"
) -> "InstigatorState":
    """Update instigator state - moved from DagsterInstance.update_instigator_state()."""
    if not ops.schedule_storage:
        check.failed("Schedule storage not available")
    return ops.schedule_storage.update_instigator_state(state)


def delete_instigator_state(ops: "SchedulingInstanceOps", origin_id: str, selector_id: str) -> None:
    """Delete instigator state - moved from DagsterInstance.delete_instigator_state()."""
    return ops.schedule_storage.delete_instigator_state(origin_id, selector_id)  # type: ignore  # (possible none)


def get_backfills(
    ops: "SchedulingInstanceOps",
    filters: Optional["BulkActionsFilter"] = None,
    cursor: Optional[str] = None,
    limit: Optional[int] = None,
    status: Optional["BulkActionStatus"] = None,
) -> Sequence["PartitionBackfill"]:
    """Get backfills - moved from DagsterInstance.get_backfills()."""
    return ops.run_storage.get_backfills(status=status, cursor=cursor, limit=limit, filters=filters)


def get_backfills_count(
    ops: "SchedulingInstanceOps", filters: Optional["BulkActionsFilter"] = None
) -> int:
    """Get backfills count - moved from DagsterInstance.get_backfills_count()."""
    return ops.run_storage.get_backfills_count(filters=filters)


def get_backfill(ops: "SchedulingInstanceOps", backfill_id: str) -> Optional["PartitionBackfill"]:
    """Get single backfill - moved from DagsterInstance.get_backfill()."""
    return ops.run_storage.get_backfill(backfill_id)


def add_backfill(ops: "SchedulingInstanceOps", partition_backfill: "PartitionBackfill") -> None:
    """Add backfill - moved from DagsterInstance.add_backfill()."""
    ops.run_storage.add_backfill(partition_backfill)


def update_backfill(ops: "SchedulingInstanceOps", partition_backfill: "PartitionBackfill") -> None:
    """Update backfill - moved from DagsterInstance.update_backfill()."""
    ops.run_storage.update_backfill(partition_backfill)


def get_tick_retention_settings(
    ops: "SchedulingInstanceOps", instigator_type: "InstigatorType"
) -> Mapping["TickStatus", int]:
    """Get tick retention settings - moved from DagsterInstance.get_tick_retention_settings()."""
    from dagster._core.definitions.run_request import InstigatorType
    from dagster._core.instance.config import get_tick_retention_settings

    retention_settings = ops.get_settings("retention")

    if instigator_type == InstigatorType.SCHEDULE:
        tick_settings = retention_settings.get("schedule")
    elif instigator_type == InstigatorType.SENSOR:
        tick_settings = retention_settings.get("sensor")
    elif instigator_type == InstigatorType.AUTO_MATERIALIZE:
        tick_settings = retention_settings.get("auto_materialize")
    else:
        raise Exception(f"Unexpected instigator type {instigator_type}")

    default_tick_settings = get_default_tick_retention_settings(instigator_type)
    return get_tick_retention_settings(tick_settings, default_tick_settings)
