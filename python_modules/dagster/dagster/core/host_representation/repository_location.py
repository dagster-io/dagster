from abc import ABCMeta, abstractmethod, abstractproperty

import six

from dagster import check
from dagster.api.snapshot_execution_plan import sync_get_external_execution_plan_grpc
from dagster.api.snapshot_partition import (
    sync_get_external_partition_config,
    sync_get_external_partition_config_grpc,
    sync_get_external_partition_names,
    sync_get_external_partition_names_grpc,
    sync_get_external_partition_tags,
    sync_get_external_partition_tags_grpc,
)
from dagster.api.snapshot_pipeline import sync_get_external_pipeline_subset_grpc
from dagster.api.snapshot_repository import (
    sync_get_external_repositories,
    sync_get_external_repositories_grpc,
)
from dagster.api.snapshot_schedule import (
    sync_get_external_schedule_execution_data,
    sync_get_external_schedule_execution_data_grpc,
)
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.execution.api import create_execution_plan, execute_plan, execute_run
from dagster.core.host_representation import (
    ExternalExecutionPlan,
    ExternalPipeline,
    ExternalPipelineExecutionResult,
    GrpcServerRepositoryLocationHandle,
    InProcessRepositoryLocationHandle,
    ManagedGrpcPythonEnvRepositoryLocationHandle,
    PipelineHandle,
    PythonEnvRepositoryLocationHandle,
    RepositoryHandle,
    RepositoryLocationHandle,
)
from dagster.core.instance import DagsterInstance
from dagster.core.snap.execution_plan_snapshot import (
    ExecutionPlanSnapshotErrorData,
    snapshot_from_execution_plan,
)
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.grpc.impl import (
    get_external_schedule_execution,
    get_partition_config,
    get_partition_names,
    get_partition_tags,
)
from dagster.grpc.types import (
    ExternalScheduleExecutionArgs,
    PartitionArgs,
    PartitionNamesArgs,
    ScheduleExecutionDataMode,
)
from dagster.utils.hosted_user_process import (
    external_repo_from_def,
    is_repository_location_in_same_python_env,
    recon_repository_from_origin,
)

from .selector import PipelineSelector


class RepositoryLocation(six.with_metaclass(ABCMeta)):
    '''
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
    '''

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
    def execute_plan(
        self,
        instance,
        external_pipeline,
        run_config,
        pipeline_run,
        step_keys_to_execute,
        retries=None,
    ):
        pass

    @abstractmethod
    def execute_pipeline(
        self, instance, external_pipeline, pipeline_run,
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
    def get_external_schedule_execution_data(
        self, instance, repository_handle, schedule_name, schedule_execution_data_mode
    ):
        pass

    @abstractproperty
    def is_reload_supported(self):
        pass

    @staticmethod
    def from_handle(repository_location_handle):
        check.inst_param(
            repository_location_handle, 'repository_location_handle', RepositoryLocationHandle
        )

        if isinstance(repository_location_handle, InProcessRepositoryLocationHandle):
            check.invariant(len(repository_location_handle.repository_code_pointer_dict) == 1)
            pointer = next(iter(repository_location_handle.repository_code_pointer_dict.values()))
            return InProcessRepositoryLocation(ReconstructableRepository(pointer))
        elif isinstance(repository_location_handle, PythonEnvRepositoryLocationHandle):
            return PythonEnvRepositoryLocation(repository_location_handle)
        elif isinstance(
            repository_location_handle, GrpcServerRepositoryLocationHandle
        ) or isinstance(repository_location_handle, ManagedGrpcPythonEnvRepositoryLocationHandle):
            return GrpcServerRepositoryLocation(repository_location_handle)
        else:
            check.failed('Unsupported handle: {}'.format(repository_location_handle))

    def create_reloaded_repository_location(self):
        return RepositoryLocation.from_handle(self.location_handle.create_reloaded_handle())


class InProcessRepositoryLocation(RepositoryLocation):
    def __init__(self, recon_repo):
        self._recon_repo = check.inst_param(recon_repo, 'recon_repo', ReconstructableRepository)
        self._handle = RepositoryLocationHandle.create_in_process_location(recon_repo.pointer)

        repo_def = recon_repo.get_definition()
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
        return self._recon_repo.get_reconstructable_pipeline(name)

    def get_reconstructable_repository(self):
        return self._recon_repo

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
        check.inst_param(selector, 'selector', PipelineSelector)
        check.invariant(
            selector.location_name == self.name,
            'PipelineSelector location_name mismatch, got {selector.location_name} expected {self.name}'.format(
                self=self, selector=selector
            ),
        )

        from dagster.cli.api import get_external_pipeline_subset_result

        return get_external_pipeline_subset_result(
            self.get_reconstructable_pipeline(selector.pipeline_name), selector.solid_selection
        )

    def get_external_execution_plan(
        self, external_pipeline, run_config, mode, step_keys_to_execute
    ):
        check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)
        check.dict_param(run_config, 'run_config')
        check.str_param(mode, 'mode')
        check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

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

    def execute_plan(
        self,
        instance,
        external_pipeline,
        run_config,
        pipeline_run,
        step_keys_to_execute,
        retries=None,
    ):
        check.inst_param(instance, 'instance', DagsterInstance)
        check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)
        check.dict_param(run_config, 'run_config')
        check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
        check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

        execution_plan = create_execution_plan(
            pipeline=self.get_reconstructable_pipeline(
                external_pipeline.name
            ).subset_for_execution_from_existing_pipeline(external_pipeline.solids_to_execute),
            run_config=run_config,
            mode=pipeline_run.mode,
            step_keys_to_execute=step_keys_to_execute,
        )

        execute_plan(
            execution_plan=execution_plan,
            instance=instance,
            pipeline_run=pipeline_run,
            run_config=run_config,
            retries=retries,
        )

    def execute_pipeline(
        self, instance, external_pipeline, pipeline_run,
    ):
        check.inst_param(instance, 'instance', DagsterInstance)
        check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)
        check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)

        pipeline = self.get_reconstructable_pipeline(
            external_pipeline.name
        ).subset_for_execution_from_existing_pipeline(external_pipeline.solids_to_execute)

        execution_result = execute_run(pipeline, pipeline_run, instance)

        return ExternalPipelineExecutionResult(event_list=execution_result.event_list)

    def get_external_partition_config(self, repository_handle, partition_set_name, partition_name):
        check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
        check.str_param(partition_set_name, 'partition_set_name')
        check.str_param(partition_name, 'partition_name')

        args = PartitionArgs(
            repository_origin=repository_handle.get_origin(),
            partition_set_name=partition_set_name,
            partition_name=partition_name,
        )
        return get_partition_config(args)

    def get_external_partition_tags(self, repository_handle, partition_set_name, partition_name):
        check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
        check.str_param(partition_set_name, 'partition_set_name')
        check.str_param(partition_name, 'partition_name')

        args = PartitionArgs(
            repository_origin=repository_handle.get_origin(),
            partition_set_name=partition_set_name,
            partition_name=partition_name,
        )
        return get_partition_tags(args)

    def get_external_partition_names(self, repository_handle, partition_set_name):
        check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
        check.str_param(partition_set_name, 'partition_set_name')

        args = PartitionNamesArgs(
            repository_origin=repository_handle.get_origin(), partition_set_name=partition_set_name
        )
        return get_partition_names(args)

    def get_external_schedule_execution_data(
        self, instance, repository_handle, schedule_name, schedule_execution_data_mode
    ):
        check.inst_param(instance, 'instance', DagsterInstance)
        check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
        check.str_param(schedule_name, 'schedule_name')
        check.inst_param(
            schedule_execution_data_mode, 'schedule_execution_data_mode', ScheduleExecutionDataMode
        )

        repo_origin = repository_handle.get_origin()
        args = ExternalScheduleExecutionArgs(
            instance_ref=instance.get_ref(),
            repository_origin=repo_origin,
            schedule_name=schedule_name,
            schedule_execution_data_mode=schedule_execution_data_mode,
        )
        recon_repo = recon_repository_from_origin(repo_origin)
        return get_external_schedule_execution(recon_repo, args)


class GrpcServerRepositoryLocation(RepositoryLocation):
    def __init__(self, repository_location_handle):
        check.param_invariant(
            isinstance(repository_location_handle, GrpcServerRepositoryLocationHandle)
            or isinstance(repository_location_handle, ManagedGrpcPythonEnvRepositoryLocationHandle),
            'repository_location_handle',
        )

        self._handle = repository_location_handle

        external_repositories_list = sync_get_external_repositories_grpc(
            self._handle.client, self._handle,
        )

        self.external_repositories = {repo.name: repo for repo in external_repositories_list}

    def create_reloaded_repository_location(self):
        return GrpcServerRepositoryLocation(self._handle)

    @property
    def is_reload_supported(self):
        return True

    def get_repository(self, name):
        check.str_param(name, 'name')
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
        check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)
        check.dict_param(run_config, 'run_config')
        check.str_param(mode, 'mode')
        check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

        execution_plan_snapshot_or_error = sync_get_external_execution_plan_grpc(
            api_client=self._handle.client,
            pipeline_origin=external_pipeline.get_origin(),
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

    def execute_plan(
        self,
        instance,
        external_pipeline,
        run_config,
        pipeline_run,
        step_keys_to_execute,
        retries=None,
    ):
        raise NotImplementedError('execute_plan is not implemented for grpc servers')

    def execute_pipeline(
        self, instance, external_pipeline, pipeline_run,
    ):
        from dagster.api.execute_run import sync_execute_run_grpc

        check.inst_param(instance, 'instance', DagsterInstance)
        check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)
        check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
        event_list = sync_execute_run_grpc(
            self._handle.client, instance.get_ref(), external_pipeline.get_origin(), pipeline_run
        )
        return ExternalPipelineExecutionResult(event_list=event_list)

    def get_subset_external_pipeline_result(self, selector):
        check.inst_param(selector, 'selector', PipelineSelector)
        check.invariant(
            selector.location_name == self.name,
            'PipelineSelector location_name mismatch, got {selector.location_name} expected {self.name}'.format(
                self=self, selector=selector
            ),
        )

        external_repository = self.external_repositories[selector.repository_name]
        pipeline_handle = PipelineHandle(selector.pipeline_name, external_repository.handle)
        return sync_get_external_pipeline_subset_grpc(
            self._handle.client, pipeline_handle.get_origin(), selector.solid_selection
        )

    def get_external_partition_config(self, repository_handle, partition_set_name, partition_name):
        check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
        check.str_param(partition_set_name, 'partition_set_name')
        check.str_param(partition_name, 'partition_name')

        return sync_get_external_partition_config_grpc(
            self._handle.client, repository_handle, partition_set_name, partition_name
        )

    def get_external_partition_tags(self, repository_handle, partition_set_name, partition_name):
        check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
        check.str_param(partition_set_name, 'partition_set_name')
        check.str_param(partition_name, 'partition_name')

        return sync_get_external_partition_tags_grpc(
            self._handle.client, repository_handle, partition_set_name, partition_name
        )

    def get_external_partition_names(self, repository_handle, partition_set_name):
        check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
        check.str_param(partition_set_name, 'partition_set_name')

        return sync_get_external_partition_names_grpc(
            self._handle.client, repository_handle, partition_set_name
        )

    def get_external_schedule_execution_data(
        self, instance, repository_handle, schedule_name, schedule_execution_data_mode
    ):
        check.inst_param(instance, 'instance', DagsterInstance)
        check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
        check.str_param(schedule_name, 'schedule_name')
        check.inst_param(
            schedule_execution_data_mode, 'schedule_execution_data_mode', ScheduleExecutionDataMode
        )

        return sync_get_external_schedule_execution_data_grpc(
            self._handle.client,
            instance,
            repository_handle,
            schedule_name,
            schedule_execution_data_mode,
        )


class PythonEnvRepositoryLocation(RepositoryLocation):
    def __init__(self, repository_location_handle):
        self._handle = check.inst_param(
            repository_location_handle,
            'repository_location_handle',
            PythonEnvRepositoryLocationHandle,
        )

        repo_list = sync_get_external_repositories(self._handle)
        self.external_repositories = {er.name: er for er in repo_list}

    def create_reloaded_repository_location(self):
        return PythonEnvRepositoryLocation(self._handle)

    @property
    def is_reload_supported(self):
        return True

    def get_repository(self, name):
        check.str_param(name, 'name')
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
        from dagster.api.snapshot_execution_plan import sync_get_external_execution_plan

        check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)
        check.dict_param(run_config, 'run_config')
        check.str_param(mode, 'mode')
        check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

        execution_plan_snapshot_or_error = sync_get_external_execution_plan(
            pipeline_origin=external_pipeline.get_origin(),
            solid_selection=external_pipeline.solid_selection,
            run_config=run_config,
            mode=mode,
            step_keys_to_execute=step_keys_to_execute,
            pipeline_snapshot_id=external_pipeline.identifying_pipeline_snapshot_id,
        )

        if isinstance(execution_plan_snapshot_or_error, ExecutionPlanSnapshotErrorData):
            return execution_plan_snapshot_or_error

        return ExternalExecutionPlan(
            execution_plan_snapshot=execution_plan_snapshot_or_error,
            represented_pipeline=external_pipeline,
        )

    def execute_plan(
        self,
        instance,
        external_pipeline,
        run_config,
        pipeline_run,
        step_keys_to_execute,
        retries=None,
    ):
        if (
            is_repository_location_in_same_python_env(self.location_handle)
            and len(self.location_handle.repository_code_pointer_dict) == 1
        ):
            check.inst_param(instance, 'instance', DagsterInstance)
            check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)
            check.dict_param(run_config, 'run_config')
            check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
            check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

            pointer = next(iter(self.location_handle.repository_code_pointer_dict.values()))
            recon_repo = ReconstructableRepository(pointer)

            execution_plan = create_execution_plan(
                pipeline=recon_repo.get_reconstructable_pipeline(
                    external_pipeline.name
                ).subset_for_execution_from_existing_pipeline(external_pipeline.solids_to_execute),
                run_config=run_config,
                mode=pipeline_run.mode,
                step_keys_to_execute=step_keys_to_execute,
            )

            execute_plan(
                execution_plan=execution_plan,
                instance=instance,
                pipeline_run=pipeline_run,
                run_config=run_config,
                retries=retries,
            )
        else:
            raise NotImplementedError(
                'execute_plan is currently only supported when the location is a python '
                'environment with the exact same executable and when there is only a single '
                'repository.'
            )

    def execute_pipeline(
        self, instance, external_pipeline, pipeline_run,
    ):
        from dagster.api.execute_run import cli_api_execute_run

        check.inst_param(instance, 'instance', DagsterInstance)
        check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)
        check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)

        event_list = cli_api_execute_run(
            instance=instance,
            pipeline_origin=external_pipeline.get_origin(),
            pipeline_run=pipeline_run,
        )

        return ExternalPipelineExecutionResult(event_list=event_list)

    def get_subset_external_pipeline_result(self, selector):
        from dagster.api.snapshot_pipeline import sync_get_external_pipeline_subset

        check.inst_param(selector, 'selector', PipelineSelector)
        check.invariant(
            selector.location_name == self.name,
            'PipelineSelector location_name mismatch, got {selector.location_name} expected {self.name}'.format(
                self=self, selector=selector
            ),
        )

        external_repository = self.external_repositories[selector.repository_name]
        pipeline_handle = PipelineHandle(selector.pipeline_name, external_repository.handle)
        return sync_get_external_pipeline_subset(
            pipeline_handle.get_origin(), selector.solid_selection
        )

    def get_external_partition_config(self, repository_handle, partition_set_name, partition_name):
        check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
        check.str_param(partition_set_name, 'partition_set_name')
        check.str_param(partition_name, 'partition_name')

        return sync_get_external_partition_config(
            repository_handle, partition_set_name, partition_name
        )

    def get_external_partition_tags(self, repository_handle, partition_set_name, partition_name):
        check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
        check.str_param(partition_set_name, 'partition_set_name')
        check.str_param(partition_name, 'partition_name')

        return sync_get_external_partition_tags(
            repository_handle, partition_set_name, partition_name
        )

    def get_external_partition_names(self, repository_handle, partition_set_name):
        check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
        check.str_param(partition_set_name, 'partition_set_name')

        return sync_get_external_partition_names(repository_handle, partition_set_name)

    def get_external_schedule_execution_data(
        self, instance, repository_handle, schedule_name, schedule_execution_data_mode
    ):
        check.inst_param(instance, 'instance', DagsterInstance)
        check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
        check.str_param(schedule_name, 'schedule_name')
        check.inst_param(
            schedule_execution_data_mode, 'schedule_execution_data_mode', ScheduleExecutionDataMode
        )

        return sync_get_external_schedule_execution_data(
            instance, repository_handle, schedule_name, schedule_execution_data_mode
        )
