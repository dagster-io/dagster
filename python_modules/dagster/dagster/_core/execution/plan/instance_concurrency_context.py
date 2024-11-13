import time
from collections import defaultdict
from types import TracebackType
from typing import List, Optional, Set, Type

from typing_extensions import Self

from dagster._core.instance import DagsterInstance
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.storage.tags import PRIORITY_TAG

INITIAL_INTERVAL_VALUE = 1
STEP_UP_BASE = 1.1
MAX_CONCURRENCY_CLAIM_BLOCKED_INTERVAL = 15

MAX_ALLOWED_PRIORITY = 2**31 - 1


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

    def __init__(self, instance: DagsterInstance, dagster_run: DagsterRun):
        self._instance = instance
        self._run_id = dagster_run.run_id
        self._global_concurrency_keys = None
        self._pending_timeouts = defaultdict(float)
        self._pending_claim_counts = defaultdict(int)
        self._pending_claims = set()
        self._claims = set()
        try:
            self._run_priority = int(dagster_run.tags.get(PRIORITY_TAG, "0"))
        except ValueError:
            self._run_priority = 0

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
            if step_key in self._pending_timeouts:
                del self._pending_timeouts[step_key]
            if step_key in self._pending_claim_counts:
                del self._pending_claim_counts[step_key]

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

    def _sync_global_concurrency_keys(self) -> None:
        self._global_concurrency_keys = self._instance.event_log_storage.get_concurrency_keys()

    def claim(self, concurrency_key: str, step_key: str, step_priority: int = 0):
        if not self._instance.event_log_storage.supports_global_concurrency_limits:
            return True

        if concurrency_key not in self.global_concurrency_keys:
            # The initialization call will be a no-op if the limit is set by another process,
            # mitigating any race condition concerns
            if not self._instance.event_log_storage.initialize_concurrency_limit_to_default(
                concurrency_key
            ):
                # still default open if the limit table has not been initialized
                return True
            else:
                # sync the global concurrency keys to ensure we have the latest
                self._sync_global_concurrency_keys()

        if step_key in self._pending_claims:
            if time.time() > self._pending_timeouts[step_key]:
                del self._pending_timeouts[step_key]
            else:
                return False
        else:
            self._pending_claims.add(step_key)

        priority = self._run_priority + step_priority

        if abs(priority) > MAX_ALLOWED_PRIORITY:
            raise Exception(
                f"Tried to claim a concurrency slot with a priority {priority} that was not in the allowed range of a 32-bit signed integer."
            )

        claim_status = self._instance.event_log_storage.claim_concurrency_slot(
            concurrency_key, self._run_id, step_key, priority
        )

        if not claim_status.is_claimed:
            interval = _calculate_timeout_interval(
                claim_status.sleep_interval, self._pending_claim_counts[step_key]
            )
            self._pending_timeouts[step_key] = time.time() + interval
            self._pending_claim_counts[step_key] += 1
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


def _calculate_timeout_interval(sleep_interval: Optional[float], pending_claim_count: int) -> float:
    if sleep_interval is not None:
        return sleep_interval

    if pending_claim_count > 30:
        # with the current values, we will always hit the max by the 30th claim attempt
        return MAX_CONCURRENCY_CLAIM_BLOCKED_INTERVAL

    # increase the step up value exponentially, up to a max of 15 seconds (starting from 0)
    step_up_value = STEP_UP_BASE**pending_claim_count - 1
    interval = INITIAL_INTERVAL_VALUE + step_up_value
    return min(MAX_CONCURRENCY_CLAIM_BLOCKED_INTERVAL, interval)
