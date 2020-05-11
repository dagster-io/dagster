import abc

import six

from dagster import ExecutionTargetHandle, check
from dagster.core.definitions.partition import PartitionScheduleDefinition
from dagster.core.execution.api import create_execution_plan, execute_plan
from dagster.core.instance import DagsterInstance
from dagster.core.snap import (
    ActiveRepositoryData,
    ExecutionPlanIndex,
    RepositoryIndex,
    active_repository_data_from_def,
    snapshot_from_execution_plan,
)
from dagster.core.storage.pipeline_run import PipelineRun

from .external import ExternalPipeline
from .pipeline_execution_manager import PipelineExecutionManager
from .reloader import Reloader


class DagsterGraphQLContext(six.with_metaclass(abc.ABCMeta)):
    def __init__(self, active_repository_data, instance):
        self.active_repository_data = check.inst_param(
            active_repository_data, 'active_repository_data', ActiveRepositoryData
        )
        self._repository_index = RepositoryIndex(active_repository_data)
        self._instance = check.inst_param(instance, 'instance', DagsterInstance)

    def get_repository_index(self):
        return self._repository_index

    @property
    def instance(self):
        return self._instance

    @abc.abstractproperty
    def is_reload_supported(self):
        pass

    def has_external_pipeline(self, name):
        check.str_param(name, 'name')
        return self._repository_index.has_pipeline(name)

    def get_external_pipeline(self, name):
        check.str_param(name, 'name')
        return ExternalPipeline(
            self._repository_index.get_pipeline_index(name),
            self.active_repository_data.get_active_pipeline_data(name),
            solid_subset=None,
        )

    def get_all_external_pipelines(self):
        return list(
            map(
                lambda pi: ExternalPipeline(
                    pi, self.active_repository_data.get_active_pipeline_data(pi.name)
                ),
                self._repository_index.get_pipeline_indices(),
            )
        )

    @abc.abstractmethod
    def get_external_pipeline_subset(self, name, solid_subset):
        pass

    @abc.abstractmethod
    def create_execution_plan_index(
        self, external_pipeline, environment_dict, mode, step_keys_to_execute
    ):
        pass

    @abc.abstractmethod
    def execute_plan(self, external_pipeline, environment_dict, pipeline_run, step_keys_to_execute):
        pass

    @abc.abstractmethod
    def execute_pipeline(self, external_pipeline, pipeline_run):
        pass


class DagsterGraphQLOutOfProcessRepositoryContext(DagsterGraphQLContext):
    def __init__(self, active_repository_data, execution_manager, instance, version=None):
        super(DagsterGraphQLOutOfProcessRepositoryContext, self).__init__(
            active_repository_data=active_repository_data, instance=instance
        )
        self.execution_manager = check.inst_param(
            execution_manager, 'pipeline_execution_manager', PipelineExecutionManager
        )
        self.version = version

    @property
    def is_reload_supported(self):
        return False

    def get_external_pipeline_subset(self, name, solid_subset):
        raise NotImplementedError('Not yet supported out of process')

    def create_execution_plan_index(
        self, external_pipeline, environment_dict, mode, step_keys_to_execute
    ):
        raise NotImplementedError('Not yet supported out of process')

    def execute_plan(self, external_pipeline, environment_dict, pipeline_run, step_keys_to_execute):
        raise NotImplementedError('Not yet supported out of process')

    def execute_pipeline(self, external_pipeline, pipeline_run):
        raise NotImplementedError('Not yet supported out of process')


class DagsterGraphQLInProcessRepositoryContext(DagsterGraphQLContext):
    def __init__(self, handle, execution_manager, instance, reloader=None, version=None):
        self.repository_definition = handle.build_repository_definition()
        super(DagsterGraphQLInProcessRepositoryContext, self).__init__(
            active_repository_data=active_repository_data_from_def(self.repository_definition),
            instance=instance,
        )
        self._handle = check.inst_param(handle, 'handle', ExecutionTargetHandle)
        self.reloader = check.opt_inst_param(reloader, 'reloader', Reloader)
        self.execution_manager = check.inst_param(
            execution_manager, 'pipeline_execution_manager', PipelineExecutionManager
        )
        self.version = version
        self._cached_pipelines = {}

    def get_handle(self):
        return self._handle

    def get_partition_set(self, partition_set_name):
        return next(
            (
                partition_set
                for partition_set in self.get_all_partition_sets()
                if partition_set.name == partition_set_name
            ),
            None,
        )

    def get_all_partition_sets(self):
        return self.repository_definition.partition_set_defs + [
            schedule_def.get_partition_set()
            for schedule_def in self.repository_definition.schedule_defs
            if isinstance(schedule_def, PartitionScheduleDefinition)
        ]

    def get_repository(self):
        return self.repository_definition

    def get_pipeline(self, pipeline_name, solid_subset=None):
        if not pipeline_name in self._cached_pipelines:
            self._cached_pipelines[pipeline_name] = self._build_pipeline(pipeline_name)

        cached_full_pipeline = self._cached_pipelines[pipeline_name]

        if solid_subset:
            return cached_full_pipeline.build_sub_pipeline(solid_subset)
        else:
            return cached_full_pipeline

    def _build_pipeline(self, pipeline_name):
        orig_handle = self.get_handle()
        if orig_handle.is_resolved_to_pipeline:
            pipeline_def = orig_handle.build_pipeline_definition()
            check.invariant(
                pipeline_def.name == pipeline_name,
                '''Dagster GraphQL Context resolved pipeline with name {handle_pipeline_name},
                couldn't resolve {pipeline_name}'''.format(
                    handle_pipeline_name=pipeline_def.name, pipeline_name=pipeline_name
                ),
            )
            return pipeline_def
        return self.get_handle().with_pipeline_name(pipeline_name).build_pipeline_definition()

    @property
    def is_reload_supported(self):
        return self.reloader and self.reloader.is_reload_supported

    def get_external_pipeline_subset(self, name, solid_subset):
        check.str_param(name, 'name')
        check.list_param(solid_subset, 'solid_subset', of_type=str)

        return ExternalPipeline.from_pipeline_def(
            self.get_pipeline(name), solid_subset=solid_subset
        )

    def create_execution_plan_index(
        self, external_pipeline, environment_dict, mode, step_keys_to_execute=None
    ):
        check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)
        check.dict_param(environment_dict, 'environment_dict')
        check.str_param(mode, 'mode')
        check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

        return ExecutionPlanIndex(
            execution_plan_snapshot=snapshot_from_execution_plan(
                create_execution_plan(
                    pipeline=self.get_pipeline(
                        external_pipeline.name, external_pipeline.solid_subset
                    ),
                    environment_dict=environment_dict,
                    mode=mode,
                    step_keys_to_execute=step_keys_to_execute,
                ),
                external_pipeline.pipeline_snapshot_id,
            ),
            pipeline_index=external_pipeline.pipeline_index,
        )

    def execute_plan(self, external_pipeline, environment_dict, pipeline_run, step_keys_to_execute):
        check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)
        check.dict_param(environment_dict, 'environment_dict')
        check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
        check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

        execution_plan = create_execution_plan(
            pipeline=self.get_pipeline(external_pipeline.name),
            environment_dict=environment_dict,
            mode=pipeline_run.mode,
            step_keys_to_execute=step_keys_to_execute,
        )

        execute_plan(
            execution_plan=execution_plan,
            instance=self.instance,
            pipeline_run=pipeline_run,
            environment_dict=environment_dict,
        )

    def execute_pipeline(self, external_pipeline, pipeline_run):
        check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)
        check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
        self.execution_manager.execute_pipeline(
            self.get_handle(),
            self.get_pipeline(external_pipeline.name).build_sub_pipeline(pipeline_run.solid_subset)
            if pipeline_run.solid_subset
            else self.get_pipeline(external_pipeline.name),
            pipeline_run,
            instance=self.instance,
        )
