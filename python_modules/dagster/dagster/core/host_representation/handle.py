import sys
from collections import namedtuple

from dagster import check
from dagster.core.code_pointer import CodePointer
from dagster.core.host_representation.selector import PipelineSelector
from dagster.core.origin import PipelinePythonOrigin, RepositoryPythonOrigin, SchedulePythonOrigin

# This is a hard-coded name for the special "in-process" location.
# This is typically only used for test, although we may allow
# users to load user code into a host process as well. We want
# to encourage the user code to be in user processes as much
# as possible since that it how this system will be used in prod.
# We used a hard-coded name so that we don't have to create
# made up names for this case.
IN_PROCESS_NAME = '<<in_process>>'


class RepositoryLocationHandle:
    @staticmethod
    def create_in_process_location(pointer):
        check.inst_param(pointer, 'pointer', CodePointer)

        # If we are here we know we are in a hosted_user_process so we can do this
        from dagster.core.definitions.reconstructable import repository_def_from_pointer

        repo_def = repository_def_from_pointer(pointer)
        return InProcessRepositoryLocationHandle(IN_PROCESS_NAME, {repo_def.name: pointer})

    @staticmethod
    def create_out_of_process_location(location_name, repository_code_pointer_dict):
        check.str_param(location_name, 'location_name')
        check.dict_param(
            repository_code_pointer_dict,
            'repository_code_pointer_dict',
            key_type=str,
            value_type=CodePointer,
        )
        return PythonEnvRepositoryLocationHandle(
            location_name=location_name,
            executable_path=sys.executable,
            repository_code_pointer_dict=repository_code_pointer_dict,
        )

    @staticmethod
    def create_python_env_location(executable_path, location_name, repository_code_pointer_dict):
        check.str_param(executable_path, 'executable_path')
        check.str_param(location_name, 'location_name')
        check.dict_param(
            repository_code_pointer_dict,
            'repository_code_pointer_dict',
            key_type=str,
            value_type=CodePointer,
        )
        return PythonEnvRepositoryLocationHandle(
            location_name=location_name,
            executable_path=executable_path,
            repository_code_pointer_dict=repository_code_pointer_dict,
        )


class PythonEnvRepositoryLocationHandle(
    namedtuple(
        '_PythonEnvRepositoryLocationHandle',
        'executable_path location_name repository_code_pointer_dict',
    ),
    RepositoryLocationHandle,
):
    pass


class InProcessRepositoryLocationHandle(
    namedtuple('_InProcessRepositoryLocationHandle', 'location_name repository_code_pointer_dict'),
    RepositoryLocationHandle,
):
    def __new__(cls, location_name, repository_code_pointer_dict):
        return super(InProcessRepositoryLocationHandle, cls).__new__(
            cls,
            check.str_param(location_name, 'location_name'),
            check.dict_param(
                repository_code_pointer_dict,
                'repository_code_pointer_dict',
                key_type=str,
                value_type=CodePointer,
            ),
        )


class RepositoryHandle(
    # repository_name is the name of the repository itself.
    # repository_key is how the repository location indexes into the collection
    # of pointers.
    namedtuple('_RepositoryHandle', 'repository_name repository_key repository_location_handle')
):
    def __new__(cls, repository_name, repository_key, repository_location_handle):
        return super(RepositoryHandle, cls).__new__(
            cls,
            check.str_param(repository_name, 'repository_name'),
            check.str_param(repository_key, 'repository_key'),
            check.inst_param(
                repository_location_handle, 'repository_location_handle', RepositoryLocationHandle
            ),
        )

    def get_origin(self):
        if isinstance(self.repository_location_handle, InProcessRepositoryLocationHandle):
            return RepositoryPythonOrigin(
                code_pointer=self.repository_location_handle.repository_code_pointer_dict[
                    self.repository_key
                ],
                executable_path=sys.executable,
            )
        elif isinstance(self.repository_location_handle, PythonEnvRepositoryLocationHandle):
            return RepositoryPythonOrigin(
                code_pointer=self.repository_location_handle.repository_code_pointer_dict[
                    self.repository_key
                ],
                executable_path=self.repository_location_handle.executable_path,
            )
        else:
            check.failed(
                'Can not target represented RepositoryDefinition locally for repository from a {}.'.format(
                    self.repository_location_handle.__class__.__name__
                )
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
        return self.repository_handle.repository_location_handle.location_name

    def get_origin(self):
        return PipelinePythonOrigin(self.pipeline_name, self.repository_handle.get_origin())

    def to_selector(self):
        return PipelineSelector(self.location_name, self.repository_name, self.pipeline_name, None)


class ScheduleHandle(namedtuple('_ScheduleHandle', 'schedule_name repository_handle')):
    def __new__(cls, schedule_name, repository_handle):
        return super(ScheduleHandle, cls).__new__(
            cls,
            check.str_param(schedule_name, 'schedule_name'),
            check.inst_param(repository_handle, 'repository_handle', RepositoryHandle),
        )

    @property
    def repository_name(self):
        return self.repository_handle.repository_name

    @property
    def location_name(self):
        return self.repository_handle.repository_location_handle.location_name

    def get_origin(self):
        return SchedulePythonOrigin(self.schedule_name, self.repository_handle.get_origin())


class PartitionSetHandle(namedtuple('_PartitionSetHandle', 'partition_set_name repository_handle')):
    def __new__(cls, partition_set_name, repository_handle):
        return super(PartitionSetHandle, cls).__new__(
            cls,
            check.str_param(partition_set_name, 'partition_set_name'),
            check.inst_param(repository_handle, 'repository_handle', RepositoryHandle),
        )

    @property
    def repository_name(self):
        return self.repository_handle.repository_name

    @property
    def location_name(self):
        return self.repository_handle.repository_location_handle.location_name
