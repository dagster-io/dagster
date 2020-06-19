from abc import ABCMeta, abstractmethod, abstractproperty

import six

from dagster import check
from dagster.api.snapshot_repository import sync_get_external_repositories
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.execution.api import create_execution_plan, execute_plan
from dagster.core.host_representation import (
    ExternalExecutionPlan,
    ExternalPipeline,
    InProcessRepositoryLocationHandle,
    PipelineHandle,
    PythonEnvRepositoryLocationHandle,
    RepositoryHandle,
    RepositoryLocationHandle,
)
from dagster.core.instance import DagsterInstance
from dagster.core.snap.execution_plan_snapshot import snapshot_from_execution_plan
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.utils.hosted_user_process import (
    external_repo_from_def,
    is_repository_location_in_same_python_env,
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
    def get_subset_external_pipeline_result(self, selector):
        pass

    @abstractmethod
    def create_reloaded_repository_location(self):
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
        else:
            check.failed('Unsupported handle: {}'.format(repository_location_handle))


class InProcessRepositoryLocation(RepositoryLocation):
    def __init__(self, recon_repo):
        self._recon_repo = check.inst_param(recon_repo, 'recon_repo', ReconstructableRepository)
        self._handle = RepositoryLocationHandle.create_in_process_location(recon_repo.pointer)

        repo_def = recon_repo.get_definition()
        def_name = repo_def.name
        self._external_repo = external_repo_from_def(
            repo_def,
            RepositoryHandle(
                repository_name=def_name,
                repository_key=def_name,
                repository_location_handle=self._handle,
            ),
        )
        self._repositories = {self._external_repo.name: self._external_repo}

    def create_reloaded_repository_location(self):
        raise NotImplementedError('Not implemented for in-process')

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
            pipeline=self.get_reconstructable_pipeline(external_pipeline.name),
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


class PythonEnvRepositoryLocation(RepositoryLocation):
    def __init__(self, repository_location_handle):
        self._handle = check.inst_param(
            repository_location_handle,
            'repository_location_handle',
            PythonEnvRepositoryLocationHandle,
        )
        self.external_repositories = {
            er.name: er for er in sync_get_external_repositories(self._handle)
        }

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

        execution_plan_snapshot = sync_get_external_execution_plan(
            pipeline_origin=external_pipeline.get_origin(),
            solid_selection=external_pipeline.solid_selection,
            run_config=run_config,
            mode=mode,
            step_keys_to_execute=step_keys_to_execute,
            pipeline_snapshot_id=external_pipeline.identifying_pipeline_snapshot_id,
        )

        return ExternalExecutionPlan(
            execution_plan_snapshot=execution_plan_snapshot, represented_pipeline=external_pipeline,
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
                pipeline=recon_repo.get_reconstructable_pipeline(external_pipeline.name),
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

    def execute_pipeline(self, instance, external_pipeline, pipeline_run):
        raise NotImplementedError()

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
