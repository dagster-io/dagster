from typing import TYPE_CHECKING, Dict, List, NamedTuple, Optional, Union

from dagster import check
from dagster.cli.workspace.workspace import Workspace, WorkspaceSnapshot
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

if TYPE_CHECKING:
    from rx.subjects import Subject
    from dagster.core.host_representation import (
        ExternalPartitionSetExecutionParamData,
        ExternalPartitionExecutionErrorData,
        ExternalPartitionNamesData,
        ExternalPartitionConfigData,
        ExternalPartitionTagsData,
    )
    from dagster.utils.error import SerializableErrorInfo


class WorkspaceRequestContext(NamedTuple):
    """
    This class is request-scoped object that stores (1) a reference to all repository locations
    that exist on the `WorkspaceProcessContext` at the start of the request and (2) a snapshot of the
    `Workspace` at the start of the request.

    This object is needed because a process context and the repository locations on that context can
    be updated (for example, from a thread on the process context). If a request is accessing a
    repository location at the same time the repository location was being cleaned up, we would run
    into errors.
    """

    instance: DagsterInstance
    workspace_snapshot: WorkspaceSnapshot
    process_context: "WorkspaceProcessContext"
    version: Optional[str] = None

    @property
    def repository_locations_dict(self) -> Dict[str, RepositoryLocation]:
        return self.workspace_snapshot.repository_locations_dict

    @property
    def repository_locations(self) -> List[RepositoryLocation]:
        return list(self.repository_locations_dict.values())

    @property
    def repository_location_names(self) -> List[str]:
        return self.workspace_snapshot.repository_location_names

    def repository_location_errors(self) -> List["SerializableErrorInfo"]:
        return self.workspace_snapshot.repository_location_errors

    def get_repository_location(self, name: str) -> RepositoryLocation:
        return self.repository_locations_dict[name]

    def has_repository_location_error(self, name: str) -> bool:
        return self.workspace_snapshot.has_repository_location_error(name)

    def get_repository_location_error(self, name: str) -> "SerializableErrorInfo":
        return self.workspace_snapshot.get_repository_location_error(name)

    def has_repository_location(self, name: str) -> bool:
        return name in self.repository_locations_dict

    def is_reload_supported(self, name: str) -> bool:
        return self.workspace_snapshot.is_reload_supported(name)

    def reload_repository_location(self, name: str) -> "WorkspaceRequestContext":
        # This method reloads the location on the process context, and returns a new
        # request context created from the updated process context
        updated_process_context = self.process_context.reload_repository_location(name)
        return updated_process_context.create_request_context()

    def reload_workspace(self) -> "WorkspaceRequestContext":
        self.process_context.reload_workspace()
        return self.process_context.create_request_context()

    def has_external_pipeline(self, selector: PipelineSelector) -> bool:
        check.inst_param(selector, "selector", PipelineSelector)
        loc = self.repository_locations_dict.get(selector.location_name)
        return (
            loc is not None
            and loc.has_repository(selector.repository_name)
            and loc.get_repository(selector.repository_name).has_external_pipeline(
                selector.pipeline_name
            )
        )

    def get_full_external_pipeline(self, selector: PipelineSelector) -> ExternalPipeline:
        return (
            self.repository_locations_dict[selector.location_name]
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
        return self.repository_locations_dict[
            external_pipeline.handle.location_name
        ].get_external_execution_plan(
            external_pipeline=external_pipeline,
            run_config=run_config,
            mode=mode,
            step_keys_to_execute=step_keys_to_execute,
            known_state=known_state,
        )

    def get_external_partition_config(
        self, repository_handle: RepositoryHandle, partition_set_name: str, partition_name: str
    ) -> Union["ExternalPartitionConfigData", "ExternalPartitionExecutionErrorData"]:
        return self.repository_locations_dict[
            repository_handle.repository_location.name
        ].get_external_partition_config(
            repository_handle=repository_handle,
            partition_set_name=partition_set_name,
            partition_name=partition_name,
        )

    def get_external_partition_tags(
        self, repository_handle: RepositoryHandle, partition_set_name: str, partition_name: str
    ) -> Union["ExternalPartitionTagsData", "ExternalPartitionExecutionErrorData"]:
        return self.repository_locations_dict[
            repository_handle.repository_location.name
        ].get_external_partition_tags(
            repository_handle=repository_handle,
            partition_set_name=partition_set_name,
            partition_name=partition_name,
        )

    def get_external_partition_names(
        self, repository_handle: RepositoryHandle, partition_set_name: str
    ) -> Union["ExternalPartitionNamesData", "ExternalPartitionExecutionErrorData"]:
        return self.repository_locations_dict[
            repository_handle.repository_location.name
        ].get_external_partition_names(repository_handle, partition_set_name)

    def get_external_partition_set_execution_param_data(
        self,
        repository_handle: RepositoryHandle,
        partition_set_name: str,
        partition_names: List[str],
    ) -> Union["ExternalPartitionSetExecutionParamData", "ExternalPartitionExecutionErrorData"]:
        return self.repository_locations_dict[
            repository_handle.repository_location.name
        ].get_external_partition_set_execution_param_data(
            repository_handle=repository_handle,
            partition_set_name=partition_set_name,
            partition_names=partition_names,
        )


class WorkspaceProcessContext:
    """
    This class is process-scoped object that is initialized using the repository handles from a
    Workspace. The responsibility of this class is to:

    1. Maintain an update-to-date dictionary of repository locations
    1. Create `WorkspaceRequestContexts` whever a request is made
    2. Run watch thread processes that monitor repository locations

    In most cases, you will want to create a `WorkspaceRequestContext` to make use of this class.
    """

    def __init__(
        self, instance: DagsterInstance, workspace: Workspace, version: Optional[str] = None
    ):
        # lazy import for perf
        from rx.subjects import Subject

        self._instance = check.inst_param(instance, "instance", DagsterInstance)
        self._workspace = workspace

        self._location_state_events = Subject()
        self._location_state_subscriber = LocationStateSubscriber(
            self._location_state_events_handler
        )

        self.version = version
        self.set_state_subscribers()

    def set_state_subscribers(self):
        self._workspace.add_state_subscriber(self._location_state_subscriber)

    def create_request_context(self) -> WorkspaceRequestContext:
        return WorkspaceRequestContext(
            instance=self.instance,
            workspace_snapshot=self._workspace.create_snapshot(),
            process_context=self,
            version=self.version,
        )

    @property
    def instance(self) -> DagsterInstance:
        return self._instance

    @property
    def workspace(self) -> Workspace:
        return self._workspace

    @property
    def repository_locations(self) -> List[RepositoryLocation]:
        return self._workspace.repository_locations

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

    def reload_repository_location(self, name: str) -> "WorkspaceProcessContext":
        self._workspace.reload_repository_location(name)
        return self

    def reload_workspace(self) -> None:
        self._workspace.reload_workspace()
        self.set_state_subscribers()
