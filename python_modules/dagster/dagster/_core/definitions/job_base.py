from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import TYPE_CHECKING, AbstractSet, Optional  # noqa: UP035

from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.events import AssetKey

if TYPE_CHECKING:
    from dagster._core.definitions.job_definition import JobDefinition
    from dagster._core.definitions.repository_definition import RepositoryDefinition


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
    def get_repository_definition(self) -> Optional["RepositoryDefinition"]:
        pass

    @abstractmethod
    def get_subset(
        self,
        *,
        op_selection: Optional[Iterable[str]] = None,
        asset_selection: Optional[AbstractSet[AssetKey]] = None,
        asset_check_selection: Optional[AbstractSet[AssetCheckKey]] = None,
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
    @abstractmethod
    def asset_check_selection(self) -> Optional[AbstractSet[AssetCheckKey]]:
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

    def get_repository_definition(self) -> Optional["RepositoryDefinition"]:
        return None

    def get_subset(
        self,
        *,
        op_selection: Optional[Iterable[str]] = None,
        asset_selection: Optional[AbstractSet[AssetKey]] = None,
        asset_check_selection: Optional[AbstractSet[AssetCheckKey]] = None,
    ) -> "InMemoryJob":
        op_selection = set(op_selection) if op_selection else None
        return InMemoryJob(
            self._job_def.get_subset(
                op_selection=op_selection,
                asset_selection=asset_selection,
                asset_check_selection=asset_check_selection,
            )
        )

    @property
    def op_selection(self) -> Optional[AbstractSet[str]]:
        return self._job_def.op_selection

    @property
    def asset_selection(self) -> Optional[AbstractSet[AssetKey]]:
        return self._job_def.asset_selection

    @property
    def asset_check_selection(self) -> Optional[AbstractSet[AssetCheckKey]]:
        return self._job_def.asset_check_selection


class RepoBackedJob(IJob):
    def __init__(
        self,
        job_name: str,
        repository_def: "RepositoryDefinition",
    ):
        self._job_name = job_name
        self._repository_def = repository_def

    def get_definition(self) -> "JobDefinition":
        return self._repository_def.get_job(self._job_name)

    def get_repository_definition(self) -> Optional["RepositoryDefinition"]:
        return self._repository_def

    @property
    def op_selection(self) -> Optional[AbstractSet[str]]:
        return self.get_definition().op_selection

    @property
    def asset_selection(self) -> Optional[AbstractSet[AssetKey]]:
        return self.get_definition().asset_selection

    @property
    def asset_check_selection(self) -> Optional[AbstractSet[AssetCheckKey]]:
        return self.get_definition().asset_check_selection

    def get_subset(
        self,
        *,
        op_selection: Optional[Iterable[str]] = None,
        asset_selection: Optional[AbstractSet[AssetKey]] = None,
        asset_check_selection: Optional[AbstractSet[AssetCheckKey]] = None,
    ) -> "RepoBackedJob":
        raise NotImplementedError("RepoBackedJob does not support get_subset")
