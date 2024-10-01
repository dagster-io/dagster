from typing import TYPE_CHECKING, Mapping

import dagster._check as check
from dagster._core.definitions.selector import JobSubsetSelector
from dagster._core.origin import RepositoryPythonOrigin
from dagster._core.remote_representation.origin import CodeLocationOrigin, RemoteRepositoryOrigin
from dagster._record import IHaveNew, record, record_custom

if TYPE_CHECKING:
    from dagster._core.remote_representation.code_location import CodeLocation


@record_custom
class RepositoryHandle(IHaveNew):
    repository_name: str
    code_location_origin: CodeLocationOrigin
    repository_python_origin: RepositoryPythonOrigin
    display_metadata: Mapping[str, str]

    def __new__(cls, repository_name: str, code_location: "CodeLocation"):
        from dagster._core.remote_representation.code_location import CodeLocation

        check.inst_param(code_location, "code_location", CodeLocation)
        return super().__new__(
            cls,
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


@record_custom
class JobHandle(IHaveNew):
    job_name: str
    repository_handle: RepositoryHandle

    # allow posargs
    def __new__(cls, job_name: str, repository_handle: RepositoryHandle):
        return super().__new__(
            cls,
            job_name=job_name,
            repository_handle=repository_handle,
        )

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


@record_custom
class InstigatorHandle(IHaveNew):
    instigator_name: str
    repository_handle: RepositoryHandle

    # allow posargs
    def __new__(cls, instigator_name: str, repository_handle: RepositoryHandle):
        return super().__new__(
            cls,
            instigator_name=instigator_name,
            repository_handle=repository_handle,
        )

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
