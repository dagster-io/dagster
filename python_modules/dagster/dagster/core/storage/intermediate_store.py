import os

from abc import ABCMeta, abstractmethod

import six

from dagster import check, seven
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.types.runtime import RuntimeType, resolve_to_runtime_type

from .object_store import ObjectStore, FileSystemObjectStore
from .type_storage import TypeStoragePluginRegistry


class IntermediateStore(six.with_metaclass(ABCMeta)):
    def __init__(self, object_store, root, type_storage_plugin_registry):
        self.root = check.str_param(root, 'root')
        self.object_store = check.inst_param(object_store, 'object_store', ObjectStore)
        self.type_storage_plugin_registry = check.inst_param(
            type_storage_plugin_registry, 'type_storage_plugin_registry', TypeStoragePluginRegistry
        )

    def uri_for_paths(self, paths, protocol=None):
        check.list_param(paths, 'paths', of_type=str)
        check.param_invariant(len(paths) > 0, 'paths')
        key = self.key_for_paths(paths)
        return self.object_store.uri_for_key(key, protocol)

    def key_for_paths(self, paths):
        return self.object_store.key_for_paths([self.root] + paths)

    def set_object(self, obj, context, runtime_type, paths):
        check.opt_inst_param(context, 'context', SystemPipelineExecutionContext)
        check.inst_param(runtime_type, 'runtime_type', RuntimeType)
        check.list_param(paths, 'paths', of_type=str)
        check.param_invariant(len(paths) > 0, 'paths')
        key = self.object_store.key_for_paths([self.root] + paths)
        return self.object_store.set_object(
            key, obj, serialization_strategy=runtime_type.serialization_strategy
        )

    def get_object(self, context, runtime_type, paths):
        check.opt_inst_param(context, 'context', SystemPipelineExecutionContext)
        check.list_param(paths, 'paths', of_type=str)
        check.param_invariant(len(paths) > 0, 'paths')
        check.inst_param(runtime_type, 'runtime_type', RuntimeType)
        key = self.object_store.key_for_paths([self.root] + paths)
        return self.object_store.get_object(
            key, serialization_strategy=runtime_type.serialization_strategy
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

    @abstractmethod
    def copy_object_from_prev_run(self, context, previous_run_id, paths):
        pass

    def set_value(self, obj, context, runtime_type, paths):
        if self.type_storage_plugin_registry.is_registered(runtime_type):
            return self.type_storage_plugin_registry.get(runtime_type.name).set_object(
                self, obj, context, runtime_type, paths
            )
        elif runtime_type.name is None:
            self.type_storage_plugin_registry.check_for_unsupported_composite_overrides(
                runtime_type
            )

        return self.set_object(obj, context, runtime_type, paths)

    def get_value(self, context, runtime_type, paths):
        if self.type_storage_plugin_registry.is_registered(runtime_type):
            return self.type_storage_plugin_registry.get(runtime_type.name).get_object(
                self, context, runtime_type, paths
            )
        elif runtime_type.name is None:
            self.type_storage_plugin_registry.check_for_unsupported_composite_overrides(
                runtime_type
            )
        return self.get_object(context, runtime_type, paths)

    @staticmethod
    def paths_for_intermediate(step_key, output_name):
        return ['intermediates', step_key, output_name]

    def get_intermediate(self, context, step_key, dagster_type, output_name='result'):
        return self.get_object(
            context=context,
            runtime_type=resolve_to_runtime_type(dagster_type),
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


class FileSystemIntermediateStore(IntermediateStore):
    def __init__(self, run_id, type_storage_plugin_registry=None, base_dir=None):
        self.run_id = check.str_param(run_id, 'run_id')
        type_storage_plugin_registry = check.inst_param(
            type_storage_plugin_registry
            if type_storage_plugin_registry
            else TypeStoragePluginRegistry(types_to_register={}),
            'type_storage_plugin_registry',
            TypeStoragePluginRegistry,
        )

        self._base_dir = os.path.abspath(
            os.path.expanduser(
                check.opt_nonempty_str_param(
                    base_dir, 'base_dir', seven.get_system_temp_directory()
                )
            )
        )
        check.invariant(
            os.path.isdir(self._base_dir),
            'Could not find a directory at the base_dir supplied to FileSystemIntermediateStore: '
            '{base_dir}'.format(base_dir=self._base_dir),
        )

        object_store = FileSystemObjectStore()

        root = object_store.key_for_paths([self.base_dir, 'dagster', 'runs', run_id, 'files'])

        super(FileSystemIntermediateStore, self).__init__(
            object_store, root=root, type_storage_plugin_registry=type_storage_plugin_registry
        )

    @property
    def base_dir(self):
        return self._base_dir

    def copy_object_from_prev_run(
        self, context, previous_run_id, paths
    ):  # pylint: disable=unused-argument
        check.str_param(previous_run_id, 'previous_run_id')
        check.list_param(paths, 'paths', of_type=str)
        check.param_invariant(len(paths) > 0, 'paths')

        prev_run_files_dir = self.object_store.key_for_paths(
            [self.base_dir, 'dagster', 'runs', previous_run_id, 'files']
        )

        check.invariant(os.path.isdir(prev_run_files_dir))

        src = os.path.join(prev_run_files_dir, *paths)
        dst = os.path.join(self.root, *paths)
        self.object_store.cp_object(src, dst)
