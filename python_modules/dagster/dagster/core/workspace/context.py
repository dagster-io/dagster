import sys
import threading
import time
import warnings
from abc import ABC, abstractmethod
from collections import OrderedDict
from contextlib import ExitStack
from typing import TYPE_CHECKING, Dict, List, Optional, Union, cast

import dagster._check as check
from dagster.core.errors import (
    DagsterRepositoryLocationLoadError,
    DagsterRepositoryLocationNotFoundError,
)
from dagster.core.execution.plan.state import KnownExecutionState
from dagster.core.host_representation import (
    ExternalExecutionPlan,
    ExternalPipeline,
    GrpcServerRepositoryLocation,
    PipelineSelector,
    RepositoryHandle,
    RepositoryLocation,
    RepositoryLocationOrigin,
)
from dagster.core.host_representation.grpc_server_registry import (
    GrpcServerRegistry,
    ProcessGrpcServerRegistry,
)
from dagster.core.host_representation.grpc_server_state_subscriber import (
    LocationStateChangeEvent,
    LocationStateChangeEventType,
    LocationStateSubscriber,
)
from dagster.core.host_representation.origin import GrpcServerRepositoryLocationOrigin
from dagster.core.instance import DagsterInstance
from dagster.grpc.server_watcher import create_grpc_watch_thread
from dagster.utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info

from .load_target import WorkspaceLoadTarget
from .permissions import get_user_permissions
from .workspace import IWorkspace, WorkspaceLocationEntry, WorkspaceLocationLoadStatus

if TYPE_CHECKING:
    from rx.subjects import Subject

    from dagster.core.host_representation import (
        ExternalPartitionConfigData,
        ExternalPartitionExecutionErrorData,
        ExternalPartitionNamesData,
        ExternalPartitionSetExecutionParamData,
        ExternalPartitionTagsData,
    )


DAGIT_GRPC_SERVER_HEARTBEAT_TTL = 45


class BaseWorkspaceRequestContext(IWorkspace):
    """
    This class is a request-scoped object that stores (1) a reference to all repository locations
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
    def get_workspace_snapshot(self) -> Dict[str, WorkspaceLocationEntry]:
        pass

    @abstractmethod
    def get_location_entry(self, name: str) -> Optional[WorkspaceLocationEntry]:
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
    def permissions(self) -> Dict[str, bool]:
        pass

    @abstractmethod
    def has_permission(self, permission: str) -> bool:
        pass

    @property
    def show_instance_config(self) -> bool:
        return True

    def get_repository_location(self, location_name: str) -> RepositoryLocation:
        location_entry = self.get_location_entry(location_name)
        if not location_entry:
            raise DagsterRepositoryLocationNotFoundError(
                f"Location {location_name} does not exist in workspace"
            )

        if location_entry.repository_location:
            return location_entry.repository_location

        error_info = cast(SerializableErrorInfo, location_entry.load_error)
        raise DagsterRepositoryLocationLoadError(
            f"Failure loading {location_name}: {error_info.to_string()}",
            load_error_infos=[error_info],
        )

    @property
    def repository_locations(self) -> List[RepositoryLocation]:
        return [
            entry.repository_location
            for entry in self.get_workspace_snapshot().values()
            if entry.repository_location
        ]

    @property
    def repository_location_names(self) -> List[str]:
        return list(self.get_workspace_snapshot())

    def repository_location_errors(self) -> List[SerializableErrorInfo]:
        return [
            entry.load_error for entry in self.get_workspace_snapshot().values() if entry.load_error
        ]

    def has_repository_location_error(self, name: str) -> bool:
        return self.get_repository_location_error(name) != None

    def get_repository_location_error(self, name: str) -> Optional[SerializableErrorInfo]:
        entry = self.get_location_entry(name)
        return entry.load_error if entry else None

    def has_repository_location_name(self, name: str) -> bool:
        return bool(self.get_location_entry(name))

    def has_repository_location(self, name: str) -> bool:
        location_entry = self.get_location_entry(name)
        return bool(location_entry and location_entry.repository_location != None)

    def is_reload_supported(self, name: str) -> bool:
        entry = self.get_location_entry(name)
        return entry.origin.is_reload_supported if entry else False

    def is_shutdown_supported(self, name: str) -> bool:
        entry = self.get_location_entry(name)
        return entry.origin.is_shutdown_supported if entry else False

    def reload_repository_location(self, name: str) -> "BaseWorkspaceRequestContext":
        # This method reloads the location on the process context, and returns a new
        # request context created from the updated process context
        self.process_context.reload_repository_location(name)
        return self.process_context.create_request_context()

    def shutdown_repository_location(self, name: str):
        self.process_context.shutdown_repository_location(name)

    def reload_workspace(self) -> "BaseWorkspaceRequestContext":
        self.process_context.reload_workspace()
        return self.process_context.create_request_context()

    def has_external_pipeline(self, selector: PipelineSelector) -> bool:
        check.inst_param(selector, "selector", PipelineSelector)
        loc = self.get_repository_location(selector.location_name)
        return (
            loc is not None
            and loc.has_repository(selector.repository_name)
            and loc.get_repository(selector.repository_name).has_external_pipeline(
                selector.pipeline_name
            )
        )

    def get_full_external_pipeline(self, selector: PipelineSelector) -> ExternalPipeline:
        return (
            self.get_repository_location(selector.location_name)
            .get_repository(selector.repository_name)
            .get_full_external_pipeline(selector.pipeline_name)
        )

    def get_external_execution_plan(
        self,
        external_pipeline: ExternalPipeline,
        run_config: dict,
        mode: str,
        step_keys_to_execute: List[str],
        known_state: KnownExecutionState,
    ) -> ExternalExecutionPlan:
        return self.get_repository_location(
            external_pipeline.handle.location_name
        ).get_external_execution_plan(
            external_pipeline=external_pipeline,
            run_config=run_config,
            mode=mode,
            step_keys_to_execute=step_keys_to_execute,
            known_state=known_state,
            instance=self.instance,
        )

    def get_external_partition_config(
        self, repository_handle: RepositoryHandle, partition_set_name: str, partition_name: str
    ) -> Union["ExternalPartitionConfigData", "ExternalPartitionExecutionErrorData"]:
        return self.get_repository_location(
            repository_handle.location_name
        ).get_external_partition_config(
            repository_handle=repository_handle,
            partition_set_name=partition_set_name,
            partition_name=partition_name,
        )

    def get_external_partition_tags(
        self, repository_handle: RepositoryHandle, partition_set_name: str, partition_name: str
    ) -> Union["ExternalPartitionTagsData", "ExternalPartitionExecutionErrorData"]:
        return self.get_repository_location(
            repository_handle.location_name
        ).get_external_partition_tags(
            repository_handle=repository_handle,
            partition_set_name=partition_set_name,
            partition_name=partition_name,
        )

    def get_external_partition_names(
        self, repository_handle: RepositoryHandle, partition_set_name: str
    ) -> Union["ExternalPartitionNamesData", "ExternalPartitionExecutionErrorData"]:
        return self.get_repository_location(
            repository_handle.location_name
        ).get_external_partition_names(repository_handle, partition_set_name)

    def get_external_partition_set_execution_param_data(
        self,
        repository_handle: RepositoryHandle,
        partition_set_name: str,
        partition_names: List[str],
    ) -> Union["ExternalPartitionSetExecutionParamData", "ExternalPartitionExecutionErrorData"]:
        return self.get_repository_location(
            repository_handle.location_name
        ).get_external_partition_set_execution_param_data(
            repository_handle=repository_handle,
            partition_set_name=partition_set_name,
            partition_names=partition_names,
        )

    def get_external_notebook_data(self, repository_location_name, notebook_path: str):
        check.str_param(repository_location_name, "repository_location_name")
        check.str_param(notebook_path, "notebook_path")
        repository_location = self.get_repository_location(repository_location_name)
        return repository_location.get_external_notebook_data(notebook_path=notebook_path)


class WorkspaceRequestContext(BaseWorkspaceRequestContext):
    def __init__(
        self,
        instance: DagsterInstance,
        workspace_snapshot: Dict[str, WorkspaceLocationEntry],
        process_context: "WorkspaceProcessContext",
        version: Optional[str],
        source: Optional[object],
    ):
        self._instance = instance
        self._workspace_snapshot = workspace_snapshot
        self._process_context = process_context
        self._version = version
        self._source = source

    @property
    def instance(self) -> DagsterInstance:
        return self._instance

    def get_workspace_snapshot(self) -> Dict[str, WorkspaceLocationEntry]:
        return self._workspace_snapshot

    def get_location_entry(self, name) -> Optional[WorkspaceLocationEntry]:
        return self._workspace_snapshot.get(name)

    @property
    def process_context(self) -> "IWorkspaceProcessContext":
        return self._process_context

    @property
    def version(self) -> Optional[str]:
        return self._version

    @property
    def read_only(self) -> bool:
        return self._process_context.read_only

    @property
    def permissions(self) -> Dict[str, bool]:
        return self._process_context.permissions

    def has_permission(self, permission: str) -> bool:
        permissions = self._process_context.permissions
        check.invariant(
            permission in permissions, f"Permission {permission} not listed in permissions map"
        )
        return permissions[permission]

    @property
    def source(self) -> Optional[object]:
        """
        The source of the request this WorkspaceRequestContext originated from.
        For example in Dagit this object represents the web request.
        """

        return self._source


class IWorkspaceProcessContext(ABC):
    """
    Class that stores process-scoped information about a dagit session.
    In most cases, you will want to create an `BaseWorkspaceRequestContext` to create a request-scoped
    object.
    """

    @abstractmethod
    def create_request_context(self, source=None) -> BaseWorkspaceRequestContext:
        """
        Create a usable fixed context for the scope of a request.

        Args:
            source (Optional[Any]):
                The source of the request, such as an object representing the web request
                or http connection.
        """

    @property
    @abstractmethod
    def version(self) -> str:
        pass

    @property
    @abstractmethod
    def location_state_events(self) -> "Subject":
        pass

    @abstractmethod
    def reload_repository_location(self, name: str) -> None:
        pass

    def shutdown_repository_location(self, name: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def reload_workspace(self) -> None:
        pass

    @property
    @abstractmethod
    def instance(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        pass


class WorkspaceProcessContext(IWorkspaceProcessContext):
    """
    This class is a process-scoped object that:

    1. Maintain an update-to-date dictionary of repository locations
    1. Create a `WorkspaceRequestContext` to be the workspace for each request
    2. Run watch thread processes that monitor repository locations

    To access a RepositoryLocation, you should create a `WorkspaceRequestContext`
    using `create_request_context`.
    """

    def __init__(
        self,
        instance: DagsterInstance,
        workspace_load_target: Optional[WorkspaceLoadTarget],
        version: str = "",
        read_only: bool = False,
        grpc_server_registry=None,
    ):
        self._stack = ExitStack()

        check.opt_str_param(version, "version")
        check.bool_param(read_only, "read_only")

        # lazy import for perf
        from rx.subjects import Subject

        self._instance = check.inst_param(instance, "instance", DagsterInstance)
        self._workspace_load_target = check.opt_inst_param(
            workspace_load_target, "workspace_load_target", WorkspaceLoadTarget
        )

        self._location_state_events = Subject()
        self._location_state_subscriber = LocationStateSubscriber(
            self._location_state_events_handler
        )

        self._read_only = read_only

        self._version = version

        # Guards changes to _location_dict, _location_error_dict, and _location_origin_dict
        self._lock = threading.Lock()

        # Only ever set up by main thread
        self._watch_thread_shutdown_events: Dict[str, threading.Event] = {}
        self._watch_threads: Dict[str, threading.Thread] = {}

        self._state_subscribers: List[LocationStateSubscriber] = []
        self.add_state_subscriber(self._location_state_subscriber)

        if grpc_server_registry:
            self._grpc_server_registry: GrpcServerRegistry = check.inst_param(
                grpc_server_registry, "grpc_server_registry", GrpcServerRegistry
            )
        else:
            self._grpc_server_registry = self._stack.enter_context(
                ProcessGrpcServerRegistry(
                    reload_interval=0,
                    heartbeat_ttl=DAGIT_GRPC_SERVER_HEARTBEAT_TTL,
                    startup_timeout=instance.code_server_process_startup_timeout,
                )
            )

        self._location_entry_dict: Dict[str, WorkspaceLocationEntry] = OrderedDict()

        with self._lock:
            self._load_workspace()

    @property
    def workspace_load_target(self):
        return self._workspace_load_target

    def add_state_subscriber(self, subscriber):
        self._state_subscribers.append(subscriber)

    def _load_workspace(self):
        assert self._lock.locked()
        repository_location_origins = (
            self._workspace_load_target.create_origins() if self._workspace_load_target else []
        )

        check.list_param(
            repository_location_origins,
            "repository_location_origins",
            of_type=RepositoryLocationOrigin,
        )

        self._location_entry_dict = OrderedDict()

        for origin in repository_location_origins:
            check.invariant(
                self._location_entry_dict.get(origin.location_name) is None,
                'Cannot have multiple locations with the same name, got multiple "{name}"'.format(
                    name=origin.location_name,
                ),
            )

            if origin.supports_server_watch:
                self._start_watch_thread(origin)
            self._location_entry_dict[origin.location_name] = self._load_location(origin)

    def _create_location_from_origin(
        self, origin: RepositoryLocationOrigin
    ) -> Optional[RepositoryLocation]:
        if not self._grpc_server_registry.supports_origin(origin):
            return origin.create_location()
        else:
            endpoint = (
                self._grpc_server_registry.reload_grpc_endpoint(origin)
                if self._grpc_server_registry.supports_reload
                else self._grpc_server_registry.get_grpc_endpoint(origin)
            )

            return GrpcServerRepositoryLocation(
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
    def instance(self):
        return self._instance

    @property
    def read_only(self):
        return self._read_only

    @property
    def permissions(self) -> Dict[str, bool]:
        return get_user_permissions(self)

    @property
    def version(self) -> str:
        return self._version

    def _send_state_event_to_subscribers(self, event: LocationStateChangeEvent) -> None:
        check.inst_param(event, "event", LocationStateChangeEvent)
        for subscriber in self._state_subscribers:
            subscriber.handle_event(event)

    def _start_watch_thread(self, origin: GrpcServerRepositoryLocationOrigin) -> None:
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
                    message="Unable to reconnect to server. You can reload the server once it is "
                    "reachable again",
                )
            ),
        )
        self._watch_thread_shutdown_events[location_name] = shutdown_event
        self._watch_threads[location_name] = watch_thread
        watch_thread.start()

    def _load_location(self, origin):
        assert self._lock.locked()
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

        return WorkspaceLocationEntry(
            origin=origin,
            repository_location=location,
            load_error=error,
            load_status=WorkspaceLocationLoadStatus.LOADED,
            display_metadata=location.get_display_metadata()
            if location
            else origin.get_display_metadata(),
            update_timestamp=time.time(),
        )

    def create_snapshot(self):
        with self._lock:
            return self._location_entry_dict.copy()

    @property
    def repository_locations_count(self):
        with self._lock:
            return len(self._location_entry_dict)

    @property
    def repository_location_names(self):
        with self._lock:
            return list(self._location_entry_dict)

    def has_repository_location(self, location_name):
        check.str_param(location_name, "location_name")

        with self._lock:
            return (
                location_name in self._location_entry_dict
                and self._location_entry_dict[location_name].repository_location
            )

    def has_repository_location_error(self, location_name):
        check.str_param(location_name, "location_name")
        with self._lock:
            return (
                location_name in self._location_entry_dict
                and self._location_entry_dict[location_name].load_error
            )

    def reload_repository_location(self, name: str) -> None:
        # Can be called from a background thread
        with self._lock:
            # Relying on GC to clean up the old location once nothing else
            # is referencing it
            self._location_entry_dict[name] = self._load_location(
                self._location_entry_dict[name].origin
            )

    def shutdown_repository_location(self, name: str):
        with self._lock:
            self._location_entry_dict[name].origin.shutdown_server()

    def reload_workspace(self):
        # Can be called from a background thread
        with self._lock:
            self._cleanup_locations()
            self._load_workspace()

    def _cleanup_locations(self):
        assert self._lock.locked()
        for _, event in self._watch_thread_shutdown_events.items():
            event.set()
        for _, watch_thread in self._watch_threads.items():
            watch_thread.join()

        self._watch_thread_shutdown_events = {}
        self._watch_threads = {}

        for entry in self._location_entry_dict.values():
            if entry.repository_location:
                entry.repository_location.cleanup()

        self._location_entry_dict = OrderedDict()

    def create_request_context(self, source=None) -> WorkspaceRequestContext:
        return WorkspaceRequestContext(
            instance=self._instance,
            workspace_snapshot=self.create_snapshot(),
            process_context=self,
            version=self.version,
            source=source,
        )

    @property
    def location_state_events(self) -> "Subject":
        return self._location_state_events

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
            self.reload_repository_location(event.location_name)

        self._location_state_events.on_next(event)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        with self._lock:
            self._cleanup_locations()
        self._stack.close()
