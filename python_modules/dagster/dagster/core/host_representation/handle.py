import sys
import threading
from abc import ABCMeta, abstractmethod
from collections import namedtuple
from enum import Enum

import six
from dagster import check
from dagster.api.list_repositories import sync_list_repositories, sync_list_repositories_grpc
from dagster.core.code_pointer import CodePointer
from dagster.core.definitions.reconstructable import repository_def_from_pointer
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.host_representation.origin import (
    GrpcServerRepositoryLocationOrigin,
    InProcessRepositoryLocationOrigin,
    ManagedGrpcPythonEnvRepositoryLocationOrigin,
    PythonEnvRepositoryLocationOrigin,
    RepositoryLocationOrigin,
)
from dagster.core.host_representation.selector import PipelineSelector
from dagster.core.instance import DagsterInstance
from dagster.core.origin import RepositoryGrpcServerOrigin, RepositoryOrigin, RepositoryPythonOrigin


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
        UserProcessApi.CLI
        if (opt_in_settings and not opt_in_settings["local_servers"])
        else UserProcessApi.GRPC
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
    def create_from_repository_location_origin(repo_location_origin):
        check.inst_param(repo_location_origin, "repo_location_origin", RepositoryLocationOrigin)
        if isinstance(repo_location_origin, PythonEnvRepositoryLocationOrigin):
            return PythonEnvRepositoryLocationHandle(repo_location_origin)
        elif isinstance(repo_location_origin, ManagedGrpcPythonEnvRepositoryLocationOrigin):
            return ManagedGrpcPythonEnvRepositoryLocationHandle(repo_location_origin)
        elif isinstance(repo_location_origin, GrpcServerRepositoryLocationOrigin):
            return GrpcServerRepositoryLocationHandle(repo_location_origin)
        elif isinstance(repo_location_origin, InProcessRepositoryLocationOrigin):
            return InProcessRepositoryLocationHandle(repo_location_origin)
        else:
            check.failed("Unexpected repository location origin")

    @staticmethod
    def create_from_repository_origin(repository_origin, instance):
        check.inst_param(repository_origin, "repository_origin", RepositoryOrigin)
        check.inst_param(instance, "instance", DagsterInstance)

        if isinstance(repository_origin, RepositoryGrpcServerOrigin):
            return RepositoryLocationHandle.create_from_repository_location_origin(
                GrpcServerRepositoryLocationOrigin(
                    port=repository_origin.port,
                    socket=repository_origin.socket,
                    host=repository_origin.host,
                )
            )
        elif isinstance(repository_origin, RepositoryPythonOrigin):
            loadable_target_origin = repository_origin.loadable_target_origin
            user_process_api = python_user_process_api_from_instance(instance)

            repo_location_origin = (
                ManagedGrpcPythonEnvRepositoryLocationOrigin(loadable_target_origin)
                if user_process_api == UserProcessApi.GRPC
                else PythonEnvRepositoryLocationOrigin(loadable_target_origin)
            )

            return RepositoryLocationHandle.create_from_repository_location_origin(
                repo_location_origin
            )
        else:
            raise DagsterInvariantViolationError("Unexpected repository origin type")


class GrpcServerRepositoryLocationHandle(RepositoryLocationHandle):
    """
    Represents a gRPC server that Dagster is not responsible for managing.
    """

    def __init__(self, origin):
        from dagster.grpc.client import DagsterGrpcClient

        self.origin = check.inst_param(origin, "origin", GrpcServerRepositoryLocationOrigin)

        port = self.origin.port
        socket = self.origin.socket
        host = self.origin.host

        self.client = DagsterGrpcClient(port=port, socket=socket, host=host)

        list_repositories_response = sync_list_repositories_grpc(self.client)

        self.repository_names = set(
            symbol.repository_name for symbol in list_repositories_response.repository_symbols
        )

    @property
    def port(self):
        return self.origin.port

    @property
    def socket(self):
        return self.origin.socket

    @property
    def host(self):
        return self.origin.host

    @property
    def location_name(self):
        return self.origin.location_name

    def create_reloaded_handle(self):
        return RepositoryLocationHandle.create_from_repository_location_origin(self.origin)

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


class PythonEnvRepositoryLocationHandle(RepositoryLocationHandle):
    def __init__(self, origin):
        self.origin = check.inst_param(origin, "origin", PythonEnvRepositoryLocationOrigin)
        loadable_target_origin = self.origin.loadable_target_origin

        response = sync_list_repositories(
            executable_path=loadable_target_origin.executable_path,
            python_file=loadable_target_origin.python_file,
            module_name=loadable_target_origin.module_name
            if loadable_target_origin.module_name
            else loadable_target_origin.package_name,
            working_directory=loadable_target_origin.working_directory,
            attribute=loadable_target_origin.attribute,
        )

        if loadable_target_origin.python_file:
            self.repository_code_pointer_dict = {
                lrs.repository_name: CodePointer.from_python_file(
                    loadable_target_origin.python_file,
                    lrs.attribute,
                    loadable_target_origin.working_directory,
                )
                for lrs in response.repository_symbols
            }
        elif loadable_target_origin.package_name:
            self.repository_code_pointer_dict = {
                lrs.repository_name: CodePointer.from_python_package(
                    loadable_target_origin.package_name, lrs.attribute
                )
                for lrs in response.repository_symbols
            }
        else:
            self.repository_code_pointer_dict = {
                lrs.repository_name: CodePointer.from_module(
                    loadable_target_origin.module_name, lrs.attribute
                )
                for lrs in response.repository_symbols
            }

    @property
    def loadable_target_origin(self):
        return self.origin.loadable_target_origin

    @property
    def location_name(self):
        return self.origin.location_name

    @property
    def executable_path(self):
        return self.loadable_target_origin.executable_path

    def create_reloaded_handle(self):
        return RepositoryLocationHandle.create_from_repository_location_origin(self.origin)


class ManagedGrpcPythonEnvRepositoryLocationHandle(RepositoryLocationHandle):
    """
    A Python environment for which Dagster is managing a gRPC server.
    """

    def __init__(self, origin):
        from dagster.grpc.client import client_heartbeat_thread
        from dagster.grpc.server import GrpcServerProcess

        self.origin = check.inst_param(
            origin, "origin", ManagedGrpcPythonEnvRepositoryLocationOrigin
        )
        loadable_target_origin = origin.loadable_target_origin

        self.grpc_server_process = GrpcServerProcess(
            loadable_target_origin=loadable_target_origin,
            max_workers=2,
            heartbeat=True,
            lazy_load_user_code=True,
        )
        self.client = self.grpc_server_process.create_ephemeral_client()

        self.heartbeat_shutdown_event = threading.Event()

        self.heartbeat_thread = threading.Thread(
            target=client_heartbeat_thread, args=(self.client, self.heartbeat_shutdown_event)
        )
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
        list_repositories_response = sync_list_repositories_grpc(self.client)

        self.executable_path = list_repositories_response.executable_path

        self.repository_code_pointer_dict = list_repositories_response.repository_code_pointer_dict

    @property
    def location_name(self):
        return self.origin.location_name

    @property
    def loadable_target_origin(self):
        return self.origin.loadable_target_origin

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
        return RepositoryLocationHandle.create_from_repository_location_origin(self.origin)

    def cleanup(self):
        self.heartbeat_shutdown_event.set()
        self.heartbeat_thread.join()
        self.client.cleanup_server()


class InProcessRepositoryLocationHandle(RepositoryLocationHandle):
    def __init__(self, origin):
        self.origin = check.inst_param(origin, "origin", InProcessRepositoryLocationOrigin)

        pointer = self.origin.recon_repo.pointer
        repo_def = repository_def_from_pointer(pointer)
        self.repository_code_pointer_dict = {repo_def.name: pointer}

    @property
    def location_name(self):
        return self.origin.location_name

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
