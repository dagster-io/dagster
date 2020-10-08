import sys
import threading
from abc import ABCMeta, abstractmethod
from collections import namedtuple
from enum import Enum

import six

from dagster import check
from dagster.api.list_repositories import sync_list_repositories, sync_list_repositories_grpc
from dagster.core.code_pointer import CodePointer
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.host_representation.selector import PipelineSelector
from dagster.core.instance import DagsterInstance
from dagster.core.origin import RepositoryGrpcServerOrigin, RepositoryOrigin, RepositoryPythonOrigin
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin

# This is a hard-coded name for the special "in-process" location.
# This is typically only used for test, although we may allow
# users to load user code into a host process as well. We want
# to encourage the user code to be in user processes as much
# as possible since that it how this system will be used in prod.
# We used a hard-coded name so that we don't have to create
# made up names for this case.
IN_PROCESS_NAME = "<<in_process>>"


def _assign_grpc_location_name(port, socket, host):
    check.opt_int_param(port, "port")
    check.opt_str_param(socket, "socket")
    check.str_param(host, "host")
    check.invariant(port or socket)
    return "grpc:{host}:{socket_or_port}".format(
        host=host, socket_or_port=(socket if socket else port)
    )


def _assign_python_env_location_name(repository_code_pointer_dict):
    check.dict_param(
        repository_code_pointer_dict,
        "repository_code_pointer_dict",
        key_type=str,
        value_type=CodePointer,
    )
    if len(repository_code_pointer_dict) > 1:
        raise DagsterInvariantViolationError(
            "If there is one than more repository you must provide a location name"
        )

    return next(iter(repository_code_pointer_dict.keys()))


# Which API the host process should use to communicate with the process
# containing user code
class UserProcessApi(Enum):
    # Execute via the command-line API
    CLI = "CLI"
    # Connect via gRPC
    GRPC = "GRPC"


def python_user_process_api_from_instance(instance):
    check.inst_param(instance, "instance", DagsterInstance)

    opt_in_settings = instance.get_settings("opt_in")
    return (
        UserProcessApi.GRPC
        if (opt_in_settings and opt_in_settings["local_servers"])
        else UserProcessApi.CLI
    )


class RepositoryLocationHandle(six.with_metaclass(ABCMeta)):
    @abstractmethod
    def create_reloaded_handle(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.cleanup()

    def cleanup(self):
        pass

    @staticmethod
    def create_from_repository_origin(repository_origin, instance):
        check.inst_param(repository_origin, "repository_origin", RepositoryOrigin)
        check.inst_param(instance, "instance", DagsterInstance)

        if isinstance(repository_origin, RepositoryGrpcServerOrigin):
            return RepositoryLocationHandle.create_grpc_server_location(
                port=repository_origin.port,
                socket=repository_origin.socket,
                host=repository_origin.host,
            )
        elif isinstance(repository_origin, RepositoryPythonOrigin):
            return RepositoryLocationHandle.create_python_env_location(
                loadable_target_origin=repository_origin.loadable_target_origin,
                user_process_api=python_user_process_api_from_instance(instance),
            )
        else:
            raise DagsterInvariantViolationError("Unexpected repository origin type")

    @staticmethod
    def create_in_process_location(pointer):
        check.inst_param(pointer, "pointer", CodePointer)

        # If we are here we know we are in a hosted_user_process so we can do this
        from dagster.core.definitions.reconstructable import repository_def_from_pointer

        repo_def = repository_def_from_pointer(pointer)
        return InProcessRepositoryLocationHandle(IN_PROCESS_NAME, {repo_def.name: pointer})

    @staticmethod
    def create_python_env_location(
        loadable_target_origin,
        location_name=None,
        user_process_api=UserProcessApi.CLI,
        use_python_package=False,
    ):
        check.inst_param(loadable_target_origin, "loadable_target_origin", LoadableTargetOrigin)
        check.opt_str_param(location_name, "location_name")
        check.bool_param(use_python_package, "use_python_package")

        if user_process_api == UserProcessApi.GRPC:
            return RepositoryLocationHandle.create_process_bound_grpc_server_location(
                loadable_target_origin=loadable_target_origin, location_name=location_name
            )

        response = sync_list_repositories(
            executable_path=loadable_target_origin.executable_path,
            python_file=loadable_target_origin.python_file,
            module_name=loadable_target_origin.module_name,
            working_directory=loadable_target_origin.working_directory,
            attribute=loadable_target_origin.attribute,
        )

        if loadable_target_origin.python_file:
            repository_code_pointer_dict = {
                lrs.repository_name: CodePointer.from_python_file(
                    loadable_target_origin.python_file,
                    lrs.attribute,
                    loadable_target_origin.working_directory,
                )
                for lrs in response.repository_symbols
            }
        elif use_python_package:
            repository_code_pointer_dict = {
                lrs.repository_name: CodePointer.from_python_package(
                    loadable_target_origin.module_name, lrs.attribute
                )
                for lrs in response.repository_symbols
            }
        else:
            repository_code_pointer_dict = {
                lrs.repository_name: CodePointer.from_module(
                    loadable_target_origin.module_name, lrs.attribute
                )
                for lrs in response.repository_symbols
            }
        return PythonEnvRepositoryLocationHandle(
            location_name=location_name
            if location_name
            else _assign_python_env_location_name(repository_code_pointer_dict),
            loadable_target_origin=loadable_target_origin,
            repository_code_pointer_dict=repository_code_pointer_dict,
        )

    @staticmethod
    def create_process_bound_grpc_server_location(loadable_target_origin, location_name):
        from dagster.grpc.client import client_heartbeat_thread
        from dagster.grpc.server import GrpcServerProcess

        server = GrpcServerProcess(
            loadable_target_origin=loadable_target_origin,
            max_workers=2,
            heartbeat=True,
            lazy_load_user_code=True,
        )
        client = server.create_ephemeral_client()

        heartbeat_shutdown_event = threading.Event()

        heartbeat_thread = threading.Thread(
            target=client_heartbeat_thread, args=(client, heartbeat_shutdown_event)
        )
        heartbeat_thread.daemon = True
        heartbeat_thread.start()
        list_repositories_response = sync_list_repositories_grpc(client)

        code_pointer_dict = list_repositories_response.repository_code_pointer_dict

        return ManagedGrpcPythonEnvRepositoryLocationHandle(
            loadable_target_origin=loadable_target_origin,
            executable_path=list_repositories_response.executable_path,
            location_name=location_name
            if location_name
            else _assign_python_env_location_name(code_pointer_dict),
            repository_code_pointer_dict=code_pointer_dict,
            client=client,
            grpc_server_process=server,
            heartbeat_thread=heartbeat_thread,
            heartbeat_shutdown_event=heartbeat_shutdown_event,
        )

    @staticmethod
    def create_grpc_server_location(port, socket, host, location_name=None):
        from dagster.grpc.client import DagsterGrpcClient

        check.opt_int_param(port, "port")
        check.opt_str_param(socket, "socket")
        check.str_param(host, "host")
        check.opt_str_param(location_name, "location_name")

        client = DagsterGrpcClient(port=port, socket=socket, host=host)

        list_repositories_response = sync_list_repositories_grpc(client)

        repository_names = set(
            symbol.repository_name for symbol in list_repositories_response.repository_symbols
        )

        return GrpcServerRepositoryLocationHandle(
            port=port,
            socket=socket,
            host=host,
            location_name=location_name
            if location_name
            else _assign_grpc_location_name(port, socket, host),
            client=client,
            repository_names=repository_names,
        )


class GrpcServerRepositoryLocationHandle(
    namedtuple(
        "_GrpcServerRepositoryLocationHandle",
        "port socket host location_name client repository_names",
    ),
    RepositoryLocationHandle,
):
    """
    Represents a gRPC server that Dagster is not responsible for managing.
    """

    def __new__(cls, port, socket, host, location_name, client, repository_names):
        from dagster.grpc.client import DagsterGrpcClient

        return super(GrpcServerRepositoryLocationHandle, cls).__new__(
            cls,
            check.opt_int_param(port, "port"),
            check.opt_str_param(socket, "socket"),
            check.str_param(host, "host"),
            check.str_param(location_name, "location_name"),
            check.inst_param(client, "client", DagsterGrpcClient),
            check.set_param(repository_names, "repository_names", of_type=str),
        )

    def create_reloaded_handle(self):
        return RepositoryLocationHandle.create_grpc_server_location(
            self.port, self.socket, self.host, self.location_name
        )

    def get_current_image(self):
        job_image = self.client.get_current_image().current_image
        if not job_image:
            raise DagsterInvariantViolationError(
                "Unable to get current image that GRPC server is running. Please make sure that "
                "env var DAGSTER_CURRENT_IMAGE is set in the GRPC server and contains the most "
                "up-to-date user code image and tag. Exiting."
            )
        return job_image

    def get_repository_python_origin(self, repository_name):
        check.str_param(repository_name, "repository_name")

        list_repositories_reply = self.client.list_repositories()
        repository_code_pointer_dict = list_repositories_reply.repository_code_pointer_dict

        if repository_name not in repository_code_pointer_dict:
            raise DagsterInvariantViolationError(
                "Unable to find repository name {} on GRPC server.".format(repository_name)
            )

        code_pointer = repository_code_pointer_dict[repository_name]
        return RepositoryPythonOrigin(
            executable_path=list_repositories_reply.executable_path or sys.executable,
            code_pointer=code_pointer,
        )


class PythonEnvRepositoryLocationHandle(
    namedtuple(
        "_PythonEnvRepositoryLocationHandle",
        "loadable_target_origin location_name repository_code_pointer_dict",
    ),
    RepositoryLocationHandle,
):
    def __new__(cls, loadable_target_origin, location_name, repository_code_pointer_dict):
        return super(PythonEnvRepositoryLocationHandle, cls).__new__(
            cls,
            check.inst_param(
                loadable_target_origin, "loadable_target_origin", LoadableTargetOrigin
            ),
            check.str_param(location_name, "location_name"),
            check.dict_param(
                repository_code_pointer_dict,
                "repository_code_pointer_dict",
                key_type=str,
                value_type=CodePointer,
            ),
        )

    @property
    def executable_path(self):
        return self.loadable_target_origin.executable_path

    def create_reloaded_handle(self):
        return RepositoryLocationHandle.create_python_env_location(
            self.loadable_target_origin, self.location_name,
        )


class ManagedGrpcPythonEnvRepositoryLocationHandle(
    namedtuple(
        "_ManagedGrpcPythonEnvRepositoryLocationHandle",
        "loadable_target_origin executable_path location_name repository_code_pointer_dict "
        "grpc_server_process client heartbeat_thread heartbeat_shutdown_event",
    ),
    RepositoryLocationHandle,
):
    """
    A Python environment for which Dagster is managing a gRPC server.
    """

    def __new__(
        cls,
        loadable_target_origin,
        executable_path,
        location_name,
        repository_code_pointer_dict,
        grpc_server_process,
        client,
        heartbeat_thread,
        heartbeat_shutdown_event,
    ):
        from dagster.grpc.client import DagsterGrpcClient
        from dagster.grpc.server import GrpcServerProcess

        return super(ManagedGrpcPythonEnvRepositoryLocationHandle, cls).__new__(
            cls,
            check.inst_param(
                loadable_target_origin, "loadable_target_origin", LoadableTargetOrigin
            ),
            check.str_param(executable_path, "executable_path"),
            check.str_param(location_name, "location_name"),
            check.dict_param(
                repository_code_pointer_dict,
                "repository_code_pointer_dict",
                key_type=str,
                value_type=CodePointer,
            ),
            check.inst_param(grpc_server_process, "grpc_server_process", GrpcServerProcess),
            check.inst_param(client, "client", DagsterGrpcClient),
            check.inst_param(heartbeat_thread, "heartbeat_thread", threading.Thread),
            heartbeat_shutdown_event,
        )

    @property
    def repository_names(self):
        return set(self.repository_code_pointer_dict.keys())

    @property
    def host(self):
        return "localhost"

    @property
    def port(self):
        return self.grpc_server_process.port

    @property
    def socket(self):
        return self.grpc_server_process.socket

    def create_reloaded_handle(self):
        return RepositoryLocationHandle.create_process_bound_grpc_server_location(
            self.loadable_target_origin, self.location_name,
        )

    def cleanup(self):
        self.heartbeat_shutdown_event.set()
        self.heartbeat_thread.join()
        self.client.cleanup_server()


class InProcessRepositoryLocationHandle(
    namedtuple("_InProcessRepositoryLocationHandle", "location_name repository_code_pointer_dict"),
    RepositoryLocationHandle,
):
    def __new__(cls, location_name, repository_code_pointer_dict):
        return super(InProcessRepositoryLocationHandle, cls).__new__(
            cls,
            check.str_param(location_name, "location_name"),
            check.dict_param(
                repository_code_pointer_dict,
                "repository_code_pointer_dict",
                key_type=str,
                value_type=CodePointer,
            ),
        )

    def create_reloaded_handle(self):
        raise NotImplementedError("Not implemented for in-process")


class RepositoryHandle(
    namedtuple("_RepositoryHandle", "repository_name repository_location_handle")
):
    def __new__(cls, repository_name, repository_location_handle):
        return super(RepositoryHandle, cls).__new__(
            cls,
            check.str_param(repository_name, "repository_name"),
            check.inst_param(
                repository_location_handle, "repository_location_handle", RepositoryLocationHandle
            ),
        )

    def get_origin(self):
        if isinstance(self.repository_location_handle, InProcessRepositoryLocationHandle):
            return RepositoryPythonOrigin(
                code_pointer=self.repository_location_handle.repository_code_pointer_dict[
                    self.repository_name
                ],
                executable_path=sys.executable,
            )
        elif isinstance(
            self.repository_location_handle, PythonEnvRepositoryLocationHandle
        ) or isinstance(
            self.repository_location_handle, ManagedGrpcPythonEnvRepositoryLocationHandle
        ):
            return RepositoryPythonOrigin(
                code_pointer=self.repository_location_handle.repository_code_pointer_dict[
                    self.repository_name
                ],
                executable_path=self.repository_location_handle.executable_path,
            )
        elif isinstance(self.repository_location_handle, GrpcServerRepositoryLocationHandle):
            return RepositoryGrpcServerOrigin(
                host=self.repository_location_handle.host,
                port=self.repository_location_handle.port,
                socket=self.repository_location_handle.socket,
                repository_name=self.repository_name,
            )
        else:
            check.failed(
                "Can not target represented RepositoryDefinition locally for repository from a {}.".format(
                    self.repository_location_handle.__class__.__name__
                )
            )


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
        return self.repository_handle.repository_location_handle.location_name

    def get_origin(self):
        return self.repository_handle.get_origin().get_pipeline_origin(self.pipeline_name)

    def to_selector(self):
        return PipelineSelector(self.location_name, self.repository_name, self.pipeline_name, None)


class ScheduleHandle(namedtuple("_ScheduleHandle", "schedule_name repository_handle")):
    def __new__(cls, schedule_name, repository_handle):
        return super(ScheduleHandle, cls).__new__(
            cls,
            check.str_param(schedule_name, "schedule_name"),
            check.inst_param(repository_handle, "repository_handle", RepositoryHandle),
        )

    @property
    def repository_name(self):
        return self.repository_handle.repository_name

    @property
    def location_name(self):
        return self.repository_handle.repository_location_handle.location_name

    def get_origin(self):
        return self.repository_handle.get_origin().get_schedule_origin(self.schedule_name)


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
        return self.repository_handle.repository_location_handle.location_name
