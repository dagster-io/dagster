import sys
import threading
import time
import warnings
from abc import ABC, abstractmethod
from collections import OrderedDict
from contextlib import ExitStack
from enum import Enum
from typing import Dict, List, NamedTuple, Optional

from dagster import check
from dagster.core.errors import DagsterInvariantViolationError, DagsterRepositoryLocationLoadError
from dagster.core.host_representation import (
    GrpcServerRepositoryLocation,
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
from dagster.grpc.server_watcher import create_grpc_watch_thread
from dagster.utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info


class IWorkspace(ABC):
    @abstractmethod
    def get_location(self, origin):
        """Return the RepositoryLocation for the given RepositoryLocationOrigin, or raise an error if there is an error loading it."""


# For locations that are loaded asynchronously
class WorkspaceLocationLoadStatus(Enum):
    LOADING = "LOADING"  # Waiting for location to load or update
    LOADED = "LOADED"  # Finished loading (may be an error)


class WorkspaceLocationEntry(NamedTuple):
    origin: RepositoryLocationOrigin
    repository_location: Optional[RepositoryLocation]
    load_error: Optional[SerializableErrorInfo]
    load_status: WorkspaceLocationLoadStatus
    display_metadata: Dict[str, str]
    update_timestamp: float


class Workspace(IWorkspace):
    """An IWorkspace that maintains a fixed list of origins, loading repositorylocations
    for all of them on initialization."""

    def __init__(self, workspace_load_target, grpc_server_registry=None):
        self._stack = ExitStack()

        # Guards changes to _location_dict, _location_error_dict, and _location_origin_dict
        self._lock = threading.Lock()

        # Only ever set up by main thread
        self._watch_thread_shutdown_events = {}
        self._watch_threads = {}

        self._state_subscribers: List[LocationStateSubscriber] = []

        from .cli_target import WorkspaceLoadTarget

        self._workspace_load_target = check.opt_inst_param(
            workspace_load_target, "workspace_load_target", WorkspaceLoadTarget
        )

        if grpc_server_registry:
            self._grpc_server_registry = check.inst_param(
                grpc_server_registry, "grpc_server_registry", GrpcServerRegistry
            )
        else:
            self._grpc_server_registry = self._stack.enter_context(
                ProcessGrpcServerRegistry(reload_interval=0, heartbeat_ttl=30)
            )

        self._location_entry_dict = OrderedDict()

        with self._lock:
            self._load_workspace()

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

    # Can be overidden in subclasses that need different logic for loading repository
    # locations from origins
    def create_location_from_origin(self, origin):
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

    def add_state_subscriber(self, subscriber):
        self._state_subscribers.append(subscriber)

    def _send_state_event_to_subscribers(self, event: LocationStateChangeEvent) -> None:
        check.inst_param(event, "event", LocationStateChangeEvent)
        for subscriber in self._state_subscribers:
            subscriber.handle_event(event)

    def _start_watch_thread(self, origin):
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
            location = self.create_location_from_origin(origin)
        except Exception:  # pylint: disable=broad-except
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
        return self.get_repository_location(location_name) != None

    def get_repository_location(self, location_name: str) -> Optional[RepositoryLocation]:
        with self._lock:
            return (
                self._location_entry_dict.get(location_name).repository_location
                if location_name in self._location_entry_dict
                else None
            )

    def has_repository_location_error(self, location_name):
        check.str_param(location_name, "location_name")
        with self._lock:
            return (
                location_name in self._location_entry_dict
                and self._location_entry_dict[location_name].load_error
            )

    def reload_repository_location(self, location_name):
        # Can be called from a background thread
        with self._lock:
            # Relying on GC to clean up the old location once nothing else
            # is referencing it
            self._location_entry_dict[location_name] = self._load_location(
                self._location_entry_dict[location_name].origin
            )

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

    def get_location(self, origin):
        with self._lock:
            location_name = origin.location_name
            location_entry = self._location_entry_dict.get(location_name)
            if not location_entry:
                raise DagsterInvariantViolationError(
                    f"Location {location_name} does not exist in workspace"
                )

            if location_entry.repository_location:
                return location_entry.repository_location

            error_info = location_entry.load_error
            raise DagsterRepositoryLocationLoadError(
                f"Failure loading {location_name}: {error_info.to_string()}",
                load_error_infos=[error_info],
            )

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        with self._lock:
            self._cleanup_locations()
        self._stack.close()
