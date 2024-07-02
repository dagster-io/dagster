from typing import Optional

from dagster_managed_elements import (
    ManagedElementDiff,
    ManagedElementReconciler,
    ManagedElementCheckResult,
)


class MyManagedElementReconciler(ManagedElementReconciler):
    def __init__(self, diff: ManagedElementDiff, apply_diff: Optional[ManagedElementDiff] = None):
        self._diff = diff
        self._apply_diff = apply_diff or diff

    def check(self, **kwargs) -> ManagedElementCheckResult:
        return self._diff

    def apply(self, **kwargs) -> ManagedElementCheckResult:
        return self._apply_diff
