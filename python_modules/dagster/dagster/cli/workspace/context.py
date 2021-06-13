from abc import ABC, abstractmethod, abstractproperty
from typing import TYPE_CHECKING, Dict, List, NamedTuple, Optional, Union, cast

from dagster import check
from dagster.cli.workspace.workspace import (
    Workspace,
    WorkspaceLocationEntry,
    WorkspaceLocationLoadStatus,
)
from dagster.core.execution.plan.state import KnownExecutionState
from dagster.core.host_representation import (
    ExternalExecutionPlan,
    ExternalPipeline,
    PipelineSelector,
    RepositoryHandle,
    RepositoryLocation,
)
from dagster.core.host_representation.grpc_server_state_subscriber import (
    LocationStateChangeEvent,
    LocationStateChangeEventType,
    LocationStateSubscriber,
)
from dagster.core.instance import DagsterInstance
from dagster.utils.error import SerializableErrorInfo

if TYPE_CHECKING:
    from rx.subjects import Subject
    from dagster.core.host_representation import (
        ExternalPartitionSetExecutionParamData,
        ExternalPartitionExecutionErrorData,
        ExternalPartitionNamesData,
        ExternalPartitionConfigData,
        ExternalPartitionTagsData,
    )


class WorkspaceRequestContext(NamedTuple):
    """
    This class is request-scoped object that stores (1) a reference to all repository locations
    that exist on the `IWorkspaceProcessContext` at the start of the request and (2) a snapshot of the
    `Workspace` at the start of the request.

    This object is needed because a process context and the repository locations on that context can
    be updated (for example, from a thread on the process context). If a request is accessing a
    repository location at the same time the repository location was being cleaned up, we would run
    into errors.
    """

    instance: DagsterInstance
    workspace_snapshot: Dict[str, WorkspaceLocationEntry]
    process_context: "IWorkspaceProcessContext"
    version: Optional[str] = None

    @property
    def repository_locations(self) -> List[RepositoryLocation]:
        return [
            entry.repository_location
            for entry in self.workspace_snapshot.values()
            if entry.repository_location
        ]

    @property
    def repository_location_names(self) -> List[str]:
        return list(self.workspace_snapshot)

    @property
    def read_only(self) -> bool:
        return self.process_context.read_only

    def repository_location_errors(self) -> List[SerializableErrorInfo]:
        return [entry.load_error for entry in self.workspace_snapshot.values() if entry.load_error]

    def get_repository_location(self, name: str) -> RepositoryLocation:
        return cast(RepositoryLocation, self.workspace_snapshot[name].repository_location)

    def get_load_status(self, name: str) -> WorkspaceLocationLoadStatus:
        return self.workspace_snapshot[name].load_status

    def has_repository_location_error(self, name: str) -> bool:
        return self.get_repository_location_error(name) != None

    def get_repository_location_error(self, name: str) -> Optional[SerializableErrorInfo]:
        return self.workspace_snapshot[name].load_error

    def has_repository_location(self, name: str) -> bool:
        location_entry = self.workspace_snapshot.get(name)
        return bool(location_entry and location_entry.repository_location != None)

    def is_reload_supported(self, name: str) -> bool:
        return self.workspace_snapshot[name].origin.is_reload_supported

    def reload_repository_location(self, name: str) -> "WorkspaceRequestContext":
        # This method reloads the location on the process context, and returns a new
        # request context created from the updated process context
        self.process_context.reload_repository_location(name)
        return self.process_context.create_request_context()

    def reload_workspace(self) -> "WorkspaceRequestContext":
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
        )

    def get_external_partition_config(
        self, repository_handle: RepositoryHandle, partition_set_name: str, partition_name: str
    ) -> Union["ExternalPartitionConfigData", "ExternalPartitionExecutionErrorData"]:
        return self.get_repository_location(
            repository_handle.repository_location.name
        ).get_external_partition_config(
            repository_handle=repository_handle,
            partition_set_name=partition_set_name,
            partition_name=partition_name,
        )

    def get_external_partition_tags(
        self, repository_handle: RepositoryHandle, partition_set_name: str, partition_name: str
    ) -> Union["ExternalPartitionTagsData", "ExternalPartitionExecutionErrorData"]:
        return self.get_repository_location(
            repository_handle.repository_location.name
        ).get_external_partition_tags(
            repository_handle=repository_handle,
            partition_set_name=partition_set_name,
            partition_name=partition_name,
        )

    def get_external_partition_names(
        self, repository_handle: RepositoryHandle, partition_set_name: str
    ) -> Union["ExternalPartitionNamesData", "ExternalPartitionExecutionErrorData"]:
        return self.get_repository_location(
            repository_handle.repository_location.name
        ).get_external_partition_names(repository_handle, partition_set_name)

    def get_external_partition_set_execution_param_data(
        self,
        repository_handle: RepositoryHandle,
        partition_set_name: str,
        partition_names: List[str],
    ) -> Union["ExternalPartitionSetExecutionParamData", "ExternalPartitionExecutionErrorData"]:
        return self.get_repository_location(
            repository_handle.repository_location.name
        ).get_external_partition_set_execution_param_data(
            repository_handle=repository_handle,
            partition_set_name=partition_set_name,
            partition_names=partition_names,
        )


class IWorkspaceProcessContext(ABC):
    """
    Class that stores process-scoped information about a dagit session.
    In most cases, you will want to create a `WorkspaceRequestContext` to create a request-scoped
    object.
    """

    @abstractmethod
    def create_request_context(self) -> WorkspaceRequestContext:
        pass

    @abstractproperty
    def read_only(self) -> bool:
        pass

    @abstractproperty
    def version(self) -> str:
        pass

    @abstractproperty
    def location_state_events(self) -> "Subject":
        pass

    @abstractmethod
    def reload_repository_location(self, name: str) -> None:
        pass

    @abstractmethod
    def reload_workspace(self) -> None:
        pass

    @abstractproperty
    def instance(self):
        pass


class WorkspaceProcessContext(IWorkspaceProcessContext):
    """
    This class is process-scoped object that is initialized using the repository handles from a
    Workspace. The responsibility of this class is to:

    1. Maintain an update-to-date dictionary of repository locations
    1. Create `WorkspaceRequestContexts` whever a request is made
    2. Run watch thread processes that monitor repository locations

    In most cases, you will want to create a `WorkspaceRequestContext` to make use of this class.
    """

    def __init__(
        self,
        instance: DagsterInstance,
        workspace: Workspace,
        version: Optional[str] = None,
        read_only: bool = False,
    ):

        check.inst_param(instance, "instance", DagsterInstance)
        check.inst_param(workspace, "workspace", Workspace)
        check.opt_str_param(version, "version")
        check.bool_param(read_only, "read_only")

        # lazy import for perf
        from rx.subjects import Subject

        self._instance = check.inst_param(instance, "instance", DagsterInstance)
        self._workspace = workspace

        self._location_state_events = Subject()
        self._location_state_subscriber = LocationStateSubscriber(
            self._location_state_events_handler
        )

        self._read_only = read_only
        self._version = version
        self._set_state_subscribers()

    @property
    def instance(self):
        return self._instance

    @property
    def read_only(self):
        return self._read_only

    @property
    def version(self):
        return self._version

    def _set_state_subscribers(self):
        self._workspace.add_state_subscriber(self._location_state_subscriber)

    def create_request_context(self) -> WorkspaceRequestContext:
        return WorkspaceRequestContext(
            instance=self._instance,
            workspace_snapshot=self._workspace.create_snapshot(),
            process_context=self,
            version=self.version,
        )

    @property
    def workspace(self) -> Workspace:
        return self._workspace

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

    def reload_repository_location(self, name: str) -> None:
        self._workspace.reload_repository_location(name)

    def reload_workspace(self) -> None:
        self._workspace.reload_workspace()
        self._set_state_subscribers()
