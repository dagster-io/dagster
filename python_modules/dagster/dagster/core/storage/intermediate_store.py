from abc import ABCMeta

import six

from dagster import check
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.types.dagster_type import DagsterType, resolve_dagster_type

from .object_store import FilesystemObjectStore, ObjectStore
from .type_storage import TypeStoragePluginRegistry


class IntermediateStore(six.with_metaclass(ABCMeta)):
    def __init__(self, object_store, root_for_run_id, run_id, type_storage_plugin_registry):
        self.root_for_run_id = check.callable_param(root_for_run_id, 'root_for_run_id')
        self.run_id = check.str_param(run_id, 'run_id')
        self.object_store = check.inst_param(object_store, 'object_store', ObjectStore)
        self.type_storage_plugin_registry = check.inst_param(
            type_storage_plugin_registry, 'type_storage_plugin_registry', TypeStoragePluginRegistry
        )

    @property
    def root(self):
        return self.root_for_run_id(self.run_id)

    def uri_for_paths(self, paths, protocol=None):
        check.list_param(paths, 'paths', of_type=str)
        check.param_invariant(len(paths) > 0, 'paths')
        key = self.key_for_paths(paths)
        return self.object_store.uri_for_key(key, protocol)

    def key_for_paths(self, paths):
        return self.object_store.key_for_paths([self.root] + paths)

    def set_object(self, obj, context, dagster_type, paths):
        check.opt_inst_param(context, 'context', SystemPipelineExecutionContext)
        check.inst_param(dagster_type, 'dagster_type', DagsterType)
        check.list_param(paths, 'paths', of_type=str)
        check.param_invariant(len(paths) > 0, 'paths')
        key = self.object_store.key_for_paths([self.root] + paths)
        return self.object_store.set_object(
            key, obj, serialization_strategy=dagster_type.serialization_strategy
        )

    def get_object(self, context, dagster_type, paths):
        check.opt_inst_param(context, 'context', SystemPipelineExecutionContext)
        check.list_param(paths, 'paths', of_type=str)
        check.param_invariant(len(paths) > 0, 'paths')
        check.inst_param(dagster_type, 'dagster_type', DagsterType)
        key = self.object_store.key_for_paths([self.root] + paths)
        return self.object_store.get_object(
            key, serialization_strategy=dagster_type.serialization_strategy
        )

    def has_object(self, context, paths):
        check.opt_inst_param(context, 'context', SystemPipelineExecutionContext)
        check.list_param(paths, 'paths', of_type=str)
        check.param_invariant(len(paths) > 0, 'paths')
        key = self.object_store.key_for_paths([self.root] + paths)
        return self.object_store.has_object(key)

    def rm_object(self, context, paths):
        check.opt_inst_param(context, 'context', SystemPipelineExecutionContext)
        check.list_param(paths, 'paths', of_type=str)
        check.param_invariant(len(paths) > 0, 'paths')
        key = self.object_store.key_for_paths([self.root] + paths)
        self.object_store.rm_object(key)

    def copy_object_from_prev_run(self, _context, previous_run_id, paths):
        check.str_param(previous_run_id, 'previous_run_id')
        check.list_param(paths, 'paths', of_type=str)
        check.param_invariant(len(paths) > 0, 'paths')

        src = self.object_store.key_for_paths([self.root_for_run_id(previous_run_id)] + paths)
        dst = self.object_store.key_for_paths([self.root] + paths)

        return self.object_store.cp_object(src, dst)

    def set_value(self, obj, context, dagster_type, paths):
        if self.type_storage_plugin_registry.is_registered(dagster_type):
            return self.type_storage_plugin_registry.get(dagster_type.name).set_object(
                self, obj, context, dagster_type, paths
            )
        elif dagster_type.name is None:
            self.type_storage_plugin_registry.check_for_unsupported_composite_overrides(
                dagster_type
            )

        return self.set_object(obj, context, dagster_type, paths)

    def get_value(self, context, dagster_type, paths):
        if self.type_storage_plugin_registry.is_registered(dagster_type):
            return self.type_storage_plugin_registry.get(dagster_type.name).get_object(
                self, context, dagster_type, paths
            )
        elif dagster_type.name is None:
            self.type_storage_plugin_registry.check_for_unsupported_composite_overrides(
                dagster_type
            )
        return self.get_object(context, dagster_type, paths)

    @staticmethod
    def paths_for_intermediate(step_key, output_name):
        return ['intermediates', step_key, output_name]

    def get_intermediate(self, context, step_key, dagster_type, output_name='result'):
        return self.get_object(
            context=context,
            dagster_type=resolve_dagster_type(dagster_type),
            paths=self.paths_for_intermediate(step_key, output_name),
        )

    def has_intermediate(self, context, step_key, output_name='result'):
        return self.has_object(
            context=context, paths=self.paths_for_intermediate(step_key, output_name)
        )

    def rm_intermediate(self, context, step_key, output_name='result'):
        return self.rm_object(
            context=context, paths=self.paths_for_intermediate(step_key, output_name)
        )


def build_fs_intermediate_store(root_for_run_id, run_id, type_storage_plugin_registry=None):
    return IntermediateStore(
        FilesystemObjectStore(),
        root_for_run_id,
        run_id,
        type_storage_plugin_registry
        if type_storage_plugin_registry
        else TypeStoragePluginRegistry(types_to_register=[]),
    )
