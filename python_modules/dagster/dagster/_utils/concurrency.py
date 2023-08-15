from datetime import datetime
from enum import Enum
from typing import NamedTuple, Optional, Set

from dagster import _check as check


class ConcurrencySlotStatus(Enum):
    BLOCKED = "BLOCKED"
    CLAIMED = "CLAIMED"


class ConcurrencyClaimStatus(
    NamedTuple(
        "_ConcurrencyClaimStatus",
        [
            ("concurrency_key", str),
            ("slot_status", ConcurrencySlotStatus),
            ("priority", Optional[int]),
            ("assigned_timestamp", Optional[datetime]),
            ("enqueued_timestamp", Optional[datetime]),
            ("sleep_interval", Optional[float]),
        ],
    )
):
    def __new__(
        cls,
        concurrency_key: str,
        slot_status: ConcurrencySlotStatus,
        priority: Optional[int] = None,
        assigned_timestamp: Optional[datetime] = None,
        enqueued_timestamp: Optional[datetime] = None,
        sleep_interval: Optional[float] = None,
    ):
        return super(ConcurrencyClaimStatus, cls).__new__(
            cls,
            check.str_param(concurrency_key, "concurrency_key"),
            check.inst_param(slot_status, "slot_status", ConcurrencySlotStatus),
            check.opt_int_param(priority, "priority"),
            check.opt_inst_param(assigned_timestamp, "assigned_timestamp", datetime),
            check.opt_inst_param(enqueued_timestamp, "enqueued_timestamp", datetime),
            check.opt_float_param(sleep_interval, "sleep_interval"),
        )

    @property
    def is_claimed(self):
        return self.slot_status == ConcurrencySlotStatus.CLAIMED

    @property
    def is_assigned(self):
        return self.assigned_timestamp is not None

    def with_slot_status(self, slot_status: ConcurrencySlotStatus):
        return ConcurrencyClaimStatus(
            concurrency_key=self.concurrency_key,
            slot_status=slot_status,
            priority=self.priority,
            assigned_timestamp=self.assigned_timestamp,
            enqueued_timestamp=self.enqueued_timestamp,
            sleep_interval=self.sleep_interval,
        )

    def with_sleep_interval(self, interval: float):
        return ConcurrencyClaimStatus(
            concurrency_key=self.concurrency_key,
            slot_status=self.slot_status,
            priority=self.priority,
            assigned_timestamp=self.assigned_timestamp,
            enqueued_timestamp=self.enqueued_timestamp,
            sleep_interval=interval,
        )


class ConcurrencyKeyInfo(
    NamedTuple(
        "_ConcurrencyKeyInfo",
        [
            ("concurrency_key", str),
            ("slot_count", int),
            ("active_slot_count", int),
            ("active_run_ids", Set[str]),
            ("pending_step_count", int),
            ("pending_run_ids", Set[str]),
            ("assigned_step_count", int),
            ("assigned_run_ids", Set[str]),
        ],
    )
):
    def __new__(
        cls,
        concurrency_key: str,
        slot_count: int,
        active_slot_count: int,
        active_run_ids: Set[str],
        pending_step_count: int,
        pending_run_ids: Set[str],
        assigned_step_count: int,
        assigned_run_ids: Set[str],
    ):
        return super(ConcurrencyKeyInfo, cls).__new__(
            cls,
            check.str_param(concurrency_key, "concurrency_key"),
            check.int_param(slot_count, "slot_count"),
            check.int_param(active_slot_count, "active_slot_count"),
            check.set_param(active_run_ids, "active_run_ids", of_type=str),
            check.int_param(pending_step_count, "pending_step_count"),
            check.set_param(pending_run_ids, "pending_run_ids", of_type=str),
            check.int_param(assigned_step_count, "assigned_step_count"),
            check.set_param(assigned_run_ids, "assigned_run_ids", of_type=str),
        )
