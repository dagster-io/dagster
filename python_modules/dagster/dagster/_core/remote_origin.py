import os
from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, NoReturn, Optional, cast

from dagster_shared.record import IHaveNew, LegacyNamedTupleMixin, record, record_custom

import dagster._check as check
from dagster._core.errors import DagsterInvariantViolationError, DagsterUserCodeUnreachableError
from dagster._core.instance.config import DEFAULT_LOCAL_CODE_SERVER_STARTUP_TIMEOUT
from dagster._core.origin import DEFAULT_DAGSTER_ENTRY_POINT
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._serdes import create_snapshot_id, whitelist_for_serdes

if TYPE_CHECKING:
    from dagster._core.definitions.selector import (
        InstigatorSelector,
        PartitionSetSelector,
        RepositorySelector,
    )
    from dagster._core.instance import DagsterInstance
    from dagster._core.remote_representation.code_location import (
        CodeLocation,
        GrpcServerCodeLocation,
        InProcessCodeLocation,
    )
    from dagster._grpc.client import DagsterGrpcClient


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
    return f"grpc:{host}:{socket if socket else port}"


def _assign_loadable_target_origin_name(loadable_target_origin: LoadableTargetOrigin) -> str:
    check.inst_param(loadable_target_origin, "loadable_target_origin", LoadableTargetOrigin)

    if loadable_target_origin.package_name:
        file_or_module = loadable_target_origin.package_name
    elif loadable_target_origin.module_name:
        file_or_module = loadable_target_origin.module_name
    elif loadable_target_origin.autoload_defs_module_name:
        file_or_module = loadable_target_origin.autoload_defs_module_name
    elif loadable_target_origin.python_file:
        file_or_module = os.path.basename(loadable_target_origin.python_file)
    else:
        check.failed(f"Unexpected LoadableTargetOrigin structure: {loadable_target_origin}")

    return (
        f"{file_or_module}:{loadable_target_origin.attribute}"
        if loadable_target_origin.attribute
        else file_or_module
    )


class CodeLocationOrigin(ABC):
    """Serializable representation of a CodeLocation that can be used to
    uniquely identify the location or reload it in across process boundaries.
    """

    @property
    def is_reload_supported(self) -> bool:
        return True

    @property
    def is_shutdown_supported(self) -> bool:
        return False

    def shutdown_server(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_display_metadata(self) -> Mapping[str, Any]:
        pass

    def get_id(self) -> str:
        # Type-ignored because `create_snapshot` takes a `NamedTuple`, and all descendants of this
        # class are `NamedTuple`, but we can't specify `NamedTuple` in the signature here.
        return create_snapshot_id(self)  # type: ignore

    @property
    @abstractmethod
    def location_name(self) -> str:
        pass

    @property
    @abstractmethod
    def loadable_target_origin(self) -> LoadableTargetOrigin: ...

    @abstractmethod
    def create_location(self, instance: "DagsterInstance") -> "CodeLocation":
        pass

    @abstractmethod
    def reload_location(self, instance: "DagsterInstance") -> "CodeLocation":
        pass


# Different storage name for backcompat
@whitelist_for_serdes(storage_name="RegisteredRepositoryLocationOrigin")
@record(kw_only=False)
class RegisteredCodeLocationOrigin(LegacyNamedTupleMixin, CodeLocationOrigin):
    """Identifies a repository location of a handle managed using metadata stored outside of the
    origin - can only be loaded in an environment that is managing repository locations using
    its own mapping from location name to repository location metadata.
    """

    location_name: str  # pyright: ignore[reportIncompatibleMethodOverride]

    def get_display_metadata(self) -> Mapping[str, Any]:
        return {}

    def create_location(self, instance: "DagsterInstance") -> NoReturn:
        raise DagsterInvariantViolationError(
            "A RegisteredCodeLocationOrigin does not have enough information to create its "
            "code location on its own."
        )

    def reload_location(self, instance: "DagsterInstance") -> NoReturn:
        raise DagsterInvariantViolationError(
            "A RegisteredCodeLocationOrigin does not have enough information to reload its "
            "code location on its own."
        )

    @property
    def loadable_target_origin(self) -> LoadableTargetOrigin:
        raise DagsterInvariantViolationError(
            "A RegisteredCodeLocationOrigin does not have enough information to provide a "
            "loadable target."
        )


# Different storage name for backcompat
@whitelist_for_serdes(storage_name="InProcessRepositoryLocationOrigin")
@record_custom
class InProcessCodeLocationOrigin(IHaveNew, LegacyNamedTupleMixin, CodeLocationOrigin):
    loadable_target_origin: LoadableTargetOrigin  # pyright: ignore[reportIncompatibleMethodOverride]
    location_name: str  # pyright: ignore[reportIncompatibleMethodOverride]
    container_image: Optional[str]
    entry_point: Sequence[str]
    container_context: Optional[Mapping[str, Any]]

    """Identifies a repository location constructed in the same process. Primarily
    used in tests, since Dagster system processes like the webserver and daemon do not
    load user code in the same process.
    """

    def __new__(
        cls,
        loadable_target_origin: LoadableTargetOrigin,
        container_image: Optional[str] = None,
        entry_point: Optional[Sequence[str]] = None,
        container_context=None,
        location_name: Optional[str] = None,
    ):
        return super().__new__(
            cls,
            loadable_target_origin=loadable_target_origin,
            container_image=container_image,
            entry_point=entry_point if entry_point else DEFAULT_DAGSTER_ENTRY_POINT,
            container_context=container_context,
            location_name=location_name if location_name else IN_PROCESS_NAME,
        )

    @property
    def is_reload_supported(self) -> bool:
        return False

    def get_display_metadata(self) -> Mapping[str, Any]:
        return {}

    def create_location(self, instance: "DagsterInstance") -> "InProcessCodeLocation":
        from dagster._core.remote_representation.code_location import InProcessCodeLocation

        return InProcessCodeLocation(self, instance=instance)

    def reload_location(self, instance: "DagsterInstance") -> "InProcessCodeLocation":
        raise NotImplementedError


# Different storage name for backcompat
@whitelist_for_serdes(storage_name="ManagedGrpcPythonEnvRepositoryLocationOrigin")
@record_custom
class ManagedGrpcPythonEnvCodeLocationOrigin(IHaveNew, LegacyNamedTupleMixin, CodeLocationOrigin):
    """Identifies a repository location in a Python environment. Dagster creates a gRPC server
    for these repository locations on startup.
    """

    loadable_target_origin: LoadableTargetOrigin  # pyright: ignore[reportIncompatibleMethodOverride]
    location_name: str  # pyright: ignore[reportIncompatibleMethodOverride]

    def __new__(
        cls, loadable_target_origin: LoadableTargetOrigin, location_name: Optional[str] = None
    ):
        return super().__new__(
            cls,
            loadable_target_origin=loadable_target_origin,
            location_name=location_name
            if location_name
            else _assign_loadable_target_origin_name(loadable_target_origin),
        )

    def get_display_metadata(self) -> Mapping[str, str]:
        metadata = {
            "python_file": self.loadable_target_origin.python_file,
            "module_name": self.loadable_target_origin.module_name,
            "autoload_defs_module_name": self.loadable_target_origin.autoload_defs_module_name,
            "working_directory": self.loadable_target_origin.working_directory,
            "attribute": self.loadable_target_origin.attribute,
            "package_name": self.loadable_target_origin.package_name,
            "executable_path": self.loadable_target_origin.executable_path,
        }
        return {key: value for key, value in metadata.items() if value is not None}

    def create_location(self, instance: "DagsterInstance") -> NoReturn:
        raise DagsterInvariantViolationError(
            "A ManagedGrpcPythonEnvCodeLocationOrigin needs a GrpcServerRegistry"
            " in order to create a code location."
        )

    def reload_location(self, instance: "DagsterInstance") -> NoReturn:
        raise DagsterInvariantViolationError(
            "A ManagedGrpcPythonEnvCodeLocationOrigin needs a GrpcServerRegistry"
            " in order to reload a code location."
        )

    @contextmanager
    def create_single_location(
        self,
        instance: "DagsterInstance",
    ) -> Iterator["GrpcServerCodeLocation"]:
        from dagster._core.remote_representation.code_location import GrpcServerCodeLocation
        from dagster._core.remote_representation.grpc_server_registry import GrpcServerRegistry
        from dagster._core.workspace.context import WEBSERVER_GRPC_SERVER_HEARTBEAT_TTL
        from dagster._grpc.server import GrpcServerCommand

        with GrpcServerRegistry(
            instance_ref=instance.get_ref(),
            server_command=GrpcServerCommand.API_GRPC,
            heartbeat_ttl=WEBSERVER_GRPC_SERVER_HEARTBEAT_TTL,
            startup_timeout=(
                instance.code_server_process_startup_timeout
                if instance
                else DEFAULT_LOCAL_CODE_SERVER_STARTUP_TIMEOUT
            ),
            wait_for_processes_on_shutdown=instance.wait_for_local_code_server_processes_on_shutdown,
        ) as grpc_server_registry:
            endpoint = grpc_server_registry.get_grpc_endpoint(self)
            with GrpcServerCodeLocation(
                origin=self,
                port=endpoint.port,
                socket=endpoint.socket,
                host=endpoint.host,
                heartbeat=True,
                watch_server=False,
                grpc_server_registry=grpc_server_registry,
                instance=instance,
            ) as location:
                yield location


# Different storage name for backcompat
@whitelist_for_serdes(
    storage_name="GrpcServerRepositoryLocationOrigin",
    skip_when_empty_fields={"use_ssl", "additional_metadata"},
)
@record_custom
class GrpcServerCodeLocationOrigin(IHaveNew, LegacyNamedTupleMixin, CodeLocationOrigin):
    """Identifies a repository location hosted in a gRPC server managed by the user. Dagster
    is not responsible for managing the lifecycle of the server.
    """

    host: str
    port: Optional[int]
    socket: Optional[str]
    location_name: str  # pyright: ignore[reportIncompatibleMethodOverride]
    use_ssl: Optional[bool]
    additional_metadata: Optional[Mapping[str, Any]]

    def __new__(
        cls,
        host: str,
        port: Optional[int] = None,
        socket: Optional[str] = None,
        location_name: Optional[str] = None,
        use_ssl: Optional[bool] = None,
        additional_metadata: Optional[Mapping[str, Any]] = None,
    ):
        return super().__new__(
            cls,
            host=host,
            port=port,
            socket=socket,
            location_name=location_name
            if location_name
            else _assign_grpc_location_name(port, socket, host),
            use_ssl=use_ssl,
            additional_metadata=additional_metadata,
        )

    def get_display_metadata(self) -> Mapping[str, str]:
        metadata = {
            "host": self.host,
            "port": str(self.port) if self.port else None,
            "socket": self.socket,
            **(self.additional_metadata if self.additional_metadata else {}),
        }
        return {key: value for key, value in metadata.items() if value is not None}

    def reload_location(self, instance: "DagsterInstance") -> "GrpcServerCodeLocation":
        # deferred for import perf
        import grpc

        from dagster._core.remote_representation.code_location import GrpcServerCodeLocation

        try:
            self.create_client().reload_code(timeout=instance.code_server_reload_timeout)
        except Exception as e:
            # Handle case when this is called against `dagster api grpc` servers that don't have this API method implemented
            if (
                isinstance(e.__cause__, grpc.RpcError)
                and cast("grpc.RpcError", e.__cause__).code() == grpc.StatusCode.UNIMPLEMENTED
            ):
                pass
            else:
                raise

        return GrpcServerCodeLocation(self, instance=instance)

    def create_location(self, instance: "DagsterInstance") -> "GrpcServerCodeLocation":
        from dagster._core.remote_representation.code_location import GrpcServerCodeLocation

        return GrpcServerCodeLocation(self, instance=instance)

    def create_client(self) -> "DagsterGrpcClient":
        from dagster._grpc.client import DagsterGrpcClient

        return DagsterGrpcClient(
            port=self.port,
            socket=self.socket,
            host=self.host,
            use_ssl=bool(self.use_ssl),
        )

    @property
    def is_shutdown_supported(self) -> bool:
        return True

    def shutdown_server(self) -> None:
        try:
            self.create_client().shutdown_server()
        except DagsterUserCodeUnreachableError:
            # Server already shutdown
            pass

    @property
    def loadable_target_origin(self) -> LoadableTargetOrigin:
        raise DagsterInvariantViolationError(
            "A GrpcServerCodeLocationOrigin does not directly know its loadable target."
        )


# Different storage field name for backcompat
@whitelist_for_serdes(
    storage_name="ExternalRepositoryOrigin",
    storage_field_names={"code_location_origin": "repository_location_origin"},
)
@record(kw_only=False)
class RemoteRepositoryOrigin(LegacyNamedTupleMixin):
    """Serializable representation of an ExternalRepository that can be used to
    uniquely it or reload it in across process boundaries.
    """

    code_location_origin: CodeLocationOrigin
    repository_name: str

    def get_id(self) -> str:
        return create_snapshot_id(self)

    def get_selector_id(self) -> str:
        return create_snapshot_id(self.get_selector())

    def get_selector(self) -> "RepositorySelector":
        from dagster._core.definitions.selector import RepositorySelector

        return RepositorySelector(
            location_name=self.code_location_origin.location_name,
            repository_name=self.repository_name,
        )

    def get_label(self) -> str:
        return f"{self.repository_name}@{self.code_location_origin.location_name}"

    def get_job_origin(self, job_name: str) -> "RemoteJobOrigin":
        return RemoteJobOrigin(repository_origin=self, job_name=job_name)

    def get_instigator_origin(self, instigator_name: str) -> "RemoteInstigatorOrigin":
        return RemoteInstigatorOrigin(repository_origin=self, instigator_name=instigator_name)

    def get_partition_set_origin(self, partition_set_name: str) -> "RemotePartitionSetOrigin":
        return RemotePartitionSetOrigin(
            repository_origin=self, partition_set_name=partition_set_name
        )


@whitelist_for_serdes(
    storage_name="ExternalPipelineOrigin",
    storage_field_names={
        "repository_origin": "external_repository_origin",
        "job_name": "pipeline_name",
    },
)
@record(kw_only=False)
class RemoteJobOrigin(LegacyNamedTupleMixin):
    """Serializable representation of an ExternalJob that can be used to
    uniquely it or reload it in across process boundaries.
    """

    repository_origin: RemoteRepositoryOrigin
    job_name: str

    def get_id(self) -> str:
        return create_snapshot_id(self)

    @property
    def location_name(self) -> str:
        return self.repository_origin.code_location_origin.location_name


@whitelist_for_serdes(
    # ExternalInstigatorOrigin used to be called ExternalJobOrigin, before the concept of "job" was
    # introduced in 0.12.0. For clarity, we changed the name of the namedtuple with `0.14.0`, but we
    # need to maintain the serialized format in order to avoid changing the origin id that is stored in
    # our schedule storage.  This registers the serialized ExternalJobOrigin named tuple class to be
    # deserialized as an ExternalInstigatorOrigin, using its corresponding serializer for serdes.
    storage_name="ExternalJobOrigin",
    storage_field_names={
        "repository_origin": "external_repository_origin",
        "instigator_name": "job_name",
    },
)
@record(kw_only=False)
class RemoteInstigatorOrigin(LegacyNamedTupleMixin):
    """Serializable representation of an ExternalJob that can be used to
    uniquely it or reload it in across process boundaries.
    """

    repository_origin: RemoteRepositoryOrigin
    instigator_name: str

    def get_selector(self) -> "InstigatorSelector":
        from dagster._core.definitions.selector import InstigatorSelector

        return InstigatorSelector(
            location_name=self.repository_origin.code_location_origin.location_name,
            repository_name=self.repository_origin.repository_name,
            name=self.instigator_name,
        )

    def get_id(self) -> str:
        return create_snapshot_id(self)

    @property
    def location_name(self) -> str:
        return self.repository_origin.code_location_origin.location_name


@whitelist_for_serdes(
    storage_name="ExternalPartitionSetOrigin",
    storage_field_names={"repository_origin": "external_repository_origin"},
)
@record
class RemotePartitionSetOrigin:
    """Serializable representation of an ExternalPartitionSet that can be used to
    uniquely it or reload it in across process boundaries.
    """

    repository_origin: RemoteRepositoryOrigin
    partition_set_name: str

    def get_id(self) -> str:
        return create_snapshot_id(self)

    @property
    def selector(self) -> "PartitionSetSelector":
        from dagster._core.definitions.selector import PartitionSetSelector

        return PartitionSetSelector(
            location_name=self.repository_origin.code_location_origin.location_name,
            repository_name=self.repository_origin.repository_name,
            partition_set_name=self.partition_set_name,
        )

    def get_selector_id(self) -> str:
        return create_snapshot_id(self.selector)
