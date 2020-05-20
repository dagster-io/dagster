from collections import namedtuple

from dagster import check


class EnvironmentHandle(namedtuple('_EnvironmentHandle', 'environment_name')):
    def __new__(cls, environment_name):
        return super(EnvironmentHandle, cls).__new__(
            cls,
            check.str_param(environment_name, 'environment_name'),
            # source to be added
        )


class RepositoryHandle(namedtuple('_RepositoryHandle', 'repository_name environment_handle')):
    def __new__(cls, repository_name, environment_handle):
        return super(RepositoryHandle, cls).__new__(
            cls,
            check.str_param(repository_name, 'repository_name'),
            check.inst_param(environment_handle, 'environment_handle', EnvironmentHandle),
        )


class PipelineHandle(namedtuple('_PipelineHandle', 'pipeline_name repository_handle')):
    def __new__(cls, pipeline_name, repository_handle):
        return super(PipelineHandle, cls).__new__(
            cls,
            check.str_param(pipeline_name, 'pipeline_name'),
            check.inst_param(repository_handle, 'repository_handle', RepositoryHandle),
        )

    def to_string(self):
        return '{self.environment_name}.{self.repository_name}.{self.pipeline_name}'.format(
            self=self
        )

    @property
    def repository_name(self):
        return self.repository_handle.repository_name

    @property
    def environment_name(self):
        return self.repository_handle.environment_handle.environment_name
