from abc import ABC

from dagster._core.instance import MayHaveInstanceWeakref, T_DagsterInstance

from .captured_log_manager import ComputeIOType as ComputeIOType


class ComputeLogManager(ABC, MayHaveInstanceWeakref[T_DagsterInstance]):
    """Abstract base class for storing unstructured compute logs (stdout/stderr) from the compute
    steps of pipeline solids.
    """

    def dispose(self):
        pass
