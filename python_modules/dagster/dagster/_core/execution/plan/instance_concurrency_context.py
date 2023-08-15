import time
from collections import defaultdict
from types import TracebackType
from typing import (
    List,
    Optional,
    Set,
    Type,
)

from typing_extensions import Self

from dagster._core.instance import DagsterInstance

DEFAULT_CONCURRENCY_CLAIM_BLOCKED_INTERVAL = 1


class InstanceConcurrencyContext:
    """This class is used to manage instance-scoped concurrency for a given run. It wraps the
    instance-based storage methods that obtains / releases concurrency slots, and provides a common
    interface for the active execution to throttle queries to the DB to check for available slots.

    It ensures that pending concurrency claims are freed upon exiting context.  It does not,
    however, free active slots that have been claimed. This is because the executor (depending on
    the executor type) may have launched processes that may continue to run even after the current
    context is exited.

    These active slots may be manually freed via the UI, which calls the event log storage method:
    `free_concurrency_slots_by_run_id`
    """

    def __init__(self, instance: DagsterInstance, run_id: str):
        self._instance = instance
        self._run_id = run_id
        self._global_concurrency_keys = None
        self._pending_timeouts = defaultdict(float)
        self._pending_claims = set()
        self._claims = set()

    def __enter__(self) -> Self:
        self._context_guard = True
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        to_clear = []
        for step_key in self._pending_claims:
            self._instance.event_log_storage.free_concurrency_slot_for_step(self._run_id, step_key)
            to_clear.append(step_key)

        for step_key in to_clear:
            del self._pending_timeouts[step_key]
            self._pending_claims.remove(step_key)

        self._context_guard = False

    @property
    def global_concurrency_keys(self) -> Set[str]:
        # lazily load the global concurrency keys, to avoid the DB fetch for plans that do not
        # have global concurrency limited keys
        if self._global_concurrency_keys is None:
            if not self._instance.event_log_storage.supports_global_concurrency_limits:
                self._global_concurrency_keys = set()
            else:
                self._global_concurrency_keys = (
                    self._instance.event_log_storage.get_concurrency_keys()
                )

        return self._global_concurrency_keys

    def claim(self, concurrency_key: str, step_key: str, priority: int = 0):
        if concurrency_key not in self.global_concurrency_keys:
            return True

        if step_key in self._pending_claims:
            if time.time() > self._pending_timeouts[step_key]:
                del self._pending_timeouts[step_key]
            else:
                return False
        else:
            self._pending_claims.add(step_key)

        claim_status = self._instance.event_log_storage.claim_concurrency_slot(
            concurrency_key, self._run_id, step_key, priority
        )

        if not claim_status.is_claimed:
            interval = (
                claim_status.sleep_interval
                if claim_status.sleep_interval
                else DEFAULT_CONCURRENCY_CLAIM_BLOCKED_INTERVAL
            )
            self._pending_timeouts[step_key] = time.time() + interval
            return False

        if step_key in self._pending_claims:
            self._pending_claims.remove(step_key)

        self._claims.add(step_key)
        return True

    def interval_to_next_pending_claim_check(self) -> float:
        if not self._pending_claims:
            return 0.0

        now = time.time()
        return min([0, *[ready_at - now for ready_at in self._pending_timeouts.values()]])

    def pending_claim_steps(self) -> List[str]:
        return list(self._pending_claims)

    def has_pending_claims(self) -> bool:
        return len(self._pending_claims) > 0

    def free_step(self, step_key) -> None:
        if step_key not in self._claims:
            return

        self._instance.event_log_storage.free_concurrency_slot_for_step(self._run_id, step_key)
        self._claims.remove(step_key)
