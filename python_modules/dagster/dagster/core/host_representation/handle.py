import weakref
from collections import namedtuple

from dagster import check
from dagster.core.host_representation.origin import ExternalRepositoryOrigin
from dagster.core.host_representation.selector import PipelineSelector


class RepositoryHandle(namedtuple("_RepositoryHandle", "repository_name repository_location_ref")):
    def __new__(cls, repository_name, repository_location):
        from dagster.core.host_representation.repository_location import RepositoryLocation

        repository_location_ref = weakref.ref(
            check.inst_param(repository_location, "repository_location", RepositoryLocation)
        )
        return super(RepositoryHandle, cls).__new__(
            cls,
            check.str_param(repository_name, "repository_name"),
            repository_location_ref,
        )

    def get_external_origin(self):
        return ExternalRepositoryOrigin(
            self.repository_location.origin,
            self.repository_name,
        )

    @property
    def repository_location(self):
        return self.repository_location_ref()

    def get_python_origin(self):
        return self.repository_location.get_repository_python_origin(self.repository_name)


class PipelineHandle(namedtuple("_PipelineHandle", "pipeline_name repository_handle")):
    def __new__(cls, pipeline_name, repository_handle):
        return super(PipelineHandle, cls).__new__(
            cls,
            check.str_param(pipeline_name, "pipeline_name"),
            check.inst_param(repository_handle, "repository_handle", RepositoryHandle),
        )

    def to_string(self):
        return "{self.location_name}.{self.repository_name}.{self.pipeline_name}".format(self=self)

    @property
    def repository_name(self):
        return self.repository_handle.repository_name

    @property
    def location_name(self):
        return self.repository_handle.repository_location.name

    def get_external_origin(self):
        return self.repository_handle.get_external_origin().get_pipeline_origin(self.pipeline_name)

    def get_python_origin(self):
        return self.repository_handle.get_python_origin().get_pipeline_origin(self.pipeline_name)

    def to_selector(self):
        return PipelineSelector(self.location_name, self.repository_name, self.pipeline_name, None)


class JobHandle(namedtuple("_JobHandle", "job_name repository_handle")):
    def __new__(cls, job_name, repository_handle):
        return super(JobHandle, cls).__new__(
            cls,
            check.str_param(job_name, "job_name"),
            check.inst_param(repository_handle, "repository_handle", RepositoryHandle),
        )

    @property
    def repository_name(self):
        return self.repository_handle.repository_name

    @property
    def location_name(self):
        return self.repository_handle.repository_location.name

    def get_external_origin(self):
        return self.repository_handle.get_external_origin().get_job_origin(self.job_name)


class PartitionSetHandle(namedtuple("_PartitionSetHandle", "partition_set_name repository_handle")):
    def __new__(cls, partition_set_name, repository_handle):
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
        return self.repository_handle.repository_location.name

    def get_external_origin(self):
        return self.repository_handle.get_external_origin().get_partition_set_origin(
            self.partition_set_name
        )
