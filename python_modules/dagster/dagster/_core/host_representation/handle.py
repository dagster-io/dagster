from typing import TYPE_CHECKING, Mapping, NamedTuple

import dagster._check as check
from dagster._core.definitions.selector import JobSubsetSelector
from dagster._core.host_representation.origin import (
    CodeLocationOrigin,
    ExternalRepositoryOrigin,
)
from dagster._core.origin import RepositoryPythonOrigin

if TYPE_CHECKING:
    from dagster._core.host_representation.code_location import CodeLocation


class RepositoryHandle(
    NamedTuple(
        "_RepositoryHandle",
        [
            ("repository_name", str),
            ("code_location_origin", CodeLocationOrigin),
            ("repository_python_origin", RepositoryPythonOrigin),
            ("display_metadata", Mapping[str, str]),
        ],
    )
):
    def __new__(cls, repository_name: str, code_location: "CodeLocation"):
        from dagster._core.host_representation.code_location import CodeLocation

        check.inst_param(code_location, "code_location", CodeLocation)
        return super(RepositoryHandle, cls).__new__(
            cls,
            check.str_param(repository_name, "repository_name"),
            code_location.origin,
            code_location.get_repository_python_origin(repository_name),
            code_location.get_display_metadata(),
        )

    @property
    def location_name(self) -> str:
        return self.code_location_origin.location_name

    def get_external_origin(self):
        return ExternalRepositoryOrigin(
            self.code_location_origin,
            self.repository_name,
        )

    def get_python_origin(self):
        return self.repository_python_origin


class JobHandle(
    NamedTuple("_PipelineHandle", [("job_name", str), ("repository_handle", RepositoryHandle)])
):
    def __new__(cls, job_name: str, repository_handle: RepositoryHandle):
        return super(JobHandle, cls).__new__(
            cls,
            check.str_param(job_name, "job_name"),
            check.inst_param(repository_handle, "repository_handle", RepositoryHandle),
        )

    def to_string(self):
        return f"{self.location_name}.{self.repository_name}.{self.job_name}"

    @property
    def repository_name(self):
        return self.repository_handle.repository_name

    @property
    def location_name(self):
        return self.repository_handle.location_name

    def get_external_origin(self):
        return self.repository_handle.get_external_origin().get_job_origin(self.job_name)

    def get_python_origin(self):
        return self.repository_handle.get_python_origin().get_job_origin(self.job_name)

    def to_selector(self):
        return JobSubsetSelector(self.location_name, self.repository_name, self.job_name, None)


class InstigatorHandle(
    NamedTuple(
        "_InstigatorHandle", [("instigator_name", str), ("repository_handle", RepositoryHandle)]
    )
):
    def __new__(cls, job_name: str, repository_handle: RepositoryHandle):
        return super(InstigatorHandle, cls).__new__(
            cls,
            check.str_param(job_name, "job_name"),
            check.inst_param(repository_handle, "repository_handle", RepositoryHandle),
        )

    @property
    def repository_name(self):
        return self.repository_handle.repository_name

    @property
    def location_name(self):
        return self.repository_handle.location_name

    def get_external_origin(self):
        return self.repository_handle.get_external_origin().get_instigator_origin(
            self.instigator_name
        )


class PartitionSetHandle(
    NamedTuple(
        "_PartitionSetHandle",
        [("partition_set_name", str), ("repository_handle", RepositoryHandle)],
    )
):
    def __new__(cls, partition_set_name: str, repository_handle: RepositoryHandle):
        return super(PartitionSetHandle, cls).__new__(
            cls,
            check.str_param(partition_set_name, "partition_set_name"),
            check.inst_param(repository_handle, "repository_handle", RepositoryHandle),
        )

    @property
    def repository_name(self):
        return self.repository_handle.repository_name

    @property
    def location_name(self):
        return self.repository_handle.location_name

    def get_external_origin(self):
        return self.repository_handle.get_external_origin().get_partition_set_origin(
            self.partition_set_name
        )
