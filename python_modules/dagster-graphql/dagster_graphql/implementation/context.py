import abc

import six

from dagster import ExecutionTargetHandle, check
from dagster.core.definitions.partition import PartitionScheduleDefinition
from dagster.core.instance import DagsterInstance
from dagster.core.snap import (
    ActivePipelineData,
    ActiveRepositoryData,
    PipelineIndex,
    RepositoryIndex,
    active_pipeline_data_from_def,
    active_repository_data_from_def,
)

from .pipeline_execution_manager import PipelineExecutionManager
from .reloader import Reloader


# Represents a pipeline definition that is resident in an external process.
#
# Object composes a pipeline index (which is an index over snapshot data)
# and the serialized ActivePipelineData
class ExternalPipeline:
    def __init__(self, pipeline_index, active_pipeline_data):
        self.pipeline_index = check.inst_param(pipeline_index, 'pipeline_index', PipelineIndex)
        self._active_pipeline_data = check.inst_param(
            active_pipeline_data, 'active_pipeline_data', ActivePipelineData
        )

    @property
    def name(self):
        return self.pipeline_index.name

    @property
    def active_presets(self):
        return self._active_pipeline_data.active_presets

    def has_solid_invocation(self, solid_name):
        return self.pipeline_index.has_solid_invocation(solid_name)

    @staticmethod
    def from_pipeline_def(pipeline_def):
        return ExternalPipeline(
            pipeline_def.get_pipeline_index(), active_pipeline_data_from_def(pipeline_def)
        )


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

    def get_pipeline(self, pipeline_name):
        if not pipeline_name in self._cached_pipelines:
            self._cached_pipelines[pipeline_name] = self._build_pipeline(pipeline_name)

        return self._cached_pipelines[pipeline_name]

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
            self.get_pipeline(name).build_sub_pipeline(solid_subset)
        )
