from abc import ABCMeta, abstractmethod, abstractproperty
from collections import namedtuple

import six

from dagster import check
from dagster.core.definitions.container import get_external_repository_from_image
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.execution.api import create_execution_plan, execute_plan
from dagster.core.host_representation import (
    ExternalExecutionPlan,
    ExternalPipeline,
    ExternalRepository,
)
from dagster.core.instance import DagsterInstance
from dagster.core.snap import snapshot_from_execution_plan
from dagster.core.storage.pipeline_run import PipelineRun

from .pipeline_execution_manager import PipelineExecutionManager
from .reloader import Reloader


# identify a pipeline with in a DagsterGraphQLContext
class PipelineHandle(
    namedtuple('_PipelineHandle', 'environment_name repository_name pipeline_name')
):
    def to_string(self):
        return '{self.environment_name}.{self.repository_name}.{self.pipeline_name}'.format(
            self=self
        )


class DagsterGraphQLContext:
    def __init__(self, instance, environments, version=None):
        self._instance = check.inst_param(instance, 'instance', DagsterInstance)
        self._environments = {}
        for env in check.list_param(environments, 'environments', DagsterEnvironment):
            check.invariant(
                self._environments.get(env.name) is None,
                'Can not have multiple environments with the same name, got multiple "{name}"'.format(
                    name=env.name
                ),
            )
            self._environments[env.name] = env
        self.version = version

    @property
    def instance(self):
        return self._instance

    def get_external_pipeline(self, handle, solid_subset):
        check.inst_param(handle, 'handle', PipelineHandle)
        return self._environments[handle.environment_name].get_external_pipeline(
            handle, solid_subset
        )

    # Legacy family of methods for assuming one in process environment with one repository

    @property
    def legacy_environment(self):
        check.invariant(len(self._environments) == 1, '[legacy] must have only one environment')
        return next(iter(self._environments.values()))

    @property
    def legacy_external_repository(self):
        repos = self.legacy_environment.get_repositories()
        check.invariant(len(repos) == 1, '[legacy] must have only one repository')
        return next(iter(repos.values()))

    def legacy_has_external_pipeline(self, name):
        check.str_param(name, 'name')
        return self.legacy_external_repository.has_pipeline(name)

    def legacy_get_full_external_pipeline(self, name):
        check.str_param(name, 'name')
        return self.legacy_external_repository.get_external_pipeline(name)

    def legacy_get_all_external_pipelines(self):
        return self.legacy_external_repository.get_all_external_pipelines()

    def legacy_get_external_pipeline(self, name, solid_subset):
        return self.legacy_environment.get_external_pipeline(
            PipelineHandle(
                environment_name=self.legacy_environment.name,
                repository_name=self.legacy_external_repository.name,
                pipeline_name=name,
            ),
            solid_subset,
        )

    def legacy_get_external_execution_plan(
        self, external_pipeline, environment_dict, mode, step_keys_to_execute
    ):
        return self.legacy_environment.get_external_execution_plan(
            external_pipeline, environment_dict, mode, step_keys_to_execute
        )

    def legacy_execute_plan(
        self, external_pipeline, environment_dict, pipeline_run, step_keys_to_execute
    ):
        return self.legacy_environment.execute_plan(
            self.instance, external_pipeline, environment_dict, pipeline_run, step_keys_to_execute
        )

    def legacy_execute_pipeline(self, external_pipeline, pipeline_run):
        return self.legacy_environment.execute_pipeline(
            self.instance, external_pipeline, pipeline_run
        )

    def legacy_get_repository_definition(self):
        check.invariant(
            isinstance(self.legacy_environment, InProcessDagsterEnvironment),
            '[legacy] must be in process env',
        )
        return self.legacy_environment.get_reconstructable_repository().get_definition()


class DagsterEnvironment(six.with_metaclass(ABCMeta)):
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


class DockerDagsterEnvironment(DagsterEnvironment):
    def __init__(self, name, image):
        self._name = check.str_param(name, 'name')
        self._image = check.str_param(image, 'image')

        external_repo = get_external_repository_from_image(image)
        self._repositories = {external_repo.name: external_repo}

    @property
    def name(self):
        return self._name

    def get_repository(self, name):
        return self._repositories[name]

    def get_repositories(self):
        return self._repositories

    def get_external_execution_plan(
        self, external_pipeline, environment_dict, mode, step_keys_to_execute
    ):
        raise NotImplementedError('Not yet supported out of process')

    def execute_plan(
        self, instance, external_pipeline, environment_dict, pipeline_run, step_keys_to_execute
    ):
        raise NotImplementedError('Not yet supported out of process')

    def execute_pipeline(self, instance, external_pipeline, pipeline_run):
        raise NotImplementedError('Not yet supported out of process')

    def get_external_pipeline(self, handle, solid_subset):
        raise NotImplementedError('Not yet supported out of process')


class InProcessDagsterEnvironment(DagsterEnvironment):
    def __init__(self, recon_repo, execution_manager, reloader=None):
        self._recon_repo = check.inst_param(recon_repo, 'recon_repo', ReconstructableRepository)
        external_repo = ExternalRepository.from_repository_def(recon_repo.get_definition())
        self._repositories = {external_repo.name: external_repo}
        self.execution_manager = check.inst_param(
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
        check.invariant(
            handle.environment_name == self.name,
            'Received invalid handle, environment name mismatch',
        )
        return ExternalPipeline.from_pipeline_def(
            self.get_reconstructable_pipeline(handle.pipeline_name).get_definition(), solid_subset
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
