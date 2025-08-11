"""Scheduling methods implementation - consolidated from SchedulingDomain."""

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Optional

import dagster._check as check
from dagster._utils import traced

if TYPE_CHECKING:
    from dagster._core.definitions.run_request import InstigatorType
    from dagster._core.execution.backfill import (
        BulkActionsFilter,
        BulkActionStatus,
        PartitionBackfill,
    )
    from dagster._core.instance.instance import DagsterInstance
    from dagster._core.remote_representation.external import RemoteSchedule, RemoteSensor
    from dagster._core.scheduler import Scheduler, SchedulerDebugInfo
    from dagster._core.scheduler.instigation import (
        InstigatorState,
        InstigatorStatus,
        InstigatorTick,
        TickData,
        TickStatus,
    )
    from dagster._core.storage.schedules import ScheduleStorage


class SchedulingMethods:
    """Mixin class containing scheduling-related functionality for DagsterInstance.

    This class provides methods for schedule, sensor, and backfill management.
    All methods are implemented as instance methods that DagsterInstance inherits.
    """

    @property
    def _instance(self) -> "DagsterInstance":
        """Cast self to DagsterInstance for type-safe access to instance methods and properties."""
        from dagster._core.instance.instance import DagsterInstance

        return check.inst(self, DagsterInstance)

    # Private member access wrappers with consolidated type: ignore
    @property
    def _scheduler_impl(self):
        """Access to scheduler."""
        return self._instance._scheduler  # noqa: SLF001

    @property
    def _schedule_storage_impl(self):
        """Access to schedule storage."""
        return self._instance._schedule_storage  # noqa: SLF001

    @property
    def _run_storage_impl(self):
        """Access to run storage."""
        return self._instance._run_storage  # noqa: SLF001

    # Public properties for schedule/sensor storage - moved from InstigatorMixin

    @property
    def schedule_storage(self) -> Optional["ScheduleStorage"]:
        """Get schedule storage."""
        return self._schedule_storage_impl

    @property
    def scheduler(self) -> Optional["Scheduler"]:
        """Get scheduler."""
        return self._scheduler_impl

    @property
    def scheduler_class(self) -> Optional[str]:
        """Get scheduler class name."""
        return self.scheduler.__class__.__name__ if self.scheduler else None

    def schedules_directory(self) -> str:
        """Get schedules directory - delegates to StorageMethods."""
        # Access the method from StorageMethods mixin
        from dagster._core.instance.methods.storage_methods import StorageMethods

        return StorageMethods.schedules_directory(self._instance)

    def start_schedule(self, remote_schedule: "RemoteSchedule") -> "InstigatorState":
        """Start schedule - moved from DagsterInstance.start_schedule()."""
        if not self._scheduler_impl:
            check.failed("Scheduler not available")
        return self._scheduler_impl.start_schedule(self._instance, remote_schedule)

    def stop_schedule(
        self,
        schedule_origin_id: str,
        schedule_selector_id: str,
        remote_schedule: Optional["RemoteSchedule"] = None,
    ) -> "InstigatorState":
        """Stop schedule - moved from DagsterInstance.stop_schedule()."""
        if not self._scheduler_impl:
            check.failed("Scheduler not available")
        return self._scheduler_impl.stop_schedule(
            self._instance, schedule_origin_id, schedule_selector_id, remote_schedule
        )

    def reset_schedule(self, remote_schedule: "RemoteSchedule") -> "InstigatorState":
        """Reset schedule - moved from DagsterInstance.reset_schedule()."""
        if not self._scheduler_impl:
            check.failed("Scheduler not available")
        return self._scheduler_impl.reset_schedule(self._instance, remote_schedule)

    def start_sensor(self, remote_sensor: "RemoteSensor") -> "InstigatorState":
        """Start sensor - moved from DagsterInstance.start_sensor()."""
        from typing import cast

        from dagster._core.definitions.run_request import InstigatorType
        from dagster._core.scheduler.instigation import (
            InstigatorState,
            InstigatorStatus,
            SensorInstigatorData,
        )
        from dagster._time import get_current_timestamp

        stored_state = self.get_instigator_state(
            remote_sensor.get_remote_origin_id(), remote_sensor.selector_id
        )

        computed_state = remote_sensor.get_current_instigator_state(stored_state)
        if computed_state.is_running:
            return computed_state

        if not stored_state:
            return self.add_instigator_state(
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
            return self.update_instigator_state(
                stored_state.with_status(InstigatorStatus.RUNNING).with_data(
                    data.with_sensor_start_timestamp(get_current_timestamp())
                )
            )

    def stop_sensor(
        self,
        instigator_origin_id: str,
        selector_id: str,
        remote_sensor: Optional["RemoteSensor"],
    ) -> "InstigatorState":
        """Stop sensor - moved from DagsterInstance.stop_sensor()."""
        import dagster._check as check
        from dagster._core.definitions.run_request import InstigatorType
        from dagster._core.scheduler.instigation import (
            InstigatorState,
            InstigatorStatus,
            SensorInstigatorData,
        )

        stored_state = self.get_instigator_state(instigator_origin_id, selector_id)
        computed_state: InstigatorState
        if remote_sensor:
            computed_state = remote_sensor.get_current_instigator_state(stored_state)
        else:
            computed_state = check.not_none(stored_state)

        if not computed_state.is_running:
            return computed_state

        if not stored_state:
            assert remote_sensor
            return self.add_instigator_state(
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
            return self.update_instigator_state(stored_state.with_status(InstigatorStatus.STOPPED))

    def reset_sensor(self, remote_sensor: "RemoteSensor") -> "InstigatorState":
        """Reset sensor - moved from DagsterInstance.reset_sensor()."""
        from dagster._core.definitions.run_request import InstigatorType
        from dagster._core.scheduler.instigation import (
            InstigatorState,
            InstigatorStatus,
            SensorInstigatorData,
        )

        stored_state = self.get_instigator_state(
            remote_sensor.get_remote_origin_id(), remote_sensor.selector_id
        )
        new_status = InstigatorStatus.DECLARED_IN_CODE

        if not stored_state:
            new_instigator_data = SensorInstigatorData(
                min_interval=remote_sensor.min_interval_seconds,
                sensor_type=remote_sensor.sensor_type,
            )

            reset_state = self.add_instigator_state(
                state=InstigatorState(
                    remote_sensor.get_remote_origin(),
                    InstigatorType.SENSOR,
                    new_status,
                    new_instigator_data,
                )
            )
        else:
            reset_state = self.update_instigator_state(state=stored_state.with_status(new_status))

        return reset_state

    @traced
    def all_instigator_state(
        self,
        repository_origin_id: Optional[str] = None,
        repository_selector_id: Optional[str] = None,
        instigator_type: Optional["InstigatorType"] = None,
        instigator_statuses: Optional[set["InstigatorStatus"]] = None,
    ) -> Sequence["InstigatorState"]:
        """Get all instigator states - moved from DagsterInstance.all_instigator_state()."""
        if not self._schedule_storage_impl:
            check.failed("Schedule storage not available")
        return self._schedule_storage_impl.all_instigator_state(
            repository_origin_id=repository_origin_id,
            repository_selector_id=repository_selector_id,
            instigator_type=instigator_type,
            instigator_statuses=instigator_statuses,
        )

    def get_instigator_state(self, origin_id: str, selector_id: str) -> Optional["InstigatorState"]:
        """Get instigator state - moved from DagsterInstance.get_instigator_state()."""
        if not self._schedule_storage_impl:
            check.failed("Schedule storage not available")
        return self._schedule_storage_impl.get_instigator_state(origin_id, selector_id)

    def add_instigator_state(self, state: "InstigatorState") -> "InstigatorState":
        """Add instigator state - moved from DagsterInstance.add_instigator_state()."""
        if not self._schedule_storage_impl:
            check.failed("Schedule storage not available")
        return self._schedule_storage_impl.add_instigator_state(state)

    def update_instigator_state(self, state: "InstigatorState") -> "InstigatorState":
        """Update instigator state - moved from DagsterInstance.update_instigator_state()."""
        if not self._schedule_storage_impl:
            check.failed("Schedule storage not available")
        return self._schedule_storage_impl.update_instigator_state(state)

    def delete_instigator_state(self, origin_id: str, selector_id: str) -> None:
        """Delete instigator state - moved from DagsterInstance.delete_instigator_state()."""
        if not self._schedule_storage_impl:
            check.failed("Schedule storage not available")
        return self._schedule_storage_impl.delete_instigator_state(origin_id, selector_id)

    def get_backfills(
        self,
        filters: Optional["BulkActionsFilter"] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        status: Optional["BulkActionStatus"] = None,
    ) -> Sequence["PartitionBackfill"]:
        """Get backfills - moved from DagsterInstance.get_backfills()."""
        return self._run_storage_impl.get_backfills(
            status=status, cursor=cursor, limit=limit, filters=filters
        )

    def get_backfills_count(self, filters: Optional["BulkActionsFilter"] = None) -> int:
        """Get backfills count - moved from DagsterInstance.get_backfills_count()."""
        return self._run_storage_impl.get_backfills_count(filters=filters)

    def get_backfill(self, backfill_id: str) -> Optional["PartitionBackfill"]:
        """Get backfill - moved from DagsterInstance.get_backfill()."""
        return self._run_storage_impl.get_backfill(backfill_id)

    def add_backfill(self, partition_backfill: "PartitionBackfill") -> None:
        """Add backfill - moved from DagsterInstance.add_backfill()."""
        self._run_storage_impl.add_backfill(partition_backfill)

    def update_backfill(self, partition_backfill: "PartitionBackfill") -> None:
        """Update backfill - moved from DagsterInstance.update_backfill()."""
        self._run_storage_impl.update_backfill(partition_backfill)

    def wipe_all_schedules(self) -> None:
        """Wipe all schedules - moved from DagsterInstance.wipe_all_schedules()."""
        if self._scheduler_impl:
            self._scheduler_impl.wipe(self._instance)  # type: ignore

        if not self._schedule_storage_impl:
            check.failed("Schedule storage not available")
        self._schedule_storage_impl.wipe()

    def logs_path_for_schedule(self, schedule_origin_id: str) -> str:
        """Get logs path for schedule - moved from DagsterInstance.logs_path_for_schedule()."""
        if not self._scheduler_impl:
            check.failed("Scheduler not available")
        return self._scheduler_impl.get_logs_path(self._instance, schedule_origin_id)

    def scheduler_debug_info(self) -> "SchedulerDebugInfo":
        """Get scheduler debug info - moved from DagsterInstance.scheduler_debug_info()."""
        from collections.abc import Mapping

        from dagster._core.definitions.run_request import InstigatorType
        from dagster._core.scheduler import SchedulerDebugInfo

        errors = []

        schedules: list[str] = []
        for schedule_state in self.all_instigator_state(instigator_type=InstigatorType.SCHEDULE):
            schedule_info: Mapping[str, Mapping[str, object]] = {
                schedule_state.instigator_name: {
                    "status": schedule_state.status.value,
                    "repository_origin_id": schedule_state.repository_origin_id,
                    "schedule_origin_id": schedule_state.instigator_origin_id,
                    "cron_schedule": getattr(schedule_state.instigator_data, "cron_schedule", None)
                    if schedule_state.instigator_data
                    else None,
                }
            }

            schedules.append(str(schedule_info))

        sensors: list[str] = []
        for sensor_state in self.all_instigator_state(instigator_type=InstigatorType.SENSOR):
            sensor_info: Mapping[str, Mapping[str, object]] = {
                sensor_state.instigator_name: {
                    "status": sensor_state.status.value,
                    "repository_origin_id": sensor_state.repository_origin_id,
                    "sensor_origin_id": sensor_state.instigator_origin_id,
                }
            }

            sensors.append(str(sensor_info))

        return SchedulerDebugInfo(
            errors=errors,
            scheduler_config_info=self._instance.scheduler_class or "",
            scheduler_info=self._instance.scheduler.debug_info()
            if self._instance.scheduler
            else "",
            schedule_storage=schedules + sensors,
        )

    def get_tick_retention_settings(
        self, instigator_type: "InstigatorType"
    ) -> Mapping["TickStatus", int]:
        """Get tick retention settings - moved from DagsterInstance.get_tick_retention_settings()."""
        from dagster._core.definitions.run_request import InstigatorType
        from dagster._core.instance.config import (
            get_default_tick_retention_settings,
            get_tick_retention_settings,
        )

        retention_settings = self._instance.get_settings("retention")

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

    # Tick operations - moved from InstigatorMixin

    @property
    def supports_batch_tick_queries(self) -> bool:
        return bool(
            self._schedule_storage_impl and self._schedule_storage_impl.supports_batch_queries
        )

    @traced
    def get_batch_ticks(
        self,
        selector_ids: Sequence[str],
        limit: Optional[int] = None,
        statuses: Optional[Sequence["TickStatus"]] = None,
    ) -> Mapping[str, Sequence["InstigatorTick"]]:
        if not self._schedule_storage_impl:
            return {}
        return self._schedule_storage_impl.get_batch_ticks(selector_ids, limit, statuses)

    @traced
    def get_tick(
        self, origin_id: str, selector_id: str, timestamp: float
    ) -> Optional["InstigatorTick"]:
        if not self._schedule_storage_impl:
            return None
        matches = self._schedule_storage_impl.get_ticks(
            origin_id, selector_id, before=timestamp + 1, after=timestamp - 1, limit=1
        )
        return matches[0] if len(matches) else None

    @traced
    def get_ticks(
        self,
        origin_id: str,
        selector_id: str,
        before: Optional[float] = None,
        after: Optional[float] = None,
        limit: Optional[int] = None,
        statuses: Optional[Sequence["TickStatus"]] = None,
    ) -> Sequence["InstigatorTick"]:
        if not self._schedule_storage_impl:
            return []
        return self._schedule_storage_impl.get_ticks(
            origin_id,
            selector_id,
            before=before,
            after=after,
            limit=limit,
            statuses=statuses,
        )

    def create_tick(self, tick_data: "TickData") -> "InstigatorTick":
        return check.not_none(self._schedule_storage_impl).create_tick(tick_data)

    def update_tick(self, tick: "InstigatorTick"):
        return check.not_none(self._schedule_storage_impl).update_tick(tick)

    def purge_ticks(
        self,
        origin_id: str,
        selector_id: str,
        before: float,
        tick_statuses: Optional[Sequence["TickStatus"]] = None,
    ) -> None:
        if self._schedule_storage_impl:
            self._schedule_storage_impl.purge_ticks(origin_id, selector_id, before, tick_statuses)

    def get_tick_termination_check_interval(self) -> Optional[int]:
        return None
