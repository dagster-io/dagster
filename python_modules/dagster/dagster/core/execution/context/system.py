'''
This module contains the execution context objects that are internal to the system.
Not every property on these should be exposed to random Jane or Joe dagster user
so we have a different layer of objects that encode the explicit public API
in the user_context module
'''
from collections import namedtuple

from dagster import check
from dagster.core.definitions.handle import ExecutionTargetHandle
from dagster.core.definitions.mode import ModeDefinition
from dagster.core.definitions.resource import ScopedResourcesBuilder
from dagster.core.log_manager import DagsterLogManager
from dagster.core.storage.file_manager import FileManager
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.system_config.objects import EnvironmentConfig
from dagster.utils import merge_dicts


class SystemPipelineExecutionContextData(
    namedtuple(
        '_SystemPipelineExecutionContextData',
        (
            'pipeline_run scoped_resources_builder environment_config pipeline_def '
            'mode_def system_storage_def instance intermediates_manager file_manager '
            'execution_target_handle executor_config raise_on_error'
        ),
    )
):
    '''
    SystemPipelineExecutionContextData is the data that remains constant throughout the entire
    execution of a pipeline.
    '''

    def __new__(
        cls,
        pipeline_run,
        scoped_resources_builder,
        environment_config,
        pipeline_def,
        mode_def,
        system_storage_def,
        instance,
        intermediates_manager,
        file_manager,
        execution_target_handle,
        executor_config,
        raise_on_error,
    ):
        from dagster.core.definitions import PipelineDefinition
        from dagster.core.definitions.system_storage import SystemStorageDefinition
        from dagster.core.execution.config import ExecutorConfig
        from dagster.core.storage.intermediates_manager import IntermediatesManager
        from dagster.core.instance import DagsterInstance

        return super(SystemPipelineExecutionContextData, cls).__new__(
            cls,
            pipeline_run=check.inst_param(pipeline_run, 'pipeline_run', PipelineRun),
            scoped_resources_builder=check.inst_param(
                scoped_resources_builder, 'scoped_resources_builder', ScopedResourcesBuilder
            ),
            environment_config=check.inst_param(
                environment_config, 'environment_config', EnvironmentConfig
            ),
            pipeline_def=check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition),
            mode_def=check.inst_param(mode_def, 'mode_def', ModeDefinition),
            system_storage_def=check.inst_param(
                system_storage_def, 'system_storage_def', SystemStorageDefinition
            ),
            instance=check.inst_param(instance, 'instance', DagsterInstance),
            intermediates_manager=check.inst_param(
                intermediates_manager, 'intermediates_manager', IntermediatesManager
            ),
            file_manager=check.inst_param(file_manager, 'file_manager', FileManager),
            execution_target_handle=check.opt_inst_param(
                execution_target_handle, 'execution_target_handle', ExecutionTargetHandle
            ),
            executor_config=check.inst_param(executor_config, 'executor_config', ExecutorConfig),
            raise_on_error=check.bool_param(raise_on_error, 'raise_on_error'),
        )

    @property
    def run_id(self):
        return self.pipeline_run.run_id

    @property
    def environment_dict(self):
        return self.environment_config.original_config_dict


class SystemPipelineExecutionContext(object):
    __slots__ = ['_pipeline_context_data', '_log_manager']

    def __init__(self, pipeline_context_data, log_manager):
        self._pipeline_context_data = check.inst_param(
            pipeline_context_data, 'pipeline_context_data', SystemPipelineExecutionContextData
        )
        self._log_manager = check.inst_param(log_manager, 'log_manager', DagsterLogManager)

    def for_step(self, step):
        from dagster.core.execution.plan.objects import ExecutionStep

        check.inst_param(step, 'step', ExecutionStep)

        return SystemStepExecutionContext(
            self._pipeline_context_data,
            DagsterLogManager(
                self.run_id, merge_dicts(self.logging_tags, step.logging_tags), self.log.loggers
            ),
            step,
        )

    def for_type(self, dagster_type):
        return TypeCheckContext(self._pipeline_context_data, self.log, dagster_type)

    @property
    def executor_config(self):
        return self._pipeline_context_data.executor_config

    @property
    def pipeline_run(self):
        return self._pipeline_context_data.pipeline_run

    @property
    def scoped_resources_builder(self):
        return self._pipeline_context_data.scoped_resources_builder

    @property
    def run_id(self):
        return self._pipeline_context_data.run_id

    @property
    def environment_dict(self):
        return self._pipeline_context_data.environment_dict

    @property
    def environment_config(self):
        return self._pipeline_context_data.environment_config

    @property
    def logging_tags(self):
        return self._log_manager.logging_tags

    def has_tag(self, key):
        check.str_param(key, 'key')
        return key in self.logging_tags

    def get_tag(self, key):
        check.str_param(key, 'key')
        return self.logging_tags[key]

    @property
    def pipeline_def(self):
        return self._pipeline_context_data.pipeline_def

    @property
    def mode_def(self):
        return self._pipeline_context_data.mode_def

    @property
    def system_storage_def(self):
        return self._pipeline_context_data.system_storage_def

    @property
    def log(self):
        return self._log_manager

    @property
    def instance(self):
        return self._pipeline_context_data.instance

    @property
    def intermediates_manager(self):
        return self._pipeline_context_data.intermediates_manager

    @property
    def file_manager(self):
        return self._pipeline_context_data.file_manager

    @property
    def execution_target_handle(self):
        return self._pipeline_context_data.execution_target_handle

    @property
    def raise_on_error(self):
        return self._pipeline_context_data.raise_on_error


class SystemStepExecutionContext(SystemPipelineExecutionContext):
    __slots__ = ['_step', '_resources', '_required_resource_keys']

    def __init__(self, pipeline_context_data, log_manager, step):
        from dagster.core.execution.plan.objects import ExecutionStep
        from dagster.core.execution.resources_init import get_required_resource_keys_for_step

        self._step = check.inst_param(step, 'step', ExecutionStep)
        super(SystemStepExecutionContext, self).__init__(pipeline_context_data, log_manager)
        self._required_resource_keys = get_required_resource_keys_for_step(
            step, pipeline_context_data.pipeline_def, pipeline_context_data.system_storage_def,
        )
        self._resources = self._pipeline_context_data.scoped_resources_builder.build(
            self._required_resource_keys
        )
        self._log_manager = log_manager

    def for_compute(self):
        return SystemComputeExecutionContext(self._pipeline_context_data, self.log, self.step)

    @property
    def step(self):
        return self._step

    @property
    def solid_handle(self):
        return self._step.solid_handle

    @property
    def solid_def(self):
        return self.solid.definition

    @property
    def solid(self):
        return self.pipeline_def.get_solid(self._step.solid_handle)

    @property
    def resources(self):
        return self._resources

    @property
    def required_resource_keys(self):
        return self._required_resource_keys

    @property
    def log(self):
        return self._log_manager


class SystemComputeExecutionContext(SystemStepExecutionContext):
    @property
    def solid_config(self):
        solid_config = self.environment_config.solids.get(str(self.solid_handle))
        return solid_config.config if solid_config else None


class TypeCheckContext(SystemPipelineExecutionContext):
    '''The ``context`` object available to a type check function on a DagsterType.

    Attributes:
        log (DagsterLogManager): Centralized log dispatch from user code.
        resources (Any): An object whose attributes contain the resources available to this solid.
        run_id (str): The id of this pipeline run.
    '''

    def __init__(self, pipeline_context_data, log_manager, dagster_type):
        super(TypeCheckContext, self).__init__(pipeline_context_data, log_manager)
        self._resources = self._pipeline_context_data.scoped_resources_builder.build(
            dagster_type.required_resource_keys
        )
        self._log_manager = log_manager

    @property
    def resources(self):
        return self._resources
