from collections import namedtuple

from dagster import check
from dagster.core.code_pointer import CodePointer
from dagster.serdes import create_snapshot_id, whitelist_for_serdes


@whitelist_for_serdes
class RepositoryPythonOrigin(
    namedtuple('_RepositoryPythonOrigin', 'executable_path code_pointer'),
):
    '''
    Derived from the handle structure in the host process, this is the subset of information
    necessary to load a target RepositoryDefinition in a "user process" locally.
    '''

    def __new__(cls, executable_path, code_pointer):
        return super(RepositoryPythonOrigin, cls).__new__(
            cls,
            check.str_param(executable_path, 'executable_path'),
            check.inst_param(code_pointer, 'code_pointer', CodePointer),
        )

    def get_cli_args(self):
        return self.code_pointer.get_cli_args()

    def get_id(self):
        return create_snapshot_id(self)


@whitelist_for_serdes
class PipelinePythonOrigin(namedtuple('_PipelinePythonOrigin', 'pipeline_name repository_origin')):
    def __new__(cls, pipeline_name, repository_origin):
        return super(PipelinePythonOrigin, cls).__new__(
            cls,
            check.str_param(pipeline_name, 'pipeline_name'),
            check.inst_param(repository_origin, 'repository_origin', RepositoryPythonOrigin),
        )

    @property
    def executable_path(self):
        return self.repository_origin.executable_path

    def get_repo_cli_args(self):
        return self.repository_origin.get_cli_args()

    def get_repo_pointer(self):
        return self.repository_origin.code_pointer

    def get_id(self):
        return create_snapshot_id(self)


@whitelist_for_serdes
class SchedulePythonOrigin(namedtuple('_SchedulePythonOrigin', 'schedule_name repository_origin')):
    def __new__(cls, schedule_name, repository_origin):
        return super(SchedulePythonOrigin, cls).__new__(
            cls,
            check.str_param(schedule_name, 'schedule_name'),
            check.inst_param(repository_origin, 'repository_origin', RepositoryPythonOrigin),
        )

    @property
    def executable_path(self):
        return self.repository_origin.executable_path

    def get_repo_cli_args(self):
        return self.repository_origin.get_cli_args()

    def get_repo_pointer(self):
        return self.repository_origin.code_pointer

    def get_id(self):
        return create_snapshot_id(self)
