from typing import Optional
from dagster_managed_stacks import ManagedStackCheckResult, ManagedStackDiff, ManagedStackReconciler


class MyManagedStackReconciler(ManagedStackReconciler):
    def __init__(self, diff: ManagedStackDiff, apply_diff: Optional[ManagedStackDiff] = None):
        self._diff = diff
        self._apply_diff = apply_diff or diff

    def check(self) -> ManagedStackCheckResult:
        return self._diff

    def apply(self) -> ManagedStackCheckResult:
        return self._apply_diff
