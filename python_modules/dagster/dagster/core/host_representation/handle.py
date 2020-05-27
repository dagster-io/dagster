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


class EnvironmentHandle(namedtuple('_EnvironmentHandle', 'environment_name in_process_origin')):
    def __new__(cls, environment_name, in_process_origin):
        return super(EnvironmentHandle, cls).__new__(
            cls,
            check.str_param(environment_name, 'environment_name'),
            check.inst_param(in_process_origin, 'in_process_origin', InProcessOrigin),
        )

    @staticmethod
    def legacy_from_yaml(environment_name, repo_yaml):
        return EnvironmentHandle(
            environment_name=environment_name,
            in_process_origin=InProcessOrigin(CodePointer.from_yaml(repo_yaml), repo_yaml),
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
