from collections import namedtuple

from dagster import check
from dagster.core.code_pointer import CodePointer


class InProcessOrigin(namedtuple('_InProcessOrigin', 'pointer repo_yaml')):
    def __new__(cls, pointer, repo_yaml):
        return super(InProcessOrigin, cls).__new__(
            cls,
            pointer=check.inst_param(pointer, 'pointer', CodePointer),
            repo_yaml=check.opt_str_param(repo_yaml, 'repo_yaml'),
        )

    def load(self):
        target = self.pointer.load_target()
        return target() if callable(target) else target


class LocationHandle(namedtuple('_LocationHandle', 'location_name in_process_origin')):
    def __new__(cls, location_name, in_process_origin):
        return super(LocationHandle, cls).__new__(
            cls,
            check.str_param(location_name, 'location_name'),
            check.inst_param(in_process_origin, 'in_process_origin', InProcessOrigin),
        )

    @staticmethod
    def legacy_from_yaml(location_name, repo_yaml):
        return LocationHandle(
            location_name=location_name,
            in_process_origin=InProcessOrigin(CodePointer.from_yaml(repo_yaml), repo_yaml),
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
