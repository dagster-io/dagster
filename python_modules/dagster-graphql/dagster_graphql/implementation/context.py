from dagster import check
from dagster.core.host_representation import PipelineSelector, RepositoryLocation
from dagster.core.host_representation.external import ExternalPipeline
from dagster.core.host_representation.grpc_server_state_subscriber import (
    LocationStateChangeEventType,
    LocationStateSubscriber,
)
from dagster.core.instance import DagsterInstance
from rx.subjects import Subject


class DagsterGraphQLContext:
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
            self._repository_locations[handle.location_name] = RepositoryLocation.from_handle(
                handle
            )

        self.version = version

    @property
    def instance(self):
        return self._instance

    @property
    def repository_locations(self):
        return list(self._repository_locations.values())

    @property
    def repository_location_names(self):
        return self._workspace.repository_location_names

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

    def repository_location_errors(self):
        return self._workspace.repository_location_errors

    def get_repository_location(self, name):
        return self._repository_locations[name]

    def has_repository_location_error(self, name):
        return self._workspace.has_repository_location_error(name)

    def get_repository_location_error(self, name):
        return self._workspace.get_repository_location_error(name)

    def has_repository_location(self, name):
        return name in self._repository_locations

    def is_reload_supported(self, name):
        return self._workspace.is_reload_supported(name)

    def reload_repository_location(self, name):
        self._workspace.reload_repository_location(name)

        if self._workspace.has_repository_location_handle(name):
            new_handle = self._workspace.get_repository_location_handle(name)
            new_handle.add_state_subscriber(self._location_state_subscriber)
            new_location = RepositoryLocation.from_handle(new_handle)
            check.invariant(new_location.name == name)
            self._repository_locations[name] = new_location
        elif name in self._repository_locations:
            del self._repository_locations[name]

    def get_subset_external_pipeline(self, selector):
        from ..schema.pipelines.pipeline_errors import GrapheneInvalidSubsetError
        from ..schema.pipelines.pipeline import GraphenePipeline
        from .utils import UserFacingGraphQLError

        check.inst_param(selector, "selector", PipelineSelector)
        # We have to grab the pipeline from the location instead of the repository directly
        # since we may have to request a subset we don't have in memory yet

        repository_location = self._repository_locations[selector.location_name]
        external_repository = repository_location.get_repository(selector.repository_name)

        subset_result = repository_location.get_subset_external_pipeline_result(selector)
        if not subset_result.success:
            error_info = subset_result.error
            raise UserFacingGraphQLError(
                GrapheneInvalidSubsetError(
                    message="{message}{cause_message}".format(
                        message=error_info.message,
                        cause_message="\n{}".format(error_info.cause.message)
                        if error_info.cause
                        else "",
                    ),
                    pipeline=GraphenePipeline(self.get_full_external_pipeline(selector)),
                )
            )

        return ExternalPipeline(
            subset_result.external_pipeline_data,
            repository_handle=external_repository.handle,
        )

    def has_external_pipeline(self, selector):
        check.inst_param(selector, "selector", PipelineSelector)
        if selector.location_name in self._repository_locations:
            loc = self._repository_locations[selector.location_name]
            if loc.has_repository(selector.repository_name):
                return loc.get_repository(selector.repository_name).has_external_pipeline(
                    selector.pipeline_name
                )

    def get_full_external_pipeline(self, selector):
        return (
            self._repository_locations[selector.location_name]
            .get_repository(selector.repository_name)
            .get_full_external_pipeline(selector.pipeline_name)
        )

    def get_external_execution_plan(
        self, external_pipeline, run_config, mode, step_keys_to_execute
    ):
        return self._repository_locations[
            external_pipeline.handle.location_name
        ].get_external_execution_plan(
            external_pipeline=external_pipeline,
            run_config=run_config,
            mode=mode,
            step_keys_to_execute=step_keys_to_execute,
        )

    def get_external_partition_config(self, repository_handle, partition_set_name, partition_name):
        return self._repository_locations[
            repository_handle.repository_location_handle.location_name
        ].get_external_partition_config(
            repository_handle=repository_handle,
            partition_set_name=partition_set_name,
            partition_name=partition_name,
        )

    def get_external_partition_tags(self, repository_handle, partition_set_name, partition_name):
        return self._repository_locations[
            repository_handle.repository_location_handle.location_name
        ].get_external_partition_tags(
            repository_handle=repository_handle,
            partition_set_name=partition_set_name,
            partition_name=partition_name,
        )

    def get_external_partition_names(self, repository_handle, partition_set_name):
        return self._repository_locations[
            repository_handle.repository_location_handle.location_name
        ].get_external_partition_names(repository_handle, partition_set_name)

    def get_external_partition_set_execution_param_data(
        self, repository_handle, partition_set_name, partition_names
    ):
        return self._repository_locations[
            repository_handle.repository_location_handle.location_name
        ].get_external_partition_set_execution_param_data(
            repository_handle=repository_handle,
            partition_set_name=partition_set_name,
            partition_names=partition_names,
        )
