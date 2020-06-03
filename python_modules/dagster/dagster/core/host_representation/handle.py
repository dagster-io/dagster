from collections import namedtuple

from dagster import check
from dagster.core.code_pointer import CodePointer

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
        return InProcessRepositoryLocationHandle(IN_PROCESS_NAME, pointer)

    @staticmethod
    def create_out_of_process_location(location_name, pointer):
        return OutOfProcessRepositoryLocationHandle(location_name, pointer)


class InProcessRepositoryLocationHandle(
    namedtuple('_InProcessRepositoryLocationHandle', 'location_name pointer'),
    RepositoryLocationHandle,
):
    def __new__(cls, location_name, pointer):
        return super(InProcessRepositoryLocationHandle, cls).__new__(
            cls,
            check.str_param(location_name, 'location_name'),
            check.inst_param(pointer, 'pointer', CodePointer),
        )


class OutOfProcessRepositoryLocationHandle(
    namedtuple('_OutOfProcessRepositoryLocationHandle', 'location_name pointer'),
    RepositoryLocationHandle,
):
    def __new__(cls, location_name, pointer):
        return super(OutOfProcessRepositoryLocationHandle, cls).__new__(
            cls,
            check.str_param(location_name, 'location_name'),
            check.inst_param(pointer, 'pointer', CodePointer),
        )


class RepositoryHandle(
    namedtuple('_RepositoryHandle', 'repository_name repository_location_handle')
):
    def __new__(cls, repository_name, repository_location_handle):
        return super(RepositoryHandle, cls).__new__(
            cls,
            check.str_param(repository_name, 'repository_name'),
            check.inst_param(
                repository_location_handle, 'repository_location_handle', RepositoryLocationHandle
            ),
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
        return self.repository_handle.location_handle.location_name


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
        return self.repository_handle.location_handle.location_name
