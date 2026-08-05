from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import AbstractSet  # noqa: UP035

import dagster._check as check
from dagster._record import record
from dagster_shared.serdes import whitelist_for_serdes


@whitelist_for_serdes
@record
class JobSelection(ABC):
    code_location_name: str
    repository_name: str

    @abstractmethod
    def resolve_job_names(self) -> AbstractSet[str]:
        raise NotImplementedError()

    @staticmethod
    def names(
        names: Sequence[str], code_location_name: str, repository_name: str
    ) -> "NamesJobSelection":
        check.invariant(len(names) == 1, "Only one job name is supported at this time")
        return NamesJobSelection(
            job_names=names, code_location_name=code_location_name, repository_name=repository_name
        )


@whitelist_for_serdes
@record
class NamesJobSelection(JobSelection):
    job_names: Sequence[str]

    def resolve_job_names(self) -> AbstractSet[str]:
        return set(self.job_names)
