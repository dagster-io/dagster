from dagster_graphql.implementation.utils import UserFacingGraphQLError
from dagster_graphql.schema.errors import DauphinInvalidSubsetError
from dagster_graphql.schema.pipelines import DauphinPipeline

from dagster import check
from dagster.core.host_representation import PipelineSelector, RepositoryLocation
from dagster.core.host_representation.external import ExternalPipeline
from dagster.core.instance import DagsterInstance
from dagster.grpc.types import ScheduleExecutionDataMode


class DagsterGraphQLContext:
    def __init__(self, instance, workspace, version=None):
        self._instance = check.inst_param(instance, "instance", DagsterInstance)
        self._workspace = workspace
        self._repository_locations = {}
        for handle in self._workspace.repository_location_handles:
            check.invariant(
                self._repository_locations.get(handle.location_name) is None,
                'Can not have multiple locations with the same name, got multiple "{name}"'.format(
                    name=handle.location_name,
                ),
            )
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

    def get_repository_location(self, name):
        return self._repository_locations[name]

    def has_repository_location(self, name):
        return name in self._repository_locations

    def reload_repository_location(self, name):
        new_handle = self._workspace.reload_repository_location(name)
        new_location = RepositoryLocation.from_handle(new_handle)
        check.invariant(new_location.name == name)
        self._repository_locations[name] = new_location
        return new_location

    def get_subset_external_pipeline(self, selector):
        check.inst_param(selector, "selector", PipelineSelector)
        # We have to grab the pipeline from the location instead of the repository directly
        # since we may have to request a subset we don't have in memory yet

        repository_location = self._repository_locations[selector.location_name]
        external_repository = repository_location.get_repository(selector.repository_name)

        subset_result = repository_location.get_subset_external_pipeline_result(selector)
        if not subset_result.success:
            error_info = subset_result.error
            raise UserFacingGraphQLError(
                DauphinInvalidSubsetError(
                    message="{message}{cause_message}".format(
                        message=error_info.message,
                        cause_message="\n{}".format(error_info.cause.message)
                        if error_info.cause
                        else "",
                    ),
                    pipeline=DauphinPipeline(self.get_full_external_pipeline(selector)),
                )
            )

        return ExternalPipeline(
            subset_result.external_pipeline_data, repository_handle=external_repository.handle,
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

    def get_external_schedule_execution_data(self, repository_handle, schedule_name):
        return self._repository_locations[
            repository_handle.repository_location_handle.location_name
        ].get_external_schedule_execution_data(
            self.instance, repository_handle, schedule_name, ScheduleExecutionDataMode.PREVIEW,
        )

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

    def execute_plan(
        self, external_pipeline, run_config, pipeline_run, step_keys_to_execute, retries=None
    ):
        return self._repository_locations[external_pipeline.handle.location_name].execute_plan(
            instance=self.instance,
            external_pipeline=external_pipeline,
            run_config=run_config,
            pipeline_run=pipeline_run,
            step_keys_to_execute=step_keys_to_execute,
            retries=retries,
        )

    def execute_pipeline(self, external_pipeline, pipeline_run):
        return self._repository_locations[external_pipeline.handle.location_name].execute_pipeline(
            instance=self.instance, external_pipeline=external_pipeline, pipeline_run=pipeline_run
        )
