import time
from collections import defaultdict
from types import TracebackType
from typing import (
    List,
    Set,
    Type,
)

from typing_extensions import Self

from dagster._core.instance import DagsterInstance

CONCURRENCY_CLAIM_BLOCKED_INTERVAL = 1


class GlobalConcurrencyContext:
    def __init__(self, instance: DagsterInstance, run_id: str):
        self._instance = instance
        self._run_id = run_id
        self._global_concurrency_keys = None
        self._pending_claims = defaultdict(float)
        self._claims = set()

    def __enter__(self) -> Self:
        self._context_guard = True
        return self

    def __exit__(
        self, exc_type: Type[Exception], exc_value: Exception, traceback: TracebackType
    ) -> None:
        to_clear = []
        for step_key in self._pending_claims.keys():
            self._instance.event_log_storage.free_concurrency_slot_for_step(self._run_id, step_key)
            to_clear.append(step_key)

        for step_key in to_clear:
            del self._pending_claims[step_key]

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
            if time.time() > self._pending_claims[step_key]:
                del self._pending_claims[step_key]
            else:
                return False

        claim_status = self._instance.event_log_storage.claim_concurrency_slot(
            concurrency_key, self._run_id, step_key, priority
        )

        if not claim_status.is_claimed:
            self._pending_claims[step_key] = time.time() + CONCURRENCY_CLAIM_BLOCKED_INTERVAL
            return False

        self._claims.add(step_key)
        return True

    def interval_to_next_pending_claim_check(self) -> float:
        if not self._pending_claims:
            return 0.0

        now = time.time()
        return min([ready_at - now for ready_at in self._pending_claims.values()])

    def pending_claim_steps(self) -> List[str]:
        return list(self._pending_claims.keys())

    def has_pending_claims(self) -> bool:
        return len(self._pending_claims) > 0

    def free_step(self, step_key) -> None:
        if step_key not in self._claims:
            return

        self._instance.event_log_storage.free_concurrency_slot_for_step(self._run_id, step_key)
        self._claims.remove(step_key)
