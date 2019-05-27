import os

from abc import ABCMeta, abstractmethod

import six

from dagster import check, seven
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.types.runtime import RuntimeType, resolve_to_runtime_type

from .object_store import ObjectStore, FileSystemObjectStore
from .runs import RunStorageMode


class TypeStoragePlugin(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    '''Base class for storage plugins.

    Extend this class for (storage_mode, runtime_type) pairs that need special handling.
    '''

    @classmethod
    @abstractmethod
    def set_object(cls, intermediate_store, obj, context, runtime_type, paths):
        check.subclass_param(intermediate_store, 'intermediate_store', IntermediateStore)
        return intermediate_store.set_object(obj, context, runtime_type, paths)

    @classmethod
    @abstractmethod
    def get_object(cls, intermediate_store, context, runtime_type, paths):
        check.subclass_param(intermediate_store, 'intermediate_store', IntermediateStore)
        return intermediate_store.get_object(context, runtime_type, paths)


class IntermediateStore(six.with_metaclass(ABCMeta)):
    def __init__(self, object_store, root, types_to_register=None):
        self.root = check.str_param(root, 'root')

        self.object_store = check.inst_param(object_store, 'object_store', ObjectStore)

        types_to_register = check.opt_dict_param(
            types_to_register,
            'types_to_register',
            key_type=RuntimeType,
            value_class=TypeStoragePlugin,
        )
        self.TYPE_STORAGE_PLUGIN_REGISTRY = {}

        for type_to_register, type_storage_plugin in types_to_register.items():
            self.register_type(type_to_register, type_storage_plugin)

    def register_type(self, type_to_register, type_storage_plugin):
        check.inst_param(type_to_register, 'type_to_register', RuntimeType)
        check.subclass_param(type_storage_plugin, 'type_storage_plugin', TypeStoragePlugin)
        check.invariant(
            type_to_register.name is not None,
            'Cannot register a type storage plugin for an anonymous type',
        )
        self.TYPE_STORAGE_PLUGIN_REGISTRY[type_to_register.name] = type_storage_plugin

    def uri_for_paths(self, paths, protocol=None):
        check.list_param(paths, 'paths', of_type=str)
        check.param_invariant(len(paths) > 0, 'paths')
        key = self.object_store.key_for_paths([self.root] + paths)
        return self.object_store.uri_for_key(key, protocol)

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

    def _check_for_unsupported_composite_overrides(self, runtime_type):
        composite_overrides = {
            t.name for t in runtime_type.inner_types if t.name in self.TYPE_STORAGE_PLUGIN_REGISTRY
        }
        if composite_overrides:
            outer_type = 'composite type'
            if runtime_type.is_list:
                if runtime_type.is_nullable:
                    outer_type = 'Nullable List'
                else:
                    outer_type = 'List'
            elif runtime_type.is_nullable:
                outer_type = 'Nullable'

            if len(composite_overrides) > 1:
                plural = 's'
                this = 'These'
                has = 'have'
            else:
                plural = ''
                this = 'This'
                has = 'has'

            check.not_implemented(
                'You are attempting to store a {outer_type} containing type{plural} '
                '{type_names} in a object store. {this} type{plural} {has} specialized storage '
                'behavior (configured in the TYPE_STORAGE_PLUGIN_REGISTRY). We do not '
                'currently support storing Nullables or Lists of types with customized '
                'storage. See https://github.com/dagster-io/dagster/issues/1190 for '
                'details.'.format(
                    outer_type=outer_type,
                    plural=plural,
                    this=this,
                    has=has,
                    type_names=', '.join([str(x) for x in composite_overrides]),
                )
            )

    def set_value(self, obj, context, runtime_type, paths):
        if runtime_type.name is not None and runtime_type.name in self.TYPE_STORAGE_PLUGIN_REGISTRY:
            return self.TYPE_STORAGE_PLUGIN_REGISTRY[runtime_type.name].set_object(
                self, obj, context, runtime_type, paths
            )
        elif runtime_type.name is None:
            self._check_for_unsupported_composite_overrides(runtime_type)
        return self.set_object(obj, context, runtime_type, paths)

    def get_value(self, context, runtime_type, paths):
        if runtime_type.name is not None and runtime_type.name in self.TYPE_STORAGE_PLUGIN_REGISTRY:
            return self.TYPE_STORAGE_PLUGIN_REGISTRY[runtime_type.name].get_object(
                self, context, runtime_type, paths
            )
        elif runtime_type.name is None:
            self._check_for_unsupported_composite_overrides(runtime_type)
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


def construct_type_storage_plugin_registry(pipeline_def, storage_mode):
    return {
        type_obj: type_obj.storage_plugins.get(storage_mode)
        for type_obj in pipeline_def.all_runtime_types()
        if type_obj.storage_plugins.get(storage_mode)
    }


class FileSystemIntermediateStore(IntermediateStore):
    def __init__(self, run_id, types_to_register=None, base_dir=None):
        self.run_id = check.str_param(run_id, 'run_id')
        self.storage_mode = RunStorageMode.FILESYSTEM

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
            object_store, root=root, types_to_register=types_to_register
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
