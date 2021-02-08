import datetime
from abc import ABC, abstractmethod, abstractproperty

import pendulum
from dagster import check
from dagster.api.snapshot_execution_plan import sync_get_external_execution_plan_grpc
from dagster.api.snapshot_partition import (
    sync_get_external_partition_config_grpc,
    sync_get_external_partition_names_grpc,
    sync_get_external_partition_set_execution_param_data_grpc,
    sync_get_external_partition_tags_grpc,
)
from dagster.api.snapshot_pipeline import sync_get_external_pipeline_subset_grpc
from dagster.api.snapshot_repository import sync_get_streaming_external_repositories_grpc
from dagster.api.snapshot_schedule import sync_get_external_schedule_execution_data_grpc
from dagster.api.snapshot_sensor import sync_get_external_sensor_execution_data_grpc
from dagster.core.execution.api import create_execution_plan
from dagster.core.host_representation import (
    ExternalExecutionPlan,
    ExternalPipeline,
    GrpcServerRepositoryLocationHandle,
    InProcessRepositoryLocationHandle,
    ManagedGrpcPythonEnvRepositoryLocationHandle,
    PipelineHandle,
    RepositoryHandle,
)
from dagster.core.instance import DagsterInstance
from dagster.core.snap.execution_plan_snapshot import (
    ExecutionPlanSnapshotErrorData,
    snapshot_from_execution_plan,
)
from dagster.grpc.impl import (
    get_external_schedule_execution,
    get_external_sensor_execution,
    get_partition_config,
    get_partition_names,
    get_partition_set_execution_param_data,
    get_partition_tags,
)
from dagster.utils.hosted_user_process import external_repo_from_def

from .selector import PipelineSelector


class RepositoryLocation(ABC):
    """
    A RepositoryLocation represents a target containing user code which has a set of Dagster
    definition objects. A given location will contain some number of uniquely named
    RepositoryDefinitions, which therein contains Pipeline, Solid, and other definitions.

    Dagster tools are typically "host" processes, meaning they load a RepositoryLocation and
    communicate with it over an IPC/RPC layer. Currently this IPC layer is implemented by
    invoking the dagster CLI in a target python interpreter (e.g. a virtual environment) in either
      a) the current node
      b) a container

    In the near future, we may also make this communication channel able over an RPC layer, in
    which case the information needed to load a RepositoryLocation will be a url that abides by
    some RPC contract.

    We also allow for InProcessRepositoryLocation which actually loads the user-defined artifacts
    into process with the host tool. This is mostly for test scenarios.
    """

    @abstractmethod
    def get_repository(self, name):
        pass

    @abstractmethod
    def has_repository(self, name):
        pass

    @abstractmethod
    def get_repositories(self):
        pass

    def get_repository_names(self):
        return list(self.get_repositories().keys())

    @abstractproperty
    def name(self):
        pass

    @abstractproperty
    def location_handle(self):
        pass

    @abstractmethod
    def get_external_execution_plan(
        self, external_pipeline, run_config, mode, step_keys_to_execute
    ):
        pass

    @abstractmethod
    def get_subset_external_pipeline_result(self, selector):
        pass

    @abstractmethod
    def get_external_partition_config(self, repository_handle, partition_set_name, partition_name):
        pass

    @abstractmethod
    def get_external_partition_tags(self, repository_handle, partition_set_name, partition_name):
        pass

    @abstractmethod
    def get_external_partition_names(self, repository_handle, partition_set_name):
        pass

    @abstractmethod
    def get_external_partition_set_execution_param_data(
        self, repository_handle, partition_set_name, partition_names
    ):
        pass

    @abstractmethod
    def get_external_schedule_execution_data(
        self,
        instance,
        repository_handle,
        schedule_name,
        scheduled_execution_time,
    ):
        pass

    @abstractmethod
    def get_external_sensor_execution_data(
        self, instance, repository_handle, name, last_completion_time, last_run_key
    ):
        pass

    @abstractproperty
    def is_reload_supported(self):
        pass


class InProcessRepositoryLocation(RepositoryLocation):
    def __init__(self, handle):
        self._handle = check.inst_param(
            handle,
            "handle",
            InProcessRepositoryLocationHandle,
        )

        self._recon_repo = self._handle.origin.recon_repo

        repo_def = self._recon_repo.get_definition()
        def_name = repo_def.name
        self._external_repo = external_repo_from_def(
            repo_def,
            RepositoryHandle(repository_name=def_name, repository_location_handle=self._handle),
        )
        self._repositories = {self._external_repo.name: self._external_repo}

    @property
    def is_reload_supported(self):
        return False

    def get_reconstructable_pipeline(self, name):
        return self.get_reconstructable_repository().get_reconstructable_pipeline(name)

    def get_reconstructable_repository(self):
        return self._handle.origin.recon_repo

    @property
    def name(self):
        return self._handle.location_name

    @property
    def location_handle(self):
        return self._handle

    def get_repository(self, name):
        return self._repositories[name]

    def has_repository(self, name):
        return name in self._repositories

    def get_repositories(self):
        return self._repositories

    def get_subset_external_pipeline_result(self, selector):
        check.inst_param(selector, "selector", PipelineSelector)
        check.invariant(
            selector.location_name == self.name,
            "PipelineSelector location_name mismatch, got {selector.location_name} expected {self.name}".format(
                self=self, selector=selector
            ),
        )

        from dagster.grpc.impl import get_external_pipeline_subset_result

        return get_external_pipeline_subset_result(
            self.get_reconstructable_pipeline(selector.pipeline_name), selector.solid_selection
        )

    def get_external_execution_plan(
        self, external_pipeline, run_config, mode, step_keys_to_execute
    ):
        check.inst_param(external_pipeline, "external_pipeline", ExternalPipeline)
        check.dict_param(run_config, "run_config")
        check.str_param(mode, "mode")
        check.opt_list_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)

        return ExternalExecutionPlan(
            execution_plan_snapshot=snapshot_from_execution_plan(
                create_execution_plan(
                    pipeline=self.get_reconstructable_pipeline(
                        external_pipeline.name
                    ).subset_for_execution_from_existing_pipeline(
                        external_pipeline.solids_to_execute
                    ),
                    run_config=run_config,
                    mode=mode,
                    step_keys_to_execute=step_keys_to_execute,
                ),
                external_pipeline.identifying_pipeline_snapshot_id,
            ),
            represented_pipeline=external_pipeline,
        )

    def get_external_partition_config(self, repository_handle, partition_set_name, partition_name):
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")
        check.str_param(partition_name, "partition_name")

        return get_partition_config(
            recon_repo=self._recon_repo,
            partition_set_name=partition_set_name,
            partition_name=partition_name,
        )

    def get_external_partition_tags(self, repository_handle, partition_set_name, partition_name):
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")
        check.str_param(partition_name, "partition_name")

        return get_partition_tags(
            recon_repo=self._recon_repo,
            partition_set_name=partition_set_name,
            partition_name=partition_name,
        )

    def get_external_partition_names(self, repository_handle, partition_set_name):
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")

        return get_partition_names(
            recon_repo=self._recon_repo,
            partition_set_name=partition_set_name,
        )

    def get_external_schedule_execution_data(
        self,
        instance,
        repository_handle,
        schedule_name,
        scheduled_execution_time,
    ):
        check.inst_param(instance, "instance", DagsterInstance)
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(schedule_name, "schedule_name")
        check.opt_inst_param(
            scheduled_execution_time, "scheduled_execution_time", pendulum.Pendulum
        )

        return get_external_schedule_execution(
            self._recon_repo,
            instance_ref=instance.get_ref(),
            schedule_name=schedule_name,
            scheduled_execution_timestamp=scheduled_execution_time.timestamp()
            if scheduled_execution_time
            else None,
            scheduled_execution_timezone=scheduled_execution_time.timezone.name
            if scheduled_execution_time
            else None,
        )

    def get_external_sensor_execution_data(
        self, instance, repository_handle, name, last_completion_time, last_run_key
    ):
        return get_external_sensor_execution(
            self._recon_repo, instance.get_ref(), name, last_completion_time, last_run_key
        )

    def get_external_partition_set_execution_param_data(
        self, repository_handle, partition_set_name, partition_names
    ):
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")
        check.list_param(partition_names, "partition_names", of_type=str)

        return get_partition_set_execution_param_data(
            self._recon_repo,
            partition_set_name=partition_set_name,
            partition_names=partition_names,
        )


class GrpcServerRepositoryLocation(RepositoryLocation):
    def __init__(self, repository_location_handle):
        check.param_invariant(
            isinstance(repository_location_handle, GrpcServerRepositoryLocationHandle)
            or isinstance(repository_location_handle, ManagedGrpcPythonEnvRepositoryLocationHandle),
            "repository_location_handle",
        )

        self._handle = repository_location_handle

        external_repositories_list = sync_get_streaming_external_repositories_grpc(
            self._handle.client,
            self._handle,
        )

        self.external_repositories = {repo.name: repo for repo in external_repositories_list}

    @property
    def is_reload_supported(self):
        return True

    def get_repository(self, name):
        check.str_param(name, "name")
        return self.external_repositories[name]

    def has_repository(self, name):
        return name in self.external_repositories

    def get_repositories(self):
        return self.external_repositories

    @property
    def name(self):
        return self._handle.location_name

    @property
    def location_handle(self):
        return self._handle

    def get_external_execution_plan(
        self, external_pipeline, run_config, mode, step_keys_to_execute
    ):
        check.inst_param(external_pipeline, "external_pipeline", ExternalPipeline)
        check.dict_param(run_config, "run_config")
        check.str_param(mode, "mode")
        check.opt_list_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)

        execution_plan_snapshot_or_error = sync_get_external_execution_plan_grpc(
            api_client=self._handle.client,
            pipeline_origin=external_pipeline.get_external_origin(),
            run_config=run_config,
            mode=mode,
            pipeline_snapshot_id=external_pipeline.identifying_pipeline_snapshot_id,
            solid_selection=external_pipeline.solid_selection,
            step_keys_to_execute=step_keys_to_execute,
        )

        if isinstance(execution_plan_snapshot_or_error, ExecutionPlanSnapshotErrorData):
            return execution_plan_snapshot_or_error

        return ExternalExecutionPlan(
            execution_plan_snapshot=execution_plan_snapshot_or_error,
            represented_pipeline=external_pipeline,
        )

    def get_subset_external_pipeline_result(self, selector):
        check.inst_param(selector, "selector", PipelineSelector)
        check.invariant(
            selector.location_name == self.name,
            "PipelineSelector location_name mismatch, got {selector.location_name} expected {self.name}".format(
                self=self, selector=selector
            ),
        )

        external_repository = self.external_repositories[selector.repository_name]
        pipeline_handle = PipelineHandle(selector.pipeline_name, external_repository.handle)
        return sync_get_external_pipeline_subset_grpc(
            self._handle.client, pipeline_handle.get_external_origin(), selector.solid_selection
        )

    def get_external_partition_config(self, repository_handle, partition_set_name, partition_name):
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")
        check.str_param(partition_name, "partition_name")

        return sync_get_external_partition_config_grpc(
            self._handle.client, repository_handle, partition_set_name, partition_name
        )

    def get_external_partition_tags(self, repository_handle, partition_set_name, partition_name):
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")
        check.str_param(partition_name, "partition_name")

        return sync_get_external_partition_tags_grpc(
            self._handle.client, repository_handle, partition_set_name, partition_name
        )

    def get_external_partition_names(self, repository_handle, partition_set_name):
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")

        return sync_get_external_partition_names_grpc(
            self._handle.client, repository_handle, partition_set_name
        )

    def get_external_schedule_execution_data(
        self,
        instance,
        repository_handle,
        schedule_name,
        scheduled_execution_time,
    ):
        check.inst_param(instance, "instance", DagsterInstance)
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(schedule_name, "schedule_name")
        check.opt_inst_param(
            scheduled_execution_time, "scheduled_execution_time", datetime.datetime
        )

        return sync_get_external_schedule_execution_data_grpc(
            self._handle.client,
            instance,
            repository_handle,
            schedule_name,
            scheduled_execution_time,
        )

    def get_external_sensor_execution_data(
        self, instance, repository_handle, name, last_completion_time, last_run_key
    ):
        return sync_get_external_sensor_execution_data_grpc(
            self._handle.client,
            instance,
            repository_handle,
            name,
            last_completion_time,
            last_run_key,
        )

    def get_external_partition_set_execution_param_data(
        self, repository_handle, partition_set_name, partition_names
    ):
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")
        check.list_param(partition_names, "partition_names", of_type=str)

        return sync_get_external_partition_set_execution_param_data_grpc(
            self._handle.client, repository_handle, partition_set_name, partition_names
        )
