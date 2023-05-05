from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, AbstractSet, Iterable, Optional

from typing_extensions import Self

from dagster._core.definitions.events import AssetKey

if TYPE_CHECKING:
    from .job_definition import JobDefinition


class IJob(ABC):
    """IJob is a wrapper interface for JobDefinitions to be used as parameters to Dagster's
    core execution APIs.  This enables these execution APIs to operate on both in memory job
    definitions to be executed in the current process (InMemoryJob) as well as definitions that
    can be reconstructed and executed in a different process (ReconstructableJob).
    """

    @abstractmethod
    def get_definition(self) -> "JobDefinition":
        pass

    @abstractmethod
    def get_subset(
        self,
        *,
        op_selection: Optional[Iterable[str]] = None,
        asset_selection: Optional[AbstractSet[AssetKey]] = None,
    ) -> "IJob":
        pass

    @property
    @abstractmethod
    def op_selection(self) -> Optional[AbstractSet[str]]:
        pass

    @property
    @abstractmethod
    def asset_selection(self) -> Optional[AbstractSet[AssetKey]]:
        pass

    @property
    def resolved_op_selection(self) -> Optional[AbstractSet[str]]:
        return set(self.op_selection) if self.op_selection else None


class InMemoryJob(IJob):
    def __init__(
        self,
        job_def: "JobDefinition",
    ):
        self._job_def = job_def

    def get_definition(self) -> "JobDefinition":
        return self._job_def

    def get_subset(
        self,
        *,
        op_selection: Optional[Iterable[str]] = None,
        asset_selection: Optional[AbstractSet[AssetKey]] = None,
    ) -> Self:
        op_selection = set(op_selection) if op_selection else None
        return InMemoryJob(
            self._job_def.get_subset(op_selection=op_selection, asset_selection=asset_selection)
        )

    @property
    def op_selection(self) -> Optional[AbstractSet[str]]:
        return self._job_def.op_selection

    @property
    def asset_selection(self) -> Optional[AbstractSet[AssetKey]]:
        return self._job_def.asset_selection
