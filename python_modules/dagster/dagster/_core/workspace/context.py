import logging
import os
import sys
import threading
import warnings
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from contextlib import ExitStack
from functools import cached_property
from itertools import count
from typing import TYPE_CHECKING, AbstractSet, Any, Optional, TypeVar, Union  # noqa: UP035

from typing_extensions import Self

import dagster._check as check
from dagster._config.snap import ConfigTypeSnap
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.assets.graph.remote_asset_graph import (
    RemoteAssetGraph,
    RemoteRepositoryAssetNode,
)
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.data_version import CachingStaleStatusResolver
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.definitions.selector import (
    JobSelector,
    JobSubsetSelector,
    RepositorySelector,
    ScheduleSelector,
    SensorSelector,
)
from dagster._core.errors import DagsterCodeLocationLoadError, DagsterCodeLocationNotFoundError
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.instance import DagsterInstance
from dagster._core.instance.types import CachingDynamicPartitionsLoader
from dagster._core.loader import LoadingContext
from dagster._core.remote_origin import (
    CodeLocationOrigin,
    GrpcServerCodeLocationOrigin,
    ManagedGrpcPythonEnvCodeLocationOrigin,
)
from dagster._core.remote_representation.code_location import CodeLocation, GrpcServerCodeLocation
from dagster._core.remote_representation.external import (
    RemoteExecutionPlan,
    RemoteJob,
    RemoteRepository,
    RemoteSchedule,
    RemoteSensor,
)
from dagster._core.remote_representation.grpc_server_registry import GrpcServerRegistry
from dagster._core.remote_representation.grpc_server_state_subscriber import (
    LocationStateChangeEvent,
    LocationStateChangeEventType,
    LocationStateSubscriber,
)
from dagster._core.remote_representation.handle import InstigatorHandle, RepositoryHandle
from dagster._core.snap.dagster_types import DagsterTypeSnap
from dagster._core.snap.mode import ResourceDefSnap
from dagster._core.snap.node import GraphDefSnap, OpDefSnap
from dagster._core.workspace.load_target import WorkspaceLoadTarget
from dagster._core.workspace.permissions import (
    PermissionResult,
    get_location_scoped_user_permissions,
    get_user_permissions,
)
from dagster._core.workspace.workspace import (
    CodeLocationEntry,
    CodeLocationLoadStatus,
    CodeLocationStatusEntry,
    CurrentWorkspace,
    location_status_from_location_entry,
)
from dagster._grpc.constants import INCREASE_TIMEOUT_DAGSTER_YAML_MSG, GrpcServerCommand
from dagster._time import get_current_timestamp
from dagster._utils.aiodataloader import DataLoader
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer
from dagster._utils.env import using_dagster_dev
from dagster._utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info

if TYPE_CHECKING:
    from dagster._core.definitions.assets.graph.remote_asset_graph import RemoteWorkspaceAssetGraph
    from dagster._core.remote_representation.external_data import (
        PartitionConfigSnap,
        PartitionExecutionErrorSnap,
        PartitionNamesSnap,
        PartitionSetExecutionParamSnap,
        PartitionTagsSnap,
    )

T = TypeVar("T")

WEBSERVER_GRPC_SERVER_HEARTBEAT_TTL = 45


class BaseWorkspaceRequestContext(LoadingContext):
    """This class is a request-scoped object that stores (1) a reference to all repository locations
    that exist on the `IWorkspaceProcessContext` at the start of the request and (2) a snapshot of the
    workspace at the start of the request.

    This object is needed because a process context and the repository locations on that context can
    be updated (for example, from a thread on the process context). If a request is accessing a
    repository location at the same time the repository location was being cleaned up, we would run
    into errors.
    """

    _exit_stack: ExitStack

    @property
    @abstractmethod
    def instance(self) -> DagsterInstance: ...

    @abstractmethod
    def get_current_workspace(self) -> CurrentWorkspace: ...

    # abstracted since they may be calculated without the full CurrentWorkspace
    def get_location_entry(self, name: str) -> Optional[CodeLocationEntry]: ...

    def get_code_location_statuses(self) -> Sequence[CodeLocationStatusEntry]: ...

    # implemented here since they require the full CurrentWorkspace
    def get_code_location_entries(self) -> Mapping[str, CodeLocationEntry]:
        return self.get_current_workspace().code_location_entries

    def __enter__(self) -> Self:
        self._exit_stack = ExitStack()
        self._exit_stack.enter_context(
            partition_loading_context(dynamic_partitions_store=self.dynamic_partitions_loader)
        )
        return self

    def __exit__(self, exception_type, exception_value, traceback) -> None:
        self._exit_stack.close()

    @property
    def asset_graph(self) -> "RemoteWorkspaceAssetGraph":
        return self.get_current_workspace().asset_graph

    @cached_property
    def instance_queryer(self) -> CachingInstanceQueryer:
        return CachingInstanceQueryer(
            instance=self.instance,
            asset_graph=self.asset_graph,
            loading_context=self,
        )

    @cached_property
    def dynamic_partitions_loader(self) -> CachingDynamicPartitionsLoader:
        return CachingDynamicPartitionsLoader(self.instance)

    @cached_property
    def stale_status_loader(self) -> CachingStaleStatusResolver:
        return CachingStaleStatusResolver(
            self.instance,
            asset_graph=lambda: self.asset_graph,
            loading_context=self,
        )

    @cached_property
    def data_time_resolver(self) -> CachingDataTimeResolver:
        return CachingDataTimeResolver(self.instance_queryer)

    @property
    @abstractmethod
    def process_context(self) -> "IWorkspaceProcessContext": ...

    @property
    @abstractmethod
    def version(self) -> Optional[str]: ...

    @property
    @abstractmethod
    def permissions(self) -> Mapping[str, PermissionResult]: ...

    @abstractmethod
    def permissions_for_location(self, *, location_name: str) -> Mapping[str, PermissionResult]:
        pass

    def has_permission_for_location(self, permission: str, location_name: str) -> bool:
        if self.has_code_location_name(location_name):
            permissions = self.permissions_for_location(location_name=location_name)
            return permissions[permission].enabled

        # if not in workspace, fall back to the global permissions across all code locations
        return self.has_permission(permission)

    @abstractmethod
    def has_permission(self, permission: str) -> bool: ...

    @abstractmethod
    def was_permission_checked(self, permission: str) -> bool: ...

    @property
    @abstractmethod
    def records_for_run_default_limit(self) -> Optional[int]: ...

    @property
    def show_instance_config(self) -> bool:
        return True

    def get_viewer_tags(self) -> dict[str, str]:
        return {}

    def get_reporting_user_tags(self) -> dict[str, str]:
        return {}

    def get_code_location(self, location_name: str) -> CodeLocation:
        location_entry = self.get_location_entry(location_name)
        if not location_entry:
            raise DagsterCodeLocationNotFoundError(
                f"Location {location_name} does not exist in workspace"
            )

        if location_entry.code_location:
            return location_entry.code_location

        if location_entry.load_error:
            error_info = location_entry.load_error
            raise DagsterCodeLocationLoadError(
                f"Failure loading {location_name}: {error_info.to_string()}",
                load_error_infos=[error_info],
            )

        raise DagsterCodeLocationNotFoundError(
            f"Location {location_name} is still loading",
        )

    @property
    def code_locations(self) -> Sequence[CodeLocation]:
        return [
            entry.code_location
            for entry in self.get_code_location_entries().values()
            if entry.code_location
        ]

    @property
    def code_location_names(self) -> Sequence[str]:
        # For some WorkspaceRequestContext subclasses, the CodeLocationEntry is more expensive
        # than the CodeLocationStatusEntry, so use the latter for a faster check.
        return [status_entry.location_name for status_entry in self.get_code_location_statuses()]

    def code_location_errors(self) -> Sequence[SerializableErrorInfo]:
        return [
            entry.load_error
            for entry in self.get_code_location_entries().values()
            if entry.load_error
        ]

    def has_code_location_error(self, name: str) -> bool:
        return self.get_code_location_error(name) is not None

    def get_code_location_error(self, name: str) -> Optional[SerializableErrorInfo]:
        entry = self.get_location_entry(name)
        return entry.load_error if entry else None

    def has_code_location_name(self, name: str) -> bool:
        # For some WorkspaceRequestContext subclasses, the CodeLocationEntry is more expensive
        # than the CodeLocationStatusEntry, so use the latter for a faster check.
        for status_entry in self.get_code_location_statuses():
            if status_entry.location_name == name:
                return True

        return False

    def has_code_location(self, name: str) -> bool:
        location_entry = self.get_location_entry(name)
        return bool(location_entry and location_entry.code_location is not None)

    def is_reload_supported(self, name: str) -> bool:
        entry = self.get_location_entry(name)
        return entry.origin.is_reload_supported if entry else False

    def is_shutdown_supported(self, name: str) -> bool:
        entry = self.get_location_entry(name)
        return entry.origin.is_shutdown_supported if entry else False

    def reload_code_location(self, name: str) -> "BaseWorkspaceRequestContext":
        # This method signals to the remote gRPC server that it should reload its
        # code, and returns a new request context created from the updated process context
        self.process_context.reload_code_location(name)
        return self.process_context.create_request_context()

    def shutdown_code_location(self, name: str):
        self.process_context.shutdown_code_location(name)

    def reload_workspace(self) -> "BaseWorkspaceRequestContext":
        self.process_context.reload_workspace()
        return self.process_context.create_request_context()

    def has_job(self, selector: Union[JobSubsetSelector, JobSelector]) -> bool:
        check.inst_param(selector, "selector", JobSubsetSelector)
        if not self.has_code_location(selector.location_name):
            return False

        loc = self.get_code_location(selector.location_name)
        return loc.has_repository(selector.repository_name) and loc.get_repository(
            selector.repository_name
        ).has_job(selector.job_name)

    def get_full_job(self, selector: Union[JobSubsetSelector, JobSelector]) -> RemoteJob:
        return (
            self.get_code_location(selector.location_name)
            .get_repository(selector.repository_name)
            .get_full_job(selector.job_name)
        )

    async def gen_job(
        self,
        selector: JobSubsetSelector,
    ) -> RemoteJob:
        return await self.get_code_location(selector.location_name).gen_job(selector)

    def get_execution_plan(
        self,
        remote_job: RemoteJob,
        run_config: Mapping[str, object],
        step_keys_to_execute: Optional[Sequence[str]],
        known_state: Optional[KnownExecutionState],
    ) -> RemoteExecutionPlan:
        return self.get_code_location(remote_job.handle.location_name).get_execution_plan(
            remote_job=remote_job,
            run_config=run_config,
            step_keys_to_execute=step_keys_to_execute,
            known_state=known_state,
            instance=self.instance,
        )

    async def gen_execution_plan(
        self,
        remote_job: RemoteJob,
        run_config: Mapping[str, object],
        step_keys_to_execute: Optional[Sequence[str]],
        known_state: Optional[KnownExecutionState],
    ) -> RemoteExecutionPlan:
        return await self.get_code_location(remote_job.handle.location_name).gen_execution_plan(
            remote_job=remote_job,
            run_config=run_config,
            step_keys_to_execute=step_keys_to_execute,
            known_state=known_state,
            instance=self.instance,
        )

    def get_partition_config(
        self,
        repository_handle: RepositoryHandle,
        job_name: str,
        partition_name: str,
        instance: DagsterInstance,
    ) -> Union["PartitionConfigSnap", "PartitionExecutionErrorSnap"]:
        return self.get_code_location(repository_handle.location_name).get_partition_config(
            repository_handle=repository_handle,
            job_name=job_name,
            partition_name=partition_name,
            instance=instance,
        )

    def get_partition_tags(
        self,
        repository_handle: RepositoryHandle,
        job_name: str,
        partition_name: str,
        instance: DagsterInstance,
        selected_asset_keys: Optional[AbstractSet[AssetKey]],
    ) -> Union["PartitionTagsSnap", "PartitionExecutionErrorSnap"]:
        return self.get_code_location(repository_handle.location_name).get_partition_tags(
            repository_handle=repository_handle,
            job_name=job_name,
            partition_name=partition_name,
            instance=instance,
            selected_asset_keys=selected_asset_keys,
        )

    def get_partition_names(
        self,
        repository_handle: RepositoryHandle,
        job_name: str,
        instance: DagsterInstance,
        selected_asset_keys: Optional[AbstractSet[AssetKey]],
    ) -> Union["PartitionNamesSnap", "PartitionExecutionErrorSnap"]:
        return self.get_code_location(repository_handle.location_name).get_partition_names(
            repository_handle=repository_handle,
            job_name=job_name,
            instance=instance,
            selected_asset_keys=selected_asset_keys,
        )

    def get_partition_set_execution_param_data(
        self,
        repository_handle: RepositoryHandle,
        partition_set_name: str,
        partition_names: Sequence[str],
        instance: DagsterInstance,
    ) -> Union["PartitionSetExecutionParamSnap", "PartitionExecutionErrorSnap"]:
        return self.get_code_location(
            repository_handle.location_name
        ).get_partition_set_execution_params(
            repository_handle=repository_handle,
            partition_set_name=partition_set_name,
            partition_names=partition_names,
            instance=instance,
        )

    def get_notebook_data(self, code_location_name: str, notebook_path: str) -> bytes:
        check.str_param(code_location_name, "code_location_name")
        check.str_param(notebook_path, "notebook_path")
        code_location = self.get_code_location(code_location_name)
        return code_location.get_notebook_data(notebook_path=notebook_path)

    def get_base_deployment_asset_graph(
        self, repository_selector: Optional["RepositorySelector"]
    ) -> Optional["RemoteAssetGraph"]:
        return None

    def get_repository(
        self, selector: Union[RepositorySelector, RepositoryHandle]
    ) -> RemoteRepository:
        return self.get_code_location(selector.location_name).get_repository(
            selector.repository_name
        )

    def get_sensor(
        self, selector: Union[InstigatorHandle, SensorSelector]
    ) -> Optional[RemoteSensor]:
        if not self.has_code_location(selector.location_name):
            return None

        location = self.get_code_location(selector.location_name)

        if not location.has_repository(selector.repository_name):
            return None

        repository = location.get_repository(selector.repository_name)
        if not repository.has_sensor(selector.instigator_name):
            return None

        return repository.get_sensor(selector.instigator_name)

    def get_schedule(
        self, selector: Union[InstigatorHandle, ScheduleSelector]
    ) -> Optional[RemoteSchedule]:
        if not self.has_code_location(selector.location_name):
            return None

        location = self.get_code_location(selector.location_name)

        if not location.has_repository(selector.repository_name):
            return None

        repository = location.get_repository(selector.repository_name)
        if not repository.has_schedule(selector.instigator_name):
            return None

        return repository.get_schedule(selector.instigator_name)

    def get_node_def(
        self,
        job_selector: Union[JobSubsetSelector, JobSelector],
        node_def_name: str,
    ) -> Union[OpDefSnap, GraphDefSnap]:
        job = self.get_full_job(job_selector)
        return job.get_node_def_snap(node_def_name)

    def get_config_type(
        self,
        job_selector: Union[JobSubsetSelector, JobSelector],
        type_key: str,
    ) -> ConfigTypeSnap:
        job = self.get_full_job(job_selector)
        return job.config_schema_snapshot.get_config_snap(type_key)

    def get_dagster_type(
        self,
        job_selector: Union[JobSubsetSelector, JobSelector],
        type_key: str,
    ) -> DagsterTypeSnap:
        job = self.get_full_job(job_selector)
        return job.job_snapshot.dagster_type_namespace_snapshot.get_dagster_type_snap(type_key)

    def get_resources(
        self,
        job_selector: Union[JobSubsetSelector, JobSelector],
    ) -> Sequence[ResourceDefSnap]:
        job = self.get_full_job(job_selector)
        if not job.mode_def_snaps:
            return []
        return job.mode_def_snaps[0].resource_def_snaps

    def get_dagster_library_versions(self, location_name: str) -> Optional[Mapping[str, str]]:
        return self.get_code_location(location_name).get_dagster_library_versions()

    def get_schedules_targeting_job(
        self,
        selector: Union[JobSubsetSelector, JobSelector],
    ) -> Sequence[RemoteSchedule]:
        repository = self.get_code_location(selector.location_name).get_repository(
            selector.repository_name
        )
        return repository.schedules_by_job_name.get(selector.job_name, [])

    def get_sensors_targeting_job(
        self,
        selector: Union[JobSubsetSelector, JobSelector],
    ) -> Sequence[RemoteSensor]:
        repository = self.get_code_location(selector.location_name).get_repository(
            selector.repository_name
        )
        return repository.sensors_by_job_name.get(selector.job_name, [])

    def get_assets_in_job(
        self,
        selector: Union[JobSubsetSelector, JobSelector],
    ) -> Sequence[RemoteRepositoryAssetNode]:
        if not self.has_code_location(selector.location_name):
            return []

        location = self.get_code_location(selector.location_name)
        if not location.has_repository(selector.repository_name):
            return []

        repository = location.get_repository(selector.repository_name)
        snaps = repository.get_asset_node_snaps(job_name=selector.job_name)

        # use repository scoped nodes to match existing behavior,
        # easily switched to workspace scope nodes by using self.asset_graph
        return [
            repository.asset_graph.get(snap.asset_key)
            for snap in snaps
            if repository.asset_graph.has(snap.asset_key)
        ]


class WorkspaceRequestContext(BaseWorkspaceRequestContext):
    def __init__(
        self,
        instance: DagsterInstance,
        current_workspace: CurrentWorkspace,
        process_context: "IWorkspaceProcessContext",
        version: Optional[str],
        source: Optional[object],
        read_only: bool,
        read_only_locations: Optional[Mapping[str, bool]] = None,
    ):
        self._instance = instance
        self._current_workspace = current_workspace
        self._process_context = process_context
        self._version = version
        self._source = source
        self._read_only = read_only
        self._read_only_locations = check.opt_mapping_param(
            read_only_locations, "read_only_locations"
        )
        self._checked_permissions: set[str] = set()
        self._loaders = {}

    def reset_for_test(self) -> "WorkspaceRequestContext":
        return WorkspaceRequestContext(
            instance=self.instance,
            current_workspace=self._current_workspace,
            process_context=self._process_context,
            version=self._version,
            source=self._source,
            read_only=self._read_only,
            read_only_locations=self._read_only_locations,
        )

    @property
    def instance(self) -> DagsterInstance:
        return self._instance

    def get_current_workspace(self) -> CurrentWorkspace:
        return self._current_workspace

    def get_location_entry(self, name: str) -> Optional[CodeLocationEntry]:
        return self._current_workspace.code_location_entries.get(name)

    def get_code_location_statuses(self) -> Sequence[CodeLocationStatusEntry]:
        return [
            location_status_from_location_entry(entry)
            for entry in self._current_workspace.code_location_entries.values()
        ]

    @property
    def process_context(self) -> "IWorkspaceProcessContext":
        return self._process_context

    @property
    def version(self) -> Optional[str]:
        return self._version

    @property
    def read_only(self) -> bool:
        return self._read_only

    @property
    def permissions(self) -> Mapping[str, PermissionResult]:
        return get_user_permissions(self._read_only)

    def permissions_for_location(self, *, location_name: str) -> Mapping[str, PermissionResult]:
        if location_name in self._read_only_locations:
            return get_location_scoped_user_permissions(self._read_only_locations[location_name])
        return get_location_scoped_user_permissions(self._read_only)

    def has_permission(self, permission: str) -> bool:
        permissions = self.permissions
        check.invariant(
            permission in permissions,
            f"Permission {permission} not listed in permissions map",
        )
        self._checked_permissions.add(permission)
        return permissions[permission].enabled

    def has_permission_for_location(self, permission: str, location_name: str) -> bool:
        self._checked_permissions.add(permission)
        return super().has_permission_for_location(permission, location_name)

    def was_permission_checked(self, permission: str) -> bool:
        return permission in self._checked_permissions

    @property
    def source(self) -> Optional[object]:
        """The source of the request this WorkspaceRequestContext originated from.
        For example in the webserver this object represents the web request.
        """
        return self._source

    @property
    def loaders(self) -> dict[type, DataLoader]:  # pyright: ignore[reportIncompatibleMethodOverride]
        return self._loaders

    @property
    def records_for_run_default_limit(self) -> Optional[int]:
        return int(os.getenv("DAGSTER_UI_EVENT_LOAD_CHUNK_SIZE", "1000"))


class IWorkspaceProcessContext(ABC):
    """Class that stores process-scoped information about a webserver session.
    In most cases, you will want to create a `BaseWorkspaceRequestContext` to create a request-scoped
    object.
    """

    @abstractmethod
    def create_request_context(self, source: Optional[Any] = None) -> BaseWorkspaceRequestContext:
        """Create a usable fixed context for the scope of a request.

        Args:
            source (Optional[Any]):
                The source of the request, such as an object representing the web request
                or http connection.
        """

    @property
    @abstractmethod
    def version(self) -> str:
        pass

    @abstractmethod
    def reload_code_location(self, name: str) -> None:
        pass

    def shutdown_code_location(self, name: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def reload_workspace(self) -> None:
        """Reload the code in each code location."""
        pass

    @abstractmethod
    def refresh_workspace(self) -> None:
        """Refresh the snapshots for each code location, without reloading the underlying code."""
        pass

    @property
    @abstractmethod
    def instance(self) -> DagsterInstance:
        pass

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exception_type, exception_value, traceback) -> None:
        pass


class WorkspaceProcessContext(IWorkspaceProcessContext):
    """Process-scoped object that tracks the state of a workspace.

    1. Maintains an update-to-date dictionary of repository locations
    2. Creates a `WorkspaceRequestContext` to be the workspace for each request
    3. Runs watch thread processes that monitor repository locations

    To access a CodeLocation, you should create a `WorkspaceRequestContext`
    using `create_request_context`.
    """

    def __init__(
        self,
        instance: DagsterInstance,
        workspace_load_target: Optional[WorkspaceLoadTarget],
        version: str = "",
        read_only: bool = False,
        grpc_server_registry: Optional[GrpcServerRegistry] = None,
        code_server_log_level: str = "INFO",
        server_command: GrpcServerCommand = GrpcServerCommand.API_GRPC,
    ):
        self._stack = ExitStack()

        check.opt_str_param(version, "version")
        check.bool_param(read_only, "read_only")

        self._instance = check.inst_param(instance, "instance", DagsterInstance)
        self._workspace_load_target = check.opt_inst_param(
            workspace_load_target, "workspace_load_target", WorkspaceLoadTarget
        )

        self._read_only = read_only

        self._version = version

        # Guards changes to _current_workspace, _watch_thread_shutdown_events and _watch_threads
        self._lock = threading.Lock()
        self._watch_thread_shutdown_events: dict[str, threading.Event] = {}
        self._watch_threads: dict[str, threading.Thread] = {}

        self._state_subscribers_lock = threading.Lock()
        self._state_subscriber_id_iter = count()
        self._state_subscribers: dict[int, LocationStateSubscriber] = {}
        self.add_state_subscriber(LocationStateSubscriber(self._location_state_events_handler))

        if grpc_server_registry:
            self._grpc_server_registry: GrpcServerRegistry = check.inst_param(
                grpc_server_registry, "grpc_server_registry", GrpcServerRegistry
            )
        else:
            self._grpc_server_registry = self._stack.enter_context(
                GrpcServerRegistry(
                    instance_ref=self._instance.get_ref(),
                    server_command=server_command,
                    heartbeat_ttl=WEBSERVER_GRPC_SERVER_HEARTBEAT_TTL,
                    startup_timeout=instance.code_server_process_startup_timeout,
                    log_level=code_server_log_level,
                    wait_for_processes_on_shutdown=instance.wait_for_local_code_server_processes_on_shutdown,
                    additional_timeout_msg=INCREASE_TIMEOUT_DAGSTER_YAML_MSG,
                )
            )

        self._current_workspace: CurrentWorkspace = CurrentWorkspace(code_location_entries={})
        self._update_workspace(
            {
                origin.location_name: self._load_location(origin, reload=False)
                for origin in self._origins
            }
        )

    @property
    def workspace_load_target(self) -> Optional[WorkspaceLoadTarget]:
        return self._workspace_load_target

    @property
    def _origins(self) -> Sequence[CodeLocationOrigin]:
        return self._workspace_load_target.create_origins() if self._workspace_load_target else []

    def get_code_server_specs(self) -> Sequence[Mapping[str, Mapping[str, Any]]]:
        result = []
        for origin in self._origins:
            if isinstance(origin, ManagedGrpcPythonEnvCodeLocationOrigin):
                grpc_endpoint = self._grpc_server_registry.get_grpc_endpoint(origin)
                server_spec = {
                    "location_name": origin.location_name,
                    "socket": grpc_endpoint.socket,
                    "port": grpc_endpoint.port,
                    "host": grpc_endpoint.host,
                    "additional_metadata": origin.loadable_target_origin.as_dict,
                }
            elif isinstance(origin, GrpcServerCodeLocationOrigin):
                server_spec = {
                    "location_name": origin.location_name,
                    "host": origin.host,
                    "port": origin.port,
                    "socket": origin.socket,
                    "additional_metadata": origin.additional_metadata,
                }
            else:
                check.failed(f"Unexpected origin type {origin}")
            result.append({"grpc_server": {k: v for k, v in server_spec.items() if v is not None}})
        return result

    def add_state_subscriber(self, subscriber: LocationStateSubscriber) -> int:
        token = next(self._state_subscriber_id_iter)
        with self._state_subscribers_lock:
            self._state_subscribers[token] = subscriber
        return token

    def rm_state_subscriber(self, token: int) -> None:
        with self._state_subscribers_lock:
            if token in self._state_subscribers:
                del self._state_subscribers[token]

    @property
    def instance(self) -> DagsterInstance:
        return self._instance

    @property
    def read_only(self) -> bool:
        return self._read_only

    @property
    def permissions(self) -> Mapping[str, PermissionResult]:
        return get_user_permissions(True)

    def permissions_for_location(self, *, location_name: str) -> Mapping[str, PermissionResult]:
        return get_location_scoped_user_permissions(True)

    @property
    def version(self) -> str:
        return self._version

    def _send_state_event_to_subscribers(self, event: LocationStateChangeEvent) -> None:
        check.inst_param(event, "event", LocationStateChangeEvent)
        with self._state_subscribers_lock:
            for subscriber in self._state_subscribers.values():
                subscriber.handle_event(event)

    def _start_watch_thread(self, origin: GrpcServerCodeLocationOrigin) -> None:
        from dagster._grpc.server_watcher import create_grpc_watch_thread

        location_name = origin.location_name
        check.invariant(location_name not in self._watch_thread_shutdown_events)
        client = origin.create_client()
        shutdown_event, watch_thread = create_grpc_watch_thread(
            location_name,
            client,
            on_updated=lambda location_name, new_server_id: self._send_state_event_to_subscribers(
                LocationStateChangeEvent(
                    LocationStateChangeEventType.LOCATION_UPDATED,
                    location_name=location_name,
                    message="Server has been updated.",
                    server_id=new_server_id,
                )
            ),
            on_error=lambda location_name: self._send_state_event_to_subscribers(
                LocationStateChangeEvent(
                    LocationStateChangeEventType.LOCATION_ERROR,
                    location_name=location_name,
                    message=(
                        "Unable to reconnect to server. You can reload the server once it is "
                        "reachable again"
                    ),
                )
            ),
        )
        self._watch_thread_shutdown_events[location_name] = shutdown_event
        self._watch_threads[location_name] = watch_thread
        watch_thread.start()

    def _load_location(self, origin: CodeLocationOrigin, reload: bool) -> CodeLocationEntry:
        location_name = origin.location_name
        location = None
        error = None
        try:
            if isinstance(origin, ManagedGrpcPythonEnvCodeLocationOrigin):
                endpoint = (
                    self._grpc_server_registry.reload_grpc_endpoint(origin)
                    if reload
                    else self._grpc_server_registry.get_grpc_endpoint(origin)
                )
                location = GrpcServerCodeLocation(
                    origin=origin,
                    port=endpoint.port,
                    socket=endpoint.socket,
                    host=endpoint.host,
                    heartbeat=True,
                    watch_server=False,
                    grpc_server_registry=self._grpc_server_registry,
                    instance=self._instance,
                )
            else:
                location = (
                    origin.reload_location(self.instance)
                    if reload
                    else origin.create_location(self.instance)
                )

        except Exception:
            error = serializable_error_info_from_exc_info(sys.exc_info())
            # In dagster dev, the code server process already logs the error, so we don't need to log it again from
            # the workspace process context
            if using_dagster_dev():
                warnings.warn(f"Error loading repository location {location_name}")
            else:
                warnings.warn(
                    f"Error loading repository location {location_name}:{error.to_string()}"
                )

        load_time = get_current_timestamp()
        if isinstance(location, GrpcServerCodeLocation):
            version_key = location.server_id
        else:
            version_key = str(load_time)

        return CodeLocationEntry(
            origin=origin,
            code_location=location,
            load_error=error,
            load_status=CodeLocationLoadStatus.LOADED,
            display_metadata=(
                location.get_display_metadata() if location else origin.get_display_metadata()
            ),
            update_timestamp=load_time,
            version_key=version_key,
        )

    def get_current_workspace(self) -> CurrentWorkspace:
        with self._lock:
            return self._current_workspace

    @property
    def code_locations_count(self) -> int:
        with self._lock:
            return len(self._current_workspace.code_location_entries)

    @property
    def code_location_names(self) -> Sequence[str]:
        with self._lock:
            return list(self._current_workspace.code_location_entries)

    def has_code_location(self, location_name: str) -> bool:
        check.str_param(location_name, "location_name")

        with self._lock:
            return (
                location_name in self._current_workspace.code_location_entries
                and self._current_workspace.code_location_entries[location_name].code_location
                is not None
            )

    def has_code_location_error(self, location_name: str) -> bool:
        check.str_param(location_name, "location_name")
        with self._lock:
            return (
                location_name in self._current_workspace.code_location_entries
                and self._current_workspace.code_location_entries[location_name].load_error
                is not None
            )

    def reload_code_location(self, name: str) -> None:
        new_entry = self._load_location(
            self._current_workspace.code_location_entries[name].origin, reload=True
        )
        with self._lock:
            # Relying on GC to clean up the old location once nothing else
            # is referencing it
            self._current_workspace = self._current_workspace.with_code_location(name, new_entry)

    def shutdown_code_location(self, name: str) -> None:
        with self._lock:
            self._current_workspace.code_location_entries[name].origin.shutdown_server()

    def refresh_workspace(self) -> None:
        updated_locations = {
            origin.location_name: self._load_location(origin, reload=False)
            for origin in self._origins
        }
        self._update_workspace(updated_locations)

    def reload_workspace(self) -> None:
        updated_locations = {
            origin.location_name: self._load_location(origin, reload=True)
            for origin in self._origins
        }
        self._update_workspace(updated_locations)

    def _update_workspace(self, new_locations: dict[str, CodeLocationEntry]):
        # minimize lock time by only holding while swapping data old to new
        with self._lock:
            previous_events = self._watch_thread_shutdown_events
            self._watch_thread_shutdown_events = {}

            previous_threads = self._watch_threads
            self._watch_threads = {}

            previous_locations = self._current_workspace.code_location_entries
            self._current_workspace = CurrentWorkspace(code_location_entries=new_locations)

            # start monitoring for new locations
            for entry in new_locations.values():
                if isinstance(entry.origin, GrpcServerCodeLocationOrigin):
                    self._start_watch_thread(entry.origin)

        # clean up previous locations
        for event in previous_events.values():
            event.set()

        for watch_thread in previous_threads.values():
            watch_thread.join()

        for entry in previous_locations.values():
            if entry.code_location:
                entry.code_location.cleanup()

    def create_request_context(self, source: Optional[object] = None) -> WorkspaceRequestContext:
        return WorkspaceRequestContext(
            instance=self._instance,
            current_workspace=self.get_current_workspace(),
            process_context=self,
            version=self.version,
            source=source,
            read_only=self._read_only,
        )

    def _location_state_events_handler(self, event: LocationStateChangeEvent) -> None:
        # If the server was updated or we were not able to reconnect, we immediately reload the
        # location handle
        if event.event_type in (
            LocationStateChangeEventType.LOCATION_UPDATED,
            LocationStateChangeEventType.LOCATION_ERROR,
        ):
            # In case of an updated location, reload the handle to get updated repository data and
            # re-attach a subscriber
            # In case of a location error, just reload the handle in order to update the workspace
            # with the correct error messages
            logging.getLogger("dagster-webserver").info(
                f"Received {event.event_type} event for location {event.location_name}, refreshing"
            )
            self.refresh_code_location(event.location_name)

    def refresh_code_location(self, name: str) -> None:
        # This method reloads the webserver's copy of the code from the remote gRPC server without
        # restarting it, and returns a new request context created from the updated process context
        new_entry = self._load_location(
            self._current_workspace.code_location_entries[name].origin, reload=False
        )
        with self._lock:
            # Relying on GC to clean up the old location once nothing else
            # is referencing it
            self._current_workspace = self._current_workspace.with_code_location(name, new_entry)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exception_type, exception_value, traceback) -> None:
        self._update_workspace({})  # update to empty to close all current locations
        self._stack.close()

    def copy_for_test_instance(self, instance: DagsterInstance) -> "WorkspaceProcessContext":
        """Make a copy with a different instance, created for tests."""
        return WorkspaceProcessContext(
            instance=instance,
            workspace_load_target=self.workspace_load_target,
            version=self.version,
            read_only=self.read_only,
            grpc_server_registry=self._grpc_server_registry,
        )
