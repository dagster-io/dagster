import sys
import threading
import time
import warnings
from abc import ABC, abstractmethod
from contextlib import ExitStack
from itertools import count
from typing import TYPE_CHECKING, Any, Dict, Mapping, Optional, Sequence, Set, TypeVar, Union

from typing_extensions import Self

import dagster._check as check
from dagster._core.definitions.selector import JobSubsetSelector
from dagster._core.errors import (
    DagsterCodeLocationLoadError,
    DagsterCodeLocationNotFoundError,
)
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.host_representation import (
    CodeLocation,
    CodeLocationOrigin,
    ExternalExecutionPlan,
    ExternalJob,
    ExternalPartitionSet,
    GrpcServerCodeLocation,
    RepositoryHandle,
)
from dagster._core.host_representation.grpc_server_registry import (
    GrpcServerRegistry,
)
from dagster._core.host_representation.grpc_server_state_subscriber import (
    LocationStateChangeEvent,
    LocationStateChangeEventType,
    LocationStateSubscriber,
)
from dagster._core.host_representation.origin import GrpcServerCodeLocationOrigin
from dagster._core.instance import DagsterInstance
from dagster._utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info

from .load_target import WorkspaceLoadTarget
from .permissions import (
    PermissionResult,
    get_location_scoped_user_permissions,
    get_user_permissions,
)
from .workspace import (
    CodeLocationEntry,
    CodeLocationLoadStatus,
    CodeLocationStatusEntry,
    IWorkspace,
    location_status_from_location_entry,
)

if TYPE_CHECKING:
    from dagster._core.host_representation import (
        ExternalPartitionConfigData,
        ExternalPartitionExecutionErrorData,
        ExternalPartitionNamesData,
        ExternalPartitionSetExecutionParamData,
        ExternalPartitionTagsData,
    )

T = TypeVar("T")

DAGIT_GRPC_SERVER_HEARTBEAT_TTL = 45


class BaseWorkspaceRequestContext(IWorkspace):
    """This class is a request-scoped object that stores (1) a reference to all repository locations
    that exist on the `IWorkspaceProcessContext` at the start of the request and (2) a snapshot of the
    workspace at the start of the request.

    This object is needed because a process context and the repository locations on that context can
    be updated (for example, from a thread on the process context). If a request is accessing a
    repository location at the same time the repository location was being cleaned up, we would run
    into errors.
    """

    @property
    @abstractmethod
    def instance(self) -> DagsterInstance:
        pass

    @abstractmethod
    def get_workspace_snapshot(self) -> Mapping[str, CodeLocationEntry]:
        pass

    @abstractmethod
    def get_location_entry(self, name: str) -> Optional[CodeLocationEntry]:
        pass

    @abstractmethod
    def get_code_location_statuses(self) -> Sequence[CodeLocationStatusEntry]:
        pass

    @property
    @abstractmethod
    def process_context(self) -> "IWorkspaceProcessContext":
        pass

    @property
    @abstractmethod
    def version(self) -> Optional[str]:
        pass

    @property
    @abstractmethod
    def permissions(self) -> Mapping[str, PermissionResult]:
        pass

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
    def has_permission(self, permission: str) -> bool:
        pass

    @abstractmethod
    def was_permission_checked(self, permission: str) -> bool:
        pass

    @property
    def show_instance_config(self) -> bool:
        return True

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
            for entry in self.get_workspace_snapshot().values()
            if entry.code_location
        ]

    @property
    def code_location_names(self) -> Sequence[str]:
        return list(self.get_workspace_snapshot())

    def code_location_errors(self) -> Sequence[SerializableErrorInfo]:
        return [
            entry.load_error for entry in self.get_workspace_snapshot().values() if entry.load_error
        ]

    def has_code_location_error(self, name: str) -> bool:
        return self.get_code_location_error(name) is not None

    def get_code_location_error(self, name: str) -> Optional[SerializableErrorInfo]:
        entry = self.get_location_entry(name)
        return entry.load_error if entry else None

    def has_code_location_name(self, name: str) -> bool:
        return bool(self.get_location_entry(name))

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
        # This method reloads the location on the process context, and returns a new
        # request context created from the updated process context
        self.process_context.reload_code_location(name)
        return self.process_context.create_request_context()

    def shutdown_code_location(self, name: str):
        self.process_context.shutdown_code_location(name)

    def reload_workspace(self) -> Self:
        self.process_context.reload_workspace()
        return self.process_context.create_request_context()

    def has_external_job(self, selector: JobSubsetSelector) -> bool:
        check.inst_param(selector, "selector", JobSubsetSelector)
        if not self.has_code_location(selector.location_name):
            return False

        loc = self.get_code_location(selector.location_name)
        return loc.has_repository(selector.repository_name) and loc.get_repository(
            selector.repository_name
        ).has_external_job(selector.job_name)

    def get_full_external_job(self, selector: JobSubsetSelector) -> ExternalJob:
        return (
            self.get_code_location(selector.location_name)
            .get_repository(selector.repository_name)
            .get_full_external_job(selector.job_name)
        )

    def get_external_execution_plan(
        self,
        external_job: ExternalJob,
        run_config: Mapping[str, object],
        step_keys_to_execute: Optional[Sequence[str]],
        known_state: Optional[KnownExecutionState],
    ) -> ExternalExecutionPlan:
        return self.get_code_location(
            external_job.handle.location_name
        ).get_external_execution_plan(
            external_job=external_job,
            run_config=run_config,
            step_keys_to_execute=step_keys_to_execute,
            known_state=known_state,
            instance=self.instance,
        )

    def get_external_partition_config(
        self,
        repository_handle: RepositoryHandle,
        partition_set_name: str,
        partition_name: str,
        instance: DagsterInstance,
    ) -> Union["ExternalPartitionConfigData", "ExternalPartitionExecutionErrorData"]:
        return self.get_code_location(
            repository_handle.location_name
        ).get_external_partition_config(
            repository_handle=repository_handle,
            partition_set_name=partition_set_name,
            partition_name=partition_name,
            instance=instance,
        )

    def get_external_partition_tags(
        self,
        repository_handle: RepositoryHandle,
        partition_set_name: str,
        partition_name: str,
        instance: DagsterInstance,
    ) -> Union["ExternalPartitionTagsData", "ExternalPartitionExecutionErrorData"]:
        return self.get_code_location(repository_handle.location_name).get_external_partition_tags(
            repository_handle=repository_handle,
            partition_set_name=partition_set_name,
            partition_name=partition_name,
            instance=instance,
        )

    def get_external_partition_names(
        self, external_partition_set: ExternalPartitionSet, instance: DagsterInstance
    ) -> Union["ExternalPartitionNamesData", "ExternalPartitionExecutionErrorData"]:
        return self.get_code_location(
            external_partition_set.repository_handle.location_name
        ).get_external_partition_names(external_partition_set, instance=instance)

    def get_external_partition_set_execution_param_data(
        self,
        repository_handle: RepositoryHandle,
        partition_set_name: str,
        partition_names: Sequence[str],
        instance: DagsterInstance,
    ) -> Union["ExternalPartitionSetExecutionParamData", "ExternalPartitionExecutionErrorData"]:
        return self.get_code_location(
            repository_handle.location_name
        ).get_external_partition_set_execution_param_data(
            repository_handle=repository_handle,
            partition_set_name=partition_set_name,
            partition_names=partition_names,
            instance=instance,
        )

    def get_external_notebook_data(self, code_location_name: str, notebook_path: str) -> bytes:
        check.str_param(code_location_name, "code_location_name")
        check.str_param(notebook_path, "notebook_path")
        code_location = self.get_code_location(code_location_name)
        return code_location.get_external_notebook_data(notebook_path=notebook_path)


class WorkspaceRequestContext(BaseWorkspaceRequestContext):
    def __init__(
        self,
        instance: DagsterInstance,
        workspace_snapshot: Mapping[str, CodeLocationEntry],
        process_context: "IWorkspaceProcessContext",
        version: Optional[str],
        source: Optional[object],
        read_only: bool,
    ):
        self._instance = instance
        self._workspace_snapshot = workspace_snapshot
        self._process_context = process_context
        self._version = version
        self._source = source
        self._read_only = read_only
        self._checked_permissions: Set[str] = set()

    @property
    def instance(self) -> DagsterInstance:
        return self._instance

    def get_workspace_snapshot(self) -> Mapping[str, CodeLocationEntry]:
        return self._workspace_snapshot

    def get_location_entry(self, name: str) -> Optional[CodeLocationEntry]:
        return self._workspace_snapshot.get(name)

    def get_code_location_statuses(self) -> Sequence[CodeLocationStatusEntry]:
        return [
            location_status_from_location_entry(entry)
            for entry in self._workspace_snapshot.values()
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
        return get_location_scoped_user_permissions(self._read_only)

    def has_permission(self, permission: str) -> bool:
        permissions = self.permissions
        check.invariant(
            permission in permissions, f"Permission {permission} not listed in permissions map"
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
        For example in Dagit this object represents the web request.
        """
        return self._source


class IWorkspaceProcessContext(ABC):
    """Class that stores process-scoped information about a dagit session.
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
        pass

    @property
    @abstractmethod
    def instance(self) -> DagsterInstance:
        pass

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exception_type, exception_value, traceback):
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

        # Guards changes to _location_dict, _location_error_dict, and _location_origin_dict
        self._lock = threading.Lock()

        # Only ever set up by main thread
        self._watch_thread_shutdown_events: Dict[str, threading.Event] = {}
        self._watch_threads: Dict[str, threading.Thread] = {}

        self._state_subscriber_id_iter = count()
        self._state_subscribers: Dict[int, LocationStateSubscriber] = {}
        self.add_state_subscriber(LocationStateSubscriber(self._location_state_events_handler))

        if grpc_server_registry:
            self._grpc_server_registry: GrpcServerRegistry = check.inst_param(
                grpc_server_registry, "grpc_server_registry", GrpcServerRegistry
            )
        else:
            self._grpc_server_registry = self._stack.enter_context(
                GrpcServerRegistry(
                    instance=self._instance,
                    reload_interval=0,
                    heartbeat_ttl=DAGIT_GRPC_SERVER_HEARTBEAT_TTL,
                    startup_timeout=instance.code_server_process_startup_timeout,
                    log_level=code_server_log_level,
                )
            )

        self._location_entry_dict: Dict[str, CodeLocationEntry] = {}
        self._update_workspace(
            {origin.location_name: self._load_location(origin) for origin in self._origins}
        )

    @property
    def workspace_load_target(self) -> Optional[WorkspaceLoadTarget]:
        return self._workspace_load_target

    @property
    def _origins(self) -> Sequence[CodeLocationOrigin]:
        return self._workspace_load_target.create_origins() if self._workspace_load_target else []

    def add_state_subscriber(self, subscriber: LocationStateSubscriber) -> int:
        token = next(self._state_subscriber_id_iter)
        self._state_subscribers[token] = subscriber
        return token

    def rm_state_subscriber(self, token: int) -> None:
        if token in self._state_subscribers:
            del self._state_subscribers[token]

    def _create_location_from_origin(self, origin: CodeLocationOrigin) -> Optional[CodeLocation]:
        if not self._grpc_server_registry.supports_origin(origin):
            return origin.create_location()
        else:
            endpoint = (
                self._grpc_server_registry.reload_grpc_endpoint(origin)
                if self._grpc_server_registry.supports_reload
                else self._grpc_server_registry.get_grpc_endpoint(origin)
            )

            return GrpcServerCodeLocation(
                origin=origin,
                server_id=endpoint.server_id,
                port=endpoint.port,
                socket=endpoint.socket,
                host=endpoint.host,
                heartbeat=True,
                watch_server=False,
                grpc_server_registry=self._grpc_server_registry,
            )

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

    def _load_location(self, origin: CodeLocationOrigin) -> CodeLocationEntry:
        location_name = origin.location_name
        location = None
        error = None
        try:
            location = self._create_location_from_origin(origin)
        except Exception:
            error = serializable_error_info_from_exc_info(sys.exc_info())
            warnings.warn(
                "Error loading repository location {location_name}:{error_string}".format(
                    location_name=location_name, error_string=error.to_string()
                )
            )

        return CodeLocationEntry(
            origin=origin,
            code_location=location,
            load_error=error,
            load_status=CodeLocationLoadStatus.LOADED,
            display_metadata=location.get_display_metadata()
            if location
            else origin.get_display_metadata(),
            update_timestamp=time.time(),
        )

    def create_snapshot(self) -> Mapping[str, CodeLocationEntry]:
        with self._lock:
            return self._location_entry_dict.copy()

    @property
    def code_locations_count(self) -> int:
        with self._lock:
            return len(self._location_entry_dict)

    @property
    def code_location_names(self) -> Sequence[str]:
        with self._lock:
            return list(self._location_entry_dict)

    def has_code_location(self, location_name: str) -> bool:
        check.str_param(location_name, "location_name")

        with self._lock:
            return (
                location_name in self._location_entry_dict
                and self._location_entry_dict[location_name].code_location is not None
            )

    def has_code_location_error(self, location_name: str) -> bool:
        check.str_param(location_name, "location_name")
        with self._lock:
            return (
                location_name in self._location_entry_dict
                and self._location_entry_dict[location_name].load_error is not None
            )

    def reload_code_location(self, name: str) -> None:
        # Can be called from a background thread
        new = self._load_location(self._location_entry_dict[name].origin)
        with self._lock:
            # Relying on GC to clean up the old location once nothing else
            # is referencing it
            self._location_entry_dict[name] = new

    def shutdown_code_location(self, name: str) -> None:
        with self._lock:
            self._location_entry_dict[name].origin.shutdown_server()

    def reload_workspace(self) -> None:
        updated_locations = {
            origin.location_name: self._load_location(origin) for origin in self._origins
        }
        self._update_workspace(updated_locations)

    def _update_workspace(self, new_locations: Dict[str, CodeLocationEntry]):
        # minimize lock time by only holding while swapping data old to new
        with self._lock:
            previous_events = self._watch_thread_shutdown_events
            self._watch_thread_shutdown_events = {}

            previous_threads = self._watch_threads
            self._watch_threads = {}

            previous_locations = self._location_entry_dict
            self._location_entry_dict = new_locations

            # start monitoring for new locations
            for entry in self._location_entry_dict.values():
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
            workspace_snapshot=self.create_snapshot(),
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
            self.reload_code_location(event.location_name)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
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
