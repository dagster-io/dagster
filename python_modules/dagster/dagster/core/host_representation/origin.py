import os
import sys
from abc import ABC, abstractmethod
from contextlib import contextmanager
from inspect import Parameter
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generator,
    List,
    Mapping,
    NamedTuple,
    NoReturn,
    Optional,
    Set,
    Type,
    cast,
)

import dagster._check as check
from dagster.core.errors import DagsterInvariantViolationError, DagsterUserCodeUnreachableError
from dagster.core.origin import DEFAULT_DAGSTER_ENTRY_POINT
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.serdes import (
    DefaultNamedTupleSerializer,
    create_snapshot_id,
    register_serdes_tuple_fallbacks,
    whitelist_for_serdes,
)
from dagster.serdes.serdes import WhitelistMap, unpack_inner_value

from .selector import RepositorySelector

if TYPE_CHECKING:
    from dagster.core.host_representation.repository_location import (
        GrpcServerRepositoryLocation,
        InProcessRepositoryLocation,
        RepositoryLocation,
    )
    from dagster.core.instance import DagsterInstance
    from dagster.grpc.client import DagsterGrpcClient

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


def _assign_loadable_target_origin_name(loadable_target_origin: LoadableTargetOrigin) -> str:
    check.inst_param(loadable_target_origin, "loadable_target_origin", LoadableTargetOrigin)

    file_or_module = (
        loadable_target_origin.package_name
        if loadable_target_origin.package_name
        else (
            loadable_target_origin.module_name
            if loadable_target_origin.module_name
            else os.path.basename(cast(str, loadable_target_origin.python_file))
        )
    )

    return (
        "{file_or_module}:{attribute}".format(
            file_or_module=file_or_module, attribute=loadable_target_origin.attribute
        )
        if loadable_target_origin.attribute
        else file_or_module
    )


class RepositoryLocationOrigin(ABC, tuple):
    """Serializable representation of a RepositoryLocation that can be used to
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
    def get_display_metadata(self) -> Dict[str, Any]:
        pass

    def get_id(self) -> str:
        return create_snapshot_id(self)

    @property
    @abstractmethod
    def location_name(self) -> str:
        pass

    @abstractmethod
    def create_location(self) -> "RepositoryLocation":
        pass

    @property
    def supports_server_watch(self):
        return False


@whitelist_for_serdes
class RegisteredRepositoryLocationOrigin(
    NamedTuple("RegisteredRepositoryLocationOrigin", [("location_name", str)]),
    RepositoryLocationOrigin,
):
    """Identifies a repository location of a handle managed using metadata stored outside of the
    origin - can only be loaded in an environment that is managing repository locations using
    its own mapping from location name to repository location metadata.
    """

    def __new__(cls, location_name: str):
        return super(RegisteredRepositoryLocationOrigin, cls).__new__(cls, location_name)

    def get_display_metadata(self) -> Dict[str, Any]:
        return {}

    def create_location(self) -> NoReturn:
        raise DagsterInvariantViolationError(
            "A RegisteredRepositoryLocationOrigin does not have enough information to load its "
            "repository location on its own."
        )


@whitelist_for_serdes
class InProcessRepositoryLocationOrigin(
    NamedTuple(
        "_InProcessRepositoryLocationOrigin",
        [
            ("loadable_target_origin", LoadableTargetOrigin),
            ("container_image", Optional[str]),
            ("entry_point", List[str]),
            ("container_context", Optional[Dict[str, Any]]),
        ],
    ),
    RepositoryLocationOrigin,
):
    """Identifies a repository location constructed in the same process. Primarily
    used in tests, since Dagster system processes like Dagit and the daemon do not
    load user code in the same process.
    """

    def __new__(
        cls,
        loadable_target_origin: LoadableTargetOrigin,
        container_image: Optional[str] = None,
        entry_point: Optional[List[str]] = None,
        container_context=None,
    ):
        return super(InProcessRepositoryLocationOrigin, cls).__new__(
            cls,
            check.inst_param(
                loadable_target_origin, "loadable_target_origin", LoadableTargetOrigin
            ),
            container_image=check.opt_str_param(container_image, "container_image"),
            entry_point=(
                check.opt_list_param(entry_point, "entry_point")
                if entry_point
                else DEFAULT_DAGSTER_ENTRY_POINT
            ),
            container_context=check.opt_dict_param(container_context, "container_context"),
        )

    @property
    def location_name(self) -> str:
        return IN_PROCESS_NAME

    @property
    def is_reload_supported(self) -> bool:
        return False

    def get_display_metadata(self) -> Dict[str, Any]:
        return {}

    def create_location(self) -> "InProcessRepositoryLocation":
        from dagster.core.host_representation.repository_location import InProcessRepositoryLocation

        return InProcessRepositoryLocation(self)


@whitelist_for_serdes
class ManagedGrpcPythonEnvRepositoryLocationOrigin(
    NamedTuple(
        "_ManagedGrpcPythonEnvRepositoryLocationOrigin",
        [("loadable_target_origin", LoadableTargetOrigin), ("location_name", str)],
    ),
    RepositoryLocationOrigin,
):
    """Identifies a repository location in a Python environment. Dagster creates a gRPC server
    for these repository locations on startup.
    """

    def __new__(
        cls, loadable_target_origin: LoadableTargetOrigin, location_name: Optional[str] = None
    ):
        return super(ManagedGrpcPythonEnvRepositoryLocationOrigin, cls).__new__(
            cls,
            check.inst_param(
                loadable_target_origin, "loadable_target_origin", LoadableTargetOrigin
            ),
            check.str_param(location_name, "location_name")
            if location_name
            else _assign_loadable_target_origin_name(loadable_target_origin),
        )

    def get_display_metadata(self) -> Dict[str, str]:
        metadata = {
            "python_file": self.loadable_target_origin.python_file,
            "module_name": self.loadable_target_origin.module_name,
            "working_directory": self.loadable_target_origin.working_directory,
            "attribute": self.loadable_target_origin.attribute,
            "package_name": self.loadable_target_origin.package_name,
            "executable_path": (
                self.loadable_target_origin.executable_path
                if self.loadable_target_origin.executable_path != sys.executable
                else None
            ),
        }
        return {key: value for key, value in metadata.items() if value is not None}

    def create_location(self) -> NoReturn:
        raise DagsterInvariantViolationError(
            "A ManagedGrpcPythonEnvRepositoryLocationOrigin needs a DynamicWorkspace"
            " in order to create a handle."
        )

    @contextmanager
    def create_single_location(
        self, instance: "DagsterInstance"
    ) -> Generator["RepositoryLocation", None, None]:
        from dagster.core.workspace.context import DAGIT_GRPC_SERVER_HEARTBEAT_TTL

        from .grpc_server_registry import ProcessGrpcServerRegistry
        from .repository_location import GrpcServerRepositoryLocation

        with ProcessGrpcServerRegistry(
            reload_interval=0,
            heartbeat_ttl=DAGIT_GRPC_SERVER_HEARTBEAT_TTL,
            startup_timeout=instance.code_server_process_startup_timeout,
        ) as grpc_server_registry:
            endpoint = grpc_server_registry.get_grpc_endpoint(self)
            with GrpcServerRepositoryLocation(
                origin=self,
                server_id=endpoint.server_id,
                port=endpoint.port,
                socket=endpoint.socket,
                host=endpoint.host,
                heartbeat=True,
                watch_server=False,
                grpc_server_registry=grpc_server_registry,
            ) as location:
                yield location


class GrpcServerOriginSerializer(DefaultNamedTupleSerializer):
    @classmethod
    def skip_when_empty(cls) -> Set[str]:
        return {"use_ssl"}  # Maintain stable origin ID for origins without use_ssl set


@whitelist_for_serdes(serializer=GrpcServerOriginSerializer)
class GrpcServerRepositoryLocationOrigin(
    NamedTuple(
        "_GrpcServerRepositoryLocationOrigin",
        [
            ("host", str),
            ("port", Optional[int]),
            ("socket", Optional[str]),
            ("location_name", str),
            ("use_ssl", Optional[bool]),
        ],
    ),
    RepositoryLocationOrigin,
):
    """Identifies a repository location hosted in a gRPC server managed by the user. Dagster
    is not responsible for managing the lifecycle of the server.
    """

    def __new__(
        cls,
        host: str,
        port: Optional[int] = None,
        socket: Optional[str] = None,
        location_name: Optional[str] = None,
        use_ssl: Optional[bool] = None,
    ):
        return super(GrpcServerRepositoryLocationOrigin, cls).__new__(
            cls,
            check.str_param(host, "host"),
            check.opt_int_param(port, "port"),
            check.opt_str_param(socket, "socket"),
            check.str_param(location_name, "location_name")
            if location_name
            else _assign_grpc_location_name(port, socket, host),
            use_ssl if check.opt_bool_param(use_ssl, "use_ssl") else None,
        )

    def get_display_metadata(self) -> Dict[str, str]:
        metadata = {
            "host": self.host,
            "port": str(self.port) if self.port else None,
            "socket": self.socket,
        }
        return {key: value for key, value in metadata.items() if value is not None}

    def create_location(self) -> "GrpcServerRepositoryLocation":
        from dagster.core.host_representation.repository_location import (
            GrpcServerRepositoryLocation,
        )

        return GrpcServerRepositoryLocation(self)

    @property
    def supports_server_watch(self) -> bool:
        return True

    def create_client(self) -> "DagsterGrpcClient":
        from dagster.grpc.client import DagsterGrpcClient

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


@whitelist_for_serdes
class ExternalRepositoryOrigin(
    NamedTuple(
        "_ExternalRepositoryOrigin",
        [("repository_location_origin", RepositoryLocationOrigin), ("repository_name", str)],
    )
):
    """Serializable representation of an ExternalRepository that can be used to
    uniquely it or reload it in across process boundaries.
    """

    def __new__(cls, repository_location_origin: RepositoryLocationOrigin, repository_name: str):
        return super(ExternalRepositoryOrigin, cls).__new__(
            cls,
            check.inst_param(
                repository_location_origin, "repository_location_origin", RepositoryLocationOrigin
            ),
            check.str_param(repository_name, "repository_name"),
        )

    def get_id(self) -> str:
        return create_snapshot_id(self)

    def get_selector_id(self) -> str:
        return create_snapshot_id(
            RepositorySelector(self.repository_location_origin.location_name, self.repository_name)
        )

    def get_label(self) -> str:
        return f"{self.repository_name}@{self.repository_location_origin.location_name}"

    def get_pipeline_origin(self, pipeline_name: str) -> "ExternalPipelineOrigin":
        return ExternalPipelineOrigin(self, pipeline_name)

    def get_instigator_origin(self, instigator_name: str) -> "ExternalInstigatorOrigin":
        return ExternalInstigatorOrigin(self, instigator_name)

    def get_partition_set_origin(self, partition_set_name: str) -> "ExternalPartitionSetOrigin":
        return ExternalPartitionSetOrigin(self, partition_set_name)


@whitelist_for_serdes
class ExternalPipelineOrigin(
    NamedTuple(
        "_ExternalPipelineOrigin",
        [("external_repository_origin", ExternalRepositoryOrigin), ("pipeline_name", str)],
    )
):
    """Serializable representation of an ExternalPipeline that can be used to
    uniquely it or reload it in across process boundaries.
    """

    def __new__(cls, external_repository_origin: ExternalRepositoryOrigin, pipeline_name: str):
        return super(ExternalPipelineOrigin, cls).__new__(
            cls,
            check.inst_param(
                external_repository_origin,
                "external_repository_origin",
                ExternalRepositoryOrigin,
            ),
            check.str_param(pipeline_name, "pipeline_name"),
        )

    def get_id(self) -> str:
        return create_snapshot_id(self)


class ExternalInstigatorOriginSerializer(DefaultNamedTupleSerializer):
    @classmethod
    def value_from_storage_dict(
        cls,
        storage_dict: Dict[str, Any],
        klass: Type,
        args_for_class: Mapping[str, Parameter],
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> NamedTuple:
        raw_dict = {
            key: unpack_inner_value(value, whitelist_map, f"{descent_path}.{key}")
            for key, value in storage_dict.items()
        }
        # the stored key for the instigator name should always be `job_name`, for backcompat
        # and origin id stability (hash of the serialized tuple).  Make sure we fetch it from the
        # raw storage dict and pass it in as instigator_name to ExternalInstigatorOrigin
        instigator_name = raw_dict.get("job_name")
        return klass(
            **{key: value for key, value in raw_dict.items() if key in args_for_class},
            instigator_name=instigator_name,
        )

    @classmethod
    def value_to_storage_dict(
        cls,
        value: NamedTuple,
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> Dict[str, Any]:
        storage = super().value_to_storage_dict(
            value,
            whitelist_map,
            descent_path,
        )
        instigator_name = storage.get("instigator_name") or storage.get("job_name")
        if "instigator_name" in storage:
            del storage["instigator_name"]
        # the stored key for the instigator name should always be `job_name`, for backcompat
        # and origin id stability (hash of the serialized tuple).  Make sure we fetch it from the
        # raw storage dict and pass it in as instigator_name to ExternalInstigatorOrigin
        storage["job_name"] = instigator_name
        # persist using legacy name
        storage["__class__"] = "ExternalJobOrigin"
        return storage


@whitelist_for_serdes(serializer=ExternalInstigatorOriginSerializer)
class ExternalInstigatorOrigin(
    NamedTuple(
        "_ExternalInstigatorOrigin",
        [("external_repository_origin", ExternalRepositoryOrigin), ("instigator_name", str)],
    )
):
    """Serializable representation of an ExternalJob that can be used to
    uniquely it or reload it in across process boundaries.
    """

    def __new__(cls, external_repository_origin: ExternalRepositoryOrigin, instigator_name: str):
        return super(ExternalInstigatorOrigin, cls).__new__(
            cls,
            check.inst_param(
                external_repository_origin,
                "external_repository_origin",
                ExternalRepositoryOrigin,
            ),
            check.str_param(instigator_name, "instigator_name"),
        )

    def get_id(self) -> str:
        return create_snapshot_id(self)


# ExternalInstigatorOrigin used to be called ExternalJobOrigin, before the concept of "job" was
# introduced in 0.12.0. For clarity, we changed the name of the namedtuple with `0.14.0`, but we
# need to maintain the serialized format in order to avoid changing the origin id that is stored in
# our schedule storage.  This registers the serialized ExternalJobOrigin named tuple class to be
# deserialized as an ExternalInstigatorOrigin, using its corresponding serializer for serdes.
register_serdes_tuple_fallbacks({"ExternalJobOrigin": ExternalInstigatorOrigin})


@whitelist_for_serdes
class ExternalPartitionSetOrigin(
    NamedTuple(
        "_PartitionSetOrigin",
        [("external_repository_origin", ExternalRepositoryOrigin), ("partition_set_name", str)],
    )
):
    """Serializable representation of an ExternalPartitionSet that can be used to
    uniquely it or reload it in across process boundaries.
    """

    def __new__(cls, external_repository_origin: ExternalRepositoryOrigin, partition_set_name: str):
        return super(ExternalPartitionSetOrigin, cls).__new__(
            cls,
            check.inst_param(
                external_repository_origin,
                "external_repository_origin",
                ExternalRepositoryOrigin,
            ),
            check.str_param(partition_set_name, "partition_set_name"),
        )

    def get_id(self) -> str:
        return create_snapshot_id(self)
