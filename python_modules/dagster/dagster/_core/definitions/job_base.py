from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, AbstractSet, Iterable, Optional, Sequence

from typing_extensions import Self

import dagster._check as check
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
        solid_selection: Optional[Iterable[str]] = None,
        asset_selection: Optional[AbstractSet[AssetKey]] = None,
    ) -> "IJob":
        pass

    @property
    @abstractmethod
    def solid_selection(self) -> Optional[Sequence[str]]:
        pass

    @property
    @abstractmethod
    def asset_selection(self) -> Optional[AbstractSet[AssetKey]]:
        pass

    @property
    def solids_to_execute(self) -> Optional[AbstractSet[str]]:
        return set(self.solid_selection) if self.solid_selection else None


class InMemoryJob(IJob):
    def __init__(
        self,
        job_def: "JobDefinition",
        solid_selection: Optional[Iterable[str]] = None,
        asset_selection: Optional[AbstractSet[AssetKey]] = None,
    ):
        self._job_def = job_def
        self._solid_selection = list(solid_selection) if solid_selection else None
        self._asset_selection = asset_selection

    def get_definition(self) -> "JobDefinition":
        return self._job_def

    def get_subset(
        self,
        solid_selection: Optional[Iterable[str]] = None,
        asset_selection: Optional[AbstractSet[AssetKey]] = None,
    ) -> Self:
        if solid_selection and asset_selection:
            check.failed(
                "solid_selection and asset_selection cannot both be provided as arguments",
            )
        elif solid_selection:
            solid_selection = list(solid_selection)
            return InMemoryJob(self._job_def.get_subset(solid_selection))
        elif asset_selection:
            return InMemoryJob(
                self._job_def.get_subset(asset_selection=asset_selection),
                asset_selection=asset_selection,
            )
        else:
            check.failed("Must provide solid_selection or asset_selection")

    @property
    def solid_selection(self) -> Sequence[str]:
        # a list of solid queries provided by the user
        return self._solid_selection  # type: ignore  # (possible none)

    @property
    def asset_selection(self) -> Optional[AbstractSet[AssetKey]]:
        return self._asset_selection
