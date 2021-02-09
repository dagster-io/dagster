from collections import namedtuple

from dagster import check
from dagster.core.host_representation import PipelineSelector
from dagster.core.host_representation.grpc_server_state_subscriber import (
    LocationStateChangeEventType,
    LocationStateSubscriber,
)
from dagster.core.instance import DagsterInstance
from rx.subjects import Subject


class WorkspaceRequestContext(
    namedtuple(
        "WorkspaceRequestContext",
        "instance workspace_snapshot repository_locations_dict process_context version",
    )
):
    """
    This class is request-scoped object that stores (1) a reference to all repository locations
    that exist on the `WorkspaceProcessContext` at the start of the request and (2) a snapshot of the
    `Workspace` at the start of the request.

    This object is needed because a process context and the repository locations on that context can
    be updated (for example, from a thread on the process context). If a request is accessing a
    repository location at the same time the repository location was being cleaned up, we would run
    into errors.
    """

    def __new__(
        cls, instance, workspace_snapshot, repository_locations_dict, process_context, version
    ):
        return super(WorkspaceRequestContext, cls).__new__(
            cls,
            instance,
            workspace_snapshot,
            repository_locations_dict,
            process_context,
            version,
        )

    @property
    def repository_locations(self):
        return list(self.repository_locations_dict.values())

    @property
    def repository_location_names(self):
        return self.workspace_snapshot.repository_location_names

    def repository_location_errors(self):
        return self.workspace_snapshot.repository_location_errors

    def get_repository_location(self, name):
        return self.repository_locations_dict[name]

    def has_repository_location_error(self, name):
        return self.workspace_snapshot.has_repository_location_error(name)

    def get_repository_location_error(self, name):
        return self.workspace_snapshot.get_repository_location_error(name)

    def has_repository_location(self, name):
        return name in self.repository_locations_dict

    def is_reload_supported(self, name):
        return self.workspace_snapshot.is_reload_supported(name)

    def reload_repository_location(self, name):
        # This method reloads the location on the process context, and returns a new
        # request context created from the updated process context
        updated_process_context = self.process_context.reload_repository_location(name)
        return updated_process_context.create_request_context()

    def has_external_pipeline(self, selector):
        check.inst_param(selector, "selector", PipelineSelector)
        if selector.location_name in self.repository_locations_dict:
            loc = self.repository_locations_dict[selector.location_name]
            if loc.has_repository(selector.repository_name):
                return loc.get_repository(selector.repository_name).has_external_pipeline(
                    selector.pipeline_name
                )

    def get_full_external_pipeline(self, selector):
        return (
            self.repository_locations_dict[selector.location_name]
            .get_repository(selector.repository_name)
            .get_full_external_pipeline(selector.pipeline_name)
        )

    def get_external_execution_plan(
        self, external_pipeline, run_config, mode, step_keys_to_execute
    ):
        return self.repository_locations_dict[
            external_pipeline.handle.location_name
        ].get_external_execution_plan(
            external_pipeline=external_pipeline,
            run_config=run_config,
            mode=mode,
            step_keys_to_execute=step_keys_to_execute,
        )

    def get_external_partition_config(self, repository_handle, partition_set_name, partition_name):
        return self.repository_locations_dict[
            repository_handle.repository_location_handle.location_name
        ].get_external_partition_config(
            repository_handle=repository_handle,
            partition_set_name=partition_set_name,
            partition_name=partition_name,
        )

    def get_external_partition_tags(self, repository_handle, partition_set_name, partition_name):
        return self.repository_locations_dict[
            repository_handle.repository_location_handle.location_name
        ].get_external_partition_tags(
            repository_handle=repository_handle,
            partition_set_name=partition_set_name,
            partition_name=partition_name,
        )

    def get_external_partition_names(self, repository_handle, partition_set_name):
        return self.repository_locations_dict[
            repository_handle.repository_location_handle.location_name
        ].get_external_partition_names(repository_handle, partition_set_name)

    def get_external_partition_set_execution_param_data(
        self, repository_handle, partition_set_name, partition_names
    ):
        return self.repository_locations_dict[
            repository_handle.repository_location_handle.location_name
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

    def __init__(self, instance, workspace, version=None):
        self._instance = check.inst_param(instance, "instance", DagsterInstance)
        self._workspace = workspace
        self._repository_locations = {}

        self._location_state_events = Subject()
        self._location_state_subscriber = LocationStateSubscriber(
            self._location_state_events_handler
        )

        for handle in self._workspace.repository_location_handles:
            check.invariant(
                self._repository_locations.get(handle.location_name) is None,
                'Cannot have multiple locations with the same name, got multiple "{name}"'.format(
                    name=handle.location_name,
                ),
            )

            handle.add_state_subscriber(self._location_state_subscriber)
            self._repository_locations[handle.location_name] = handle.create_location()

        self.version = version

    def create_request_context(self):
        return WorkspaceRequestContext(
            instance=self.instance,
            workspace_snapshot=self._workspace.create_snapshot(),
            repository_locations_dict=self._repository_locations.copy(),
            process_context=self,
            version=self.version,
        )

    @property
    def instance(self):
        return self._instance

    @property
    def workspace(self):
        return self._instance

    @property
    def repository_locations(self):
        return list(self._repository_locations.values())

    @property
    def location_state_events(self):
        return self._location_state_events

    def _location_state_events_handler(self, event):
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

    def reload_repository_location(self, name):
        self._workspace.reload_repository_location(name)

        if self._workspace.has_repository_location_handle(name):
            new_handle = self._workspace.get_repository_location_handle(name)
            new_handle.add_state_subscriber(self._location_state_subscriber)
            new_location = new_handle.create_location()
            check.invariant(new_location.name == name)
            self._repository_locations[name] = new_location
        elif name in self._repository_locations:
            del self._repository_locations[name]

        return self
