import sys
from collections import namedtuple
from enum import Enum

from dagster import check
from dagster.api.list_repositories import sync_list_repositories_grpc
from dagster.core.code_pointer import CodePointer
from dagster.core.host_representation.selector import PipelineSelector
from dagster.core.origin import RepositoryGrpcServerOrigin, RepositoryPythonOrigin

# This is a hard-coded name for the special "in-process" location.
# This is typically only used for test, although we may allow
# users to load user code into a host process as well. We want
# to encourage the user code to be in user processes as much
# as possible since that it how this system will be used in prod.
# We used a hard-coded name so that we don't have to create
# made up names for this case.
IN_PROCESS_NAME = '<<in_process>>'


def assign_grpc_location_name(port, socket, host):
    check.opt_int_param(port, 'port')
    check.opt_str_param(socket, 'socket')
    check.str_param(host, 'host')
    check.invariant(port or socket)
    return 'grpc:{host}:{socket_or_port}'.format(
        host=host, socket_or_port=(socket if socket else port)
    )


# Which API the host process should use to communicate with the process
# containing user code
class UserProcessApi(Enum):
    # Execute via the command-line API
    CLI = 'CLI'
    # Connect via gRPC
    GRPC = 'GRPC'


class RepositoryLocationHandle:
    @staticmethod
    def create_in_process_location(pointer):
        check.inst_param(pointer, 'pointer', CodePointer)

        # If we are here we know we are in a hosted_user_process so we can do this
        from dagster.core.definitions.reconstructable import repository_def_from_pointer

        repo_def = repository_def_from_pointer(pointer)
        return InProcessRepositoryLocationHandle(IN_PROCESS_NAME, {repo_def.name: pointer})

    @staticmethod
    def create_out_of_process_location(
        location_name, repository_code_pointer_dict,
    ):
        return RepositoryLocationHandle.create_python_env_location(
            executable_path=sys.executable,
            location_name=location_name,
            repository_code_pointer_dict=repository_code_pointer_dict,
        )

    @staticmethod
    def create_python_env_location(
        executable_path, location_name, repository_code_pointer_dict,
    ):
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

    @staticmethod
    def create_process_bound_grpc_server_location(loadable_target_origin, location_name):
        from dagster.grpc.server import GrpcServerProcess

        server = GrpcServerProcess(loadable_target_origin=loadable_target_origin)
        client = server.create_client()
        list_repositories_response = sync_list_repositories_grpc(client)

        repository_keys = set(
            symbol.repository_name for symbol in list_repositories_response.repository_symbols
        )

        return GrpcServerRepositoryLocationHandle(
            port=server.port,
            socket=server.socket,
            host='localhost',
            location_name=location_name
            if location_name
            else assign_grpc_location_name(server.port, server.socket, 'localhost'),
            client=client,
            server_process=server,
            repository_keys=repository_keys,
        )

    @staticmethod
    def create_grpc_server_location(location_name, port, socket, host):
        from dagster.grpc.client import DagsterGrpcClient

        check.opt_str_param(location_name, 'location_name')
        check.opt_int_param(port, 'port')
        check.opt_str_param(socket, 'socket')
        check.str_param(host, 'host')

        client = DagsterGrpcClient(port=port, socket=socket, host=host)

        list_repositories_response = sync_list_repositories_grpc(client)

        repository_keys = set(
            symbol.repository_name for symbol in list_repositories_response.repository_symbols
        )

        return GrpcServerRepositoryLocationHandle(
            port=port,
            socket=socket,
            host=host,
            location_name=location_name
            if location_name
            else assign_grpc_location_name(port, socket, host),
            client=client,
            server_process=None,
            repository_keys=repository_keys,
        )


class GrpcServerRepositoryLocationHandle(
    namedtuple(
        '_GrpcServerRepositoryLocationHandle',
        'port socket host location_name client server_process repository_keys',
    ),
    RepositoryLocationHandle,
):
    def __new__(cls, port, socket, host, location_name, client, server_process, repository_keys):
        from dagster.grpc.client import DagsterGrpcClient
        from dagster.grpc.server import GrpcServerProcess

        return super(GrpcServerRepositoryLocationHandle, cls).__new__(
            cls,
            check.opt_int_param(port, 'port'),
            check.opt_str_param(socket, 'socket'),
            check.str_param(host, 'host'),
            check.str_param(location_name, 'location_name'),
            check.inst_param(client, 'client', DagsterGrpcClient),
            check.opt_inst_param(server_process, 'server_process', GrpcServerProcess),
            check.set_param(repository_keys, 'repository_keys', of_type=str),
        )


class PythonEnvRepositoryLocationHandle(
    namedtuple(
        '_PythonEnvRepositoryLocationHandle',
        'executable_path location_name repository_code_pointer_dict',
    ),
    RepositoryLocationHandle,
):
    def __new__(cls, executable_path, location_name, repository_code_pointer_dict):
        return super(PythonEnvRepositoryLocationHandle, cls).__new__(
            cls,
            check.str_param(executable_path, 'executable_path'),
            check.str_param(location_name, 'location_name'),
            check.dict_param(
                repository_code_pointer_dict,
                'repository_code_pointer_dict',
                key_type=str,
                value_type=CodePointer,
            ),
        )


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
        elif isinstance(self.repository_location_handle, GrpcServerRepositoryLocationHandle):
            return RepositoryGrpcServerOrigin(
                host=self.repository_location_handle.host,
                port=self.repository_location_handle.port,
                socket=self.repository_location_handle.socket,
                repository_key=self.repository_key,
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
        return self.repository_handle.get_origin().get_pipeline_origin(self.pipeline_name)

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
        return self.repository_handle.get_origin().get_schedule_origin(self.schedule_name)


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
