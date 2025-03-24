import sys
from collections.abc import Mapping
from typing import TYPE_CHECKING, Optional

from dagster_shared.serdes import whitelist_for_serdes

import dagster._check as check
from dagster._core.code_pointer import ModuleCodePointer
from dagster._core.definitions.selector import JobSubsetSelector, RepositorySelector
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.origin import RepositoryPythonOrigin
from dagster._core.remote_representation.origin import (
    CodeLocationOrigin,
    RegisteredCodeLocationOrigin,
    RemoteRepositoryOrigin,
)
from dagster._record import record

if TYPE_CHECKING:
    from dagster._core.remote_representation.code_location import CodeLocation


@whitelist_for_serdes
@record
class RepositoryHandle:
    repository_name: str
    code_location_origin: CodeLocationOrigin
    repository_python_origin: RepositoryPythonOrigin
    display_metadata: Mapping[str, str]

    @classmethod
    def from_location(cls, repository_name: str, code_location: "CodeLocation"):
        from dagster._core.remote_representation.code_location import CodeLocation

        check.inst_param(code_location, "code_location", CodeLocation)
        return cls(
            repository_name=repository_name,
            code_location_origin=code_location.origin,
            repository_python_origin=code_location.get_repository_python_origin(repository_name),
            display_metadata=code_location.get_display_metadata(),
        )

    @property
    def location_name(self) -> str:
        return self.code_location_origin.location_name

    def get_remote_origin(self) -> RemoteRepositoryOrigin:
        return RemoteRepositoryOrigin(
            code_location_origin=self.code_location_origin,
            repository_name=self.repository_name,
        )

    def get_python_origin(self) -> RepositoryPythonOrigin:
        return self.repository_python_origin

    def to_selector(self) -> RepositorySelector:
        return RepositorySelector(
            location_name=self.location_name,
            repository_name=self.repository_name,
        )

    def get_compound_id(self) -> "CompoundID":
        return CompoundID(
            remote_origin_id=self.get_remote_origin().get_id(),
            selector_id=self.to_selector().selector_id,
        )

    @staticmethod
    def for_test(
        *,
        location_name: str = "fake_location",
        repository_name: str = "fake_repository",
        display_metadata: Optional[Mapping[str, str]] = None,
    ) -> "RepositoryHandle":
        return RepositoryHandle(
            repository_name=repository_name,
            code_location_origin=RegisteredCodeLocationOrigin(location_name=location_name),
            repository_python_origin=RepositoryPythonOrigin(
                executable_path=sys.executable,
                code_pointer=ModuleCodePointer(
                    module="fake.module",
                    fn_name="fake_fn",
                ),
            ),
            display_metadata=display_metadata or {},
        )


@record(kw_only=False)
class JobHandle:
    job_name: str
    repository_handle: RepositoryHandle

    def to_string(self):
        return f"{self.location_name}.{self.repository_name}.{self.job_name}"

    @property
    def repository_name(self):
        return self.repository_handle.repository_name

    @property
    def location_name(self):
        return self.repository_handle.location_name

    def get_remote_origin(self):
        return self.repository_handle.get_remote_origin().get_job_origin(self.job_name)

    def get_python_origin(self):
        return self.repository_handle.get_python_origin().get_job_origin(self.job_name)

    def to_selector(self) -> JobSubsetSelector:
        return JobSubsetSelector(
            location_name=self.location_name,
            repository_name=self.repository_name,
            job_name=self.job_name,
            op_selection=None,
        )


@record(kw_only=False)
class InstigatorHandle:
    instigator_name: str
    repository_handle: RepositoryHandle

    @property
    def repository_name(self) -> str:
        return self.repository_handle.repository_name

    @property
    def location_name(self) -> str:
        return self.repository_handle.location_name

    def get_remote_origin(self):
        return self.repository_handle.get_remote_origin().get_instigator_origin(
            self.instigator_name
        )


@record
class PartitionSetHandle:
    partition_set_name: str
    repository_handle: RepositoryHandle

    @property
    def repository_name(self):
        return self.repository_handle.repository_name

    @property
    def location_name(self):
        return self.repository_handle.location_name

    def get_remote_origin(self):
        return self.repository_handle.get_remote_origin().get_partition_set_origin(
            self.partition_set_name
        )


_DELIMITER = "::"


@record
class CompoundID:
    """Compound ID object for the two id schemes that state is recorded in the database against."""

    remote_origin_id: str
    selector_id: str

    def to_string(self) -> str:
        return f"{self.remote_origin_id}{_DELIMITER}{self.selector_id}"

    @staticmethod
    def from_string(serialized: str):
        parts = serialized.split(_DELIMITER)
        if len(parts) != 2:
            raise DagsterInvariantViolationError(f"Invalid serialized InstigatorID: {serialized}")

        return CompoundID(
            remote_origin_id=parts[0],
            selector_id=parts[1],
        )

    @staticmethod
    def is_valid_string(serialized: str):
        parts = serialized.split(_DELIMITER)
        return len(parts) == 2
