from collections import namedtuple

from dagster import check
from dagster.core.code_pointer import CodePointer


class LocationHandle(namedtuple('_LocationHandle', 'location_name pointer')):
    def __new__(cls, location_name, pointer):
        return super(LocationHandle, cls).__new__(
            cls,
            check.str_param(location_name, 'location_name'),
            check.inst_param(pointer, 'pointer', CodePointer),
        )


class RepositoryHandle(namedtuple('_RepositoryHandle', 'repository_name location_handle')):
    def __new__(cls, repository_name, location_handle):
        return super(RepositoryHandle, cls).__new__(
            cls,
            check.str_param(repository_name, 'repository_name'),
            check.inst_param(location_handle, 'location_handle', LocationHandle),
        )


class PipelineHandle(namedtuple('_PipelineHandle', 'pipeline_name repository_handle')):
    def __new__(cls, pipeline_name, repository_handle):
        return super(PipelineHandle, cls).__new__(
            cls,
            check.str_param(pipeline_name, 'pipeline_name'),
            check.inst_param(repository_handle, 'repository_handle', RepositoryHandle),
        )

    def to_string(self):
        return '{self.location_name}.{self.repository_name}.{self.pipeline_name}'.format(self=self)

    @property
    def repository_name(self):
        return self.repository_handle.repository_name

    @property
    def location_name(self):
        return self.repository_handle.location_handle.location_name
