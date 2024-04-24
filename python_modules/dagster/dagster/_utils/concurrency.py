import os
from datetime import datetime
from enum import Enum
from typing import List, NamedTuple, Optional, Set

from dagster import _check as check


def get_max_concurrency_limit_value() -> int:
    return int(os.getenv("DAGSTER_MAX_GLOBAL_OP_CONCURRENCY_LIMIT", "1000"))


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


class PendingStepInfo(
    NamedTuple(
        "_PendingStepInfo",
        [
            ("run_id", str),
            ("step_key", str),
            ("enqueued_timestamp", datetime),
            ("assigned_timestamp", Optional[datetime]),
            ("priority", Optional[int]),
        ],
    )
):
    def __new__(
        cls,
        run_id: int,
        step_key: str,
        enqueued_timestamp: datetime,
        assigned_timestamp: Optional[datetime],
        priority: Optional[int],
    ):
        return super(PendingStepInfo, cls).__new__(
            cls,
            check.str_param(run_id, "run_id"),
            check.str_param(step_key, "step_key"),
            check.inst_param(enqueued_timestamp, "enqueued_timestamp", datetime),
            check.opt_inst_param(assigned_timestamp, "assigned_timestamp", datetime),
            check.opt_int_param(priority, "priority"),
        )


class ClaimedSlotInfo(
    NamedTuple(
        "_ClaimedSlotInfo",
        [
            ("run_id", str),
            ("step_key", str),
        ],
    )
):
    def __new__(cls, run_id: int, step_key: str):
        return super(ClaimedSlotInfo, cls).__new__(
            cls,
            check.str_param(run_id, "run_id"),
            check.str_param(step_key, "step_key"),
        )


class ConcurrencyKeyInfo(
    NamedTuple(
        "_ConcurrencyKeyInfo",
        [
            ("concurrency_key", str),
            ("slot_count", int),
            ("claimed_slots", List[ClaimedSlotInfo]),
            ("pending_steps", List[PendingStepInfo]),
        ],
    )
):
    def __new__(
        cls,
        concurrency_key: str,
        slot_count: int,
        claimed_slots: List[ClaimedSlotInfo],
        pending_steps: List[PendingStepInfo],
    ):
        return super(ConcurrencyKeyInfo, cls).__new__(
            cls,
            check.str_param(concurrency_key, "concurrency_key"),
            check.int_param(slot_count, "slot_count"),
            check.list_param(claimed_slots, "claimed_slots", of_type=ClaimedSlotInfo),
            check.list_param(pending_steps, "pending_steps", of_type=PendingStepInfo),
        )

    ###################################################
    # Fields that we need to keep around for backcompat
    ###################################################
    @property
    def active_slot_count(self) -> int:
        return len(self.claimed_slots)

    @property
    def active_run_ids(self) -> Set[str]:
        return set([slot.run_id for slot in self.claimed_slots])

    @property
    def pending_step_count(self) -> int:
        # here pending steps are steps that are not assigned
        return len([step for step in self.pending_steps if step.assigned_timestamp is None])

    @property
    def pending_run_ids(self) -> Set[str]:
        # here pending steps are steps that are not assigned
        return set([step.run_id for step in self.pending_steps if step.assigned_timestamp is None])

    @property
    def assigned_step_count(self) -> int:
        return len([step for step in self.pending_steps if step.assigned_timestamp is not None])

    @property
    def assigned_run_ids(self) -> Set[str]:
        return set(
            [step.run_id for step in self.pending_steps if step.assigned_timestamp is not None]
        )
