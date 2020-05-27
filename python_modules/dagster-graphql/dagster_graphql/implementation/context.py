from abc import ABCMeta, abstractmethod, abstractproperty

import six

from dagster import check
from dagster.api.snapshot_repository import sync_get_external_repository
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.execution.api import create_execution_plan, execute_plan
from dagster.core.host_representation import (
    ExternalExecutionPlan,
    ExternalPipeline,
    PipelineHandle,
    RepositoryHandle,
)
from dagster.core.instance import DagsterInstance
from dagster.core.snap import snapshot_from_execution_plan
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.utils.hosted_user_process import (
    external_pipeline_from_recon_pipeline,
    external_repo_from_recon_repo,
)

from .pipeline_execution_manager import PipelineExecutionManager
from .reloader import Reloader


class DagsterGraphQLContext:
    def __init__(self, instance, locations, version=None):
        self._instance = check.inst_param(instance, 'instance', DagsterInstance)
        self._repository_locations = {}
        for loc in check.list_param(locations, 'locations', RepositoryLocation):
            check.invariant(
                self._repository_locations.get(loc.name) is None,
                'Can not have multiple locations with the same name, got multiple "{name}"'.format(
                    name=loc.name
                ),
            )
            self._repository_locations[loc.name] = loc
        self.version = version

    @property
    def instance(self):
        return self._instance

    def get_external_pipeline(self, handle, solid_subset):
        check.inst_param(handle, 'handle', PipelineHandle)
        return self._repository_locations[handle.location_name].get_external_pipeline(
            handle, solid_subset
        )

    # Legacy family of methods for assuming one in process location with one repository

    @property
    def legacy_location(self):
        check.invariant(
            len(self._repository_locations) == 1, '[legacy] must have only one location'
        )
        return next(iter(self._repository_locations.values()))

    @property
    def legacy_external_repository(self):
        repos = self.legacy_location.get_repositories()
        check.invariant(len(repos) == 1, '[legacy] must have only one repository')
        return next(iter(repos.values()))

    def legacy_has_external_pipeline(self, name):
        check.str_param(name, 'name')
        return self.legacy_external_repository.has_pipeline(name)

    def legacy_get_full_external_pipeline(self, name):
        check.str_param(name, 'name')
        return self.legacy_external_repository.get_full_external_pipeline(name)

    def legacy_get_all_external_pipelines(self):
        return self.legacy_external_repository.get_all_external_pipelines()

    def legacy_get_external_pipeline(self, name, solid_subset):
        return self.legacy_location.get_external_pipeline(
            PipelineHandle(name, self.legacy_external_repository.handle), solid_subset
        )

    def legacy_get_external_execution_plan(
        self, external_pipeline, environment_dict, mode, step_keys_to_execute
    ):
        return self.legacy_location.get_external_execution_plan(
            external_pipeline, environment_dict, mode, step_keys_to_execute
        )

    def legacy_execute_plan(
        self, external_pipeline, environment_dict, pipeline_run, step_keys_to_execute
    ):
        return self.legacy_location.execute_plan(
            self.instance, external_pipeline, environment_dict, pipeline_run, step_keys_to_execute
        )

    def legacy_execute_pipeline(self, external_pipeline, pipeline_run):
        return self.legacy_location.execute_pipeline(self.instance, external_pipeline, pipeline_run)

    def legacy_get_repository_definition(self):
        check.invariant(
            isinstance(self.legacy_location, InProcessRepositoryLocation),
            '[legacy] must be in process loc',
        )
        return self.legacy_location.get_reconstructable_repository().get_definition()

    def drain_outstanding_executions(self):
        '''
        This ensures that any outstanding executions of runs are waited on.
        Useful for tests contexts when you want to ensure a started run
        has ended in order to verify its results.
        '''
        if self.legacy_location.execution_manager:
            self.legacy_location.execution_manager.join()

        if self.instance.run_launcher:
            self.instance.run_launcher.join()


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
    def get_repositories(self):
        pass

    @abstractproperty
    def name(self):
        pass

    @abstractmethod
    def get_external_execution_plan(
        self, external_pipeline, environment_dict, mode, step_keys_to_execute
    ):
        pass

    @abstractmethod
    def execute_plan(
        self, instance, external_pipeline, environment_dict, pipeline_run, step_keys_to_execute
    ):
        pass

    @abstractmethod
    def execute_pipeline(self, instance, external_pipeline, pipeline_run):
        pass

    @abstractmethod
    def get_external_pipeline(self, handle, solid_subset):
        pass


class InProcessRepositoryLocation(RepositoryLocation):
    def __init__(self, recon_repo, execution_manager, reloader=None):

        self._recon_repo = check.inst_param(recon_repo, 'recon_repo', ReconstructableRepository)
        self._external_repo = external_repo_from_recon_repo(recon_repo)
        self._repositories = {self._external_repo.name: self._external_repo}
        self.execution_manager = check.opt_inst_param(
            execution_manager, 'pipeline_execution_manager', PipelineExecutionManager
        )
        self.reloader = check.opt_inst_param(reloader, 'reloader', Reloader)

    def get_reconstructable_pipeline(self, name):
        return self._recon_repo.get_reconstructable_pipeline(name)

    def get_reconstructable_repository(self):
        return self._recon_repo

    @property
    def is_reload_supported(self):
        return self.reloader and self.reloader.is_reload_supported

    @property
    def name(self):
        return '<<in_process>>'

    def get_repository(self, name):
        return self._repositories[name]

    def get_repositories(self):
        return self._repositories

    def get_external_pipeline(self, handle, solid_subset):
        check.inst_param(handle, 'handle', PipelineHandle)
        return external_pipeline_from_recon_pipeline(
            recon_pipeline=self.get_reconstructable_pipeline(handle.pipeline_name),
            solid_subset=solid_subset,
        )

    def get_external_execution_plan(
        self, external_pipeline, environment_dict, mode, step_keys_to_execute
    ):
        check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)
        check.dict_param(environment_dict, 'environment_dict')
        check.str_param(mode, 'mode')
        check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

        return ExternalExecutionPlan(
            execution_plan_snapshot=snapshot_from_execution_plan(
                create_execution_plan(
                    pipeline=self.get_reconstructable_pipeline(
                        external_pipeline.name
                    ).subset_for_execution(external_pipeline.solid_subset),
                    environment_dict=environment_dict,
                    mode=mode,
                    step_keys_to_execute=step_keys_to_execute,
                ),
                external_pipeline.identifying_pipeline_snapshot_id,
            ),
            represented_pipeline=external_pipeline,
        )

    def execute_plan(
        self, instance, external_pipeline, environment_dict, pipeline_run, step_keys_to_execute
    ):
        check.inst_param(instance, 'instance', DagsterInstance)
        check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)
        check.dict_param(environment_dict, 'environment_dict')
        check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
        check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

        execution_plan = create_execution_plan(
            pipeline=self.get_reconstructable_pipeline(external_pipeline.name),
            environment_dict=environment_dict,
            mode=pipeline_run.mode,
            step_keys_to_execute=step_keys_to_execute,
        )

        execute_plan(
            execution_plan=execution_plan,
            instance=instance,
            pipeline_run=pipeline_run,
            environment_dict=environment_dict,
        )

    def execute_pipeline(self, instance, external_pipeline, pipeline_run):
        check.inst_param(instance, 'instance', DagsterInstance)
        check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)
        check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
        self.execution_manager.execute_pipeline(
            self.get_reconstructable_pipeline(external_pipeline.name).subset_for_execution(
                pipeline_run.solid_subset
            ),
            pipeline_run,
            instance=instance,
        )


class OutOfProcessRepositoryLocation(RepositoryLocation):
    def __init__(self, name, repository_handle):
        check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
        check.param_invariant(
            repository_handle.location_handle.in_process_origin.repo_yaml,
            'location_handle',
            'Must have repo_yaml for now because dagster cli api only supports that',
        )
        self._name = check.str_param(name, 'name')
        self.external_repository = sync_get_external_repository(repository_handle)

    @property
    def execution_manager(self):
        return None

    def get_repository(self, name):
        check.str_param(name, 'name')
        check.param_invariant(name == self.external_repository.name, 'name')
        return self.external_repository

    def get_repositories(self):
        return {self.external_repository.name: self.external_repository}

    @property
    def name(self):
        return self._name

    def get_external_execution_plan(
        self, external_pipeline, environment_dict, mode, step_keys_to_execute
    ):
        raise NotImplementedError()

    def execute_plan(
        self, instance, external_pipeline, environment_dict, pipeline_run, step_keys_to_execute
    ):
        raise NotImplementedError()

    def execute_pipeline(self, instance, external_pipeline, pipeline_run):
        raise NotImplementedError()

    def get_external_pipeline(self, handle, solid_subset):
        raise NotImplementedError()
