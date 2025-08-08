from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional, cast

import dagster._check as check
from dagster._utils import traced

if TYPE_CHECKING:
    from dagster._core.definitions.run_request import InstigatorType
    from dagster._core.instance.instance import DagsterInstance
    from dagster._core.remote_representation import RemoteSchedule, RemoteSensor
    from dagster._core.scheduler import Scheduler, SchedulerDebugInfo
    from dagster._core.scheduler.instigation import (
        InstigatorState,
        InstigatorStatus,
        InstigatorTick,
        TickData,
        TickStatus,
    )
    from dagster._core.storage.schedules import ScheduleStorage


class InstigatorMixin:
    """Mixin providing instigator, schedule, and sensor-related methods for DagsterInstance.

    This mixin requires that the concrete class also inherits from DomainsMixin to provide
    the storage_domain property.
    """

    # schedule/sensor storage properties

    @property
    def schedule_storage(self) -> Optional["ScheduleStorage"]:
        return cast("DagsterInstance", self)._schedule_storage  # noqa: SLF001

    @property
    def scheduler(self) -> Optional["Scheduler"]:
        return cast("DagsterInstance", self)._scheduler  # noqa: SLF001

    @property
    def scheduler_class(self) -> Optional[str]:
        return self.scheduler.__class__.__name__ if self.scheduler else None

    def schedules_directory(self) -> str:
        return cast("DagsterInstance", self).storage_domain.schedules_directory()

    # Schedule control

    def start_schedule(self, remote_schedule: "RemoteSchedule") -> "InstigatorState":
        return cast("DagsterInstance", self).scheduling_domain.start_schedule(remote_schedule)

    def stop_schedule(
        self,
        schedule_origin_id: str,
        schedule_selector_id: str,
        remote_schedule: Optional["RemoteSchedule"],
    ) -> "InstigatorState":
        return cast("DagsterInstance", self).scheduling_domain.stop_schedule(
            schedule_origin_id, schedule_selector_id, remote_schedule
        )

    def reset_schedule(self, remote_schedule: "RemoteSchedule") -> "InstigatorState":
        return cast("DagsterInstance", self).scheduling_domain.reset_schedule(remote_schedule)

    def scheduler_debug_info(self) -> "SchedulerDebugInfo":
        return cast("DagsterInstance", self).scheduling_domain.scheduler_debug_info()

    # Sensor control

    def start_sensor(self, remote_sensor: "RemoteSensor") -> "InstigatorState":
        return cast("DagsterInstance", self).scheduling_domain.start_sensor(remote_sensor)

    def stop_sensor(
        self,
        instigator_origin_id: str,
        selector_id: str,
        remote_sensor: Optional["RemoteSensor"],
    ) -> "InstigatorState":
        return cast("DagsterInstance", self).scheduling_domain.stop_sensor(
            instigator_origin_id, selector_id, remote_sensor
        )

    def reset_sensor(self, remote_sensor: "RemoteSensor") -> "InstigatorState":
        """If the given sensor has a default sensor status, then update the status to
        `InstigatorStatus.DECLARED_IN_CODE` in instigator storage.

        Args:
            instance (DagsterInstance): The current instance.
            remote_sensor (ExternalSensor): The sensor to reset.
        """
        return cast("DagsterInstance", self).scheduling_domain.reset_sensor(remote_sensor)

    # Instigator state management

    @traced
    def all_instigator_state(
        self,
        repository_origin_id: Optional[str] = None,
        repository_selector_id: Optional[str] = None,
        instigator_type: Optional["InstigatorType"] = None,
        instigator_statuses: Optional[set["InstigatorStatus"]] = None,
    ):
        return cast("DagsterInstance", self).scheduling_domain.all_instigator_state(
            repository_origin_id, repository_selector_id, instigator_type, instigator_statuses
        )

    @traced
    def get_instigator_state(self, origin_id: str, selector_id: str) -> Optional["InstigatorState"]:
        return cast("DagsterInstance", self).scheduling_domain.get_instigator_state(
            origin_id, selector_id
        )

    def add_instigator_state(self, state: "InstigatorState") -> "InstigatorState":
        return cast("DagsterInstance", self).scheduling_domain.add_instigator_state(state)

    def update_instigator_state(self, state: "InstigatorState") -> "InstigatorState":
        return cast("DagsterInstance", self).scheduling_domain.update_instigator_state(state)

    def delete_instigator_state(self, origin_id: str, selector_id: str) -> None:
        return cast("DagsterInstance", self).scheduling_domain.delete_instigator_state(
            origin_id, selector_id
        )

    # Tick operations

    @property
    def supports_batch_tick_queries(self) -> bool:
        return bool(self.schedule_storage and self.schedule_storage.supports_batch_queries)

    @traced
    def get_batch_ticks(
        self,
        selector_ids: Sequence[str],
        limit: Optional[int] = None,
        statuses: Optional[Sequence["TickStatus"]] = None,
    ) -> Mapping[str, Sequence["InstigatorTick"]]:
        if not self.schedule_storage:
            return {}
        return self.schedule_storage.get_batch_ticks(selector_ids, limit, statuses)

    @traced
    def get_tick(
        self, origin_id: str, selector_id: str, timestamp: float
    ) -> Optional["InstigatorTick"]:
        if not self.schedule_storage:
            return None
        matches = self.schedule_storage.get_ticks(
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
        if not self.schedule_storage:
            return []
        return self.schedule_storage.get_ticks(
            origin_id,
            selector_id,
            before=before,
            after=after,
            limit=limit,
            statuses=statuses,
        )

    def create_tick(self, tick_data: "TickData") -> "InstigatorTick":
        return check.not_none(self.schedule_storage).create_tick(tick_data)

    def update_tick(self, tick: "InstigatorTick"):
        return check.not_none(self.schedule_storage).update_tick(tick)

    def purge_ticks(
        self,
        origin_id: str,
        selector_id: str,
        before: float,
        tick_statuses: Optional[Sequence["TickStatus"]] = None,
    ) -> None:
        if self.schedule_storage:
            self.schedule_storage.purge_ticks(origin_id, selector_id, before, tick_statuses)

    def get_tick_retention_settings(
        self, instigator_type: "InstigatorType"
    ) -> Mapping["TickStatus", int]:
        return cast("DagsterInstance", self).scheduling_domain.get_tick_retention_settings(
            instigator_type
        )

    def get_tick_termination_check_interval(self) -> Optional[int]:
        return None

    # Maintenance

    def wipe_all_schedules(self) -> None:
        if self.scheduler:
            cast("Any", self.scheduler).wipe(cast("DagsterInstance", self))

        if self.schedule_storage:
            self.schedule_storage.wipe()

    def logs_path_for_schedule(self, schedule_origin_id: str) -> str:
        if not self.scheduler:
            raise RuntimeError("No scheduler configured")
        return self.scheduler.get_logs_path(cast("DagsterInstance", self), schedule_origin_id)
