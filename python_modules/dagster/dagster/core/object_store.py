import os
import shutil

from abc import ABCMeta, abstractmethod

import six

from dagster import check, seven
from dagster.utils import mkdir_p

from .execution_context import SystemPipelineExecutionContext
from .runs import RunStorageMode
from .types.runtime import RuntimeType, resolve_to_runtime_type


class TypeStoragePlugin(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    '''Base class for storage plugins.

    Extend this class for (storage_mode, runtime_type) pairs that need special handling.
    '''

    @classmethod
    @abstractmethod
    def set_object(cls, object_store, obj, context, runtime_type, paths):
        check.subclass_param(object_store, 'object_store', ObjectStore)
        return object_store.set_object(obj, context, runtime_type, paths)

    @classmethod
    @abstractmethod
    def get_object(cls, object_store, context, runtime_type, paths):
        check.subclass_param(object_store, 'object_store', ObjectStore)
        return object_store.get_object(context, runtime_type, paths)


class ObjectStore(six.with_metaclass(ABCMeta)):
    def __init__(self, types_to_register=None):
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

    @abstractmethod
    def set_object(self, obj, context, runtime_type, paths):
        pass

    @abstractmethod
    def get_object(self, context, runtime_type, paths):
        pass

    @abstractmethod
    def has_object(self, context, paths):
        pass

    @abstractmethod
    def rm_object(self, context, paths):
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


def get_run_files_directory(base_dir, run_id):
    return os.path.join(base_dir, 'dagster', 'runs', run_id, 'files')


def get_valid_target_path(base_dir, paths):
    if len(paths) > 1:
        target_dir = os.path.join(base_dir, *paths[:-1])
        mkdir_p(target_dir)
        return os.path.join(target_dir, paths[-1])
    else:
        check.invariant(len(paths) == 1)
        target_dir = base_dir
        mkdir_p(target_dir)
        return os.path.join(target_dir, paths[0])


class FileSystemObjectStore(ObjectStore):
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
            'Could not find a directory at the base_dir supplied to FileSystemObjectStore: '
            '{base_dir}'.format(base_dir=self._base_dir),
        )
        self.root = get_run_files_directory(self.base_dir, run_id)

        super(FileSystemObjectStore, self).__init__(types_to_register)

    @property
    def base_dir(self):
        return self._base_dir

    def url_for_paths(self, paths):
        return 'file:///' + '/'.join([self.root] + paths)

    def set_object(self, obj, context, runtime_type, paths):  # pylint: disable=unused-argument
        check.inst_param(context, 'context', SystemPipelineExecutionContext)
        check.inst_param(runtime_type, 'runtime_type', RuntimeType)
        check.list_param(paths, 'paths', of_type=str)
        check.param_invariant(len(paths) > 0, 'paths')

        target_path = get_valid_target_path(self.root, paths)

        check.invariant(not os.path.exists(target_path))
        # This is not going to be right in the general case, e.g. for types like Spark
        # datasets/dataframes, which naturally serialize to
        # union(parquet_file, directory([parquet_file])) -- we will need a) to pass the
        # object store into the serializer and b) to provide sugar for the common case where
        # we don't need to do anything other than open the target path as a binary file
        with open(target_path, 'wb') as ff:
            runtime_type.serialization_strategy.serialize_value(context, obj, ff)

        return target_path

    def get_object(self, context, runtime_type, paths):  # pylint: disable=unused-argument
        check.list_param(paths, 'paths', of_type=str)
        check.inst_param(runtime_type, 'runtime_type', RuntimeType)

        check.param_invariant(len(paths) > 0, 'paths')
        target_path = os.path.join(self.root, *paths)
        with open(target_path, 'rb') as ff:
            return runtime_type.serialization_strategy.deserialize_value(context, ff)

    def has_object(self, context, paths):  # pylint: disable=unused-argument
        target_path = os.path.join(self.root, *paths)
        return os.path.exists(target_path)

    def rm_object(self, context, paths):  # pylint: disable=unused-argument
        target_path = os.path.join(self.root, *paths)
        if not self.has_object(context, paths):
            return
        if os.path.isfile(target_path):
            os.unlink(target_path)
        elif os.path.isdir(target_path):
            shutil.rmtree(target_path)
        return

    def copy_object_from_prev_run(
        self, context, previous_run_id, paths
    ):  # pylint: disable=unused-argument
        prev_run_files_dir = get_run_files_directory(self.base_dir, previous_run_id)
        check.invariant(os.path.isdir(prev_run_files_dir))

        copy_from_path = os.path.join(prev_run_files_dir, *paths)
        copy_to_path = get_valid_target_path(self.root, paths)

        check.invariant(
            not os.path.exists(copy_to_path), 'Path already exists {}'.format(copy_to_path)
        )

        if os.path.isfile(copy_from_path):
            shutil.copy(copy_from_path, copy_to_path)
        elif os.path.isdir(copy_from_path):
            shutil.copytree(copy_from_path, copy_to_path)
        else:
            check.failed('should not get here')


def get_fs_paths(step_key, output_name):
    return ['intermediates', step_key, output_name]


def get_filesystem_intermediate(run_id, step_key, dagster_type, output_name='result'):
    object_store = FileSystemObjectStore(run_id)
    return object_store.get_object(
        context=None,
        runtime_type=resolve_to_runtime_type(dagster_type),
        paths=get_fs_paths(step_key, output_name),
    )


def has_filesystem_intermediate(run_id, step_key, output_name='result'):
    object_store = FileSystemObjectStore(run_id)
    return object_store.has_object(context=None, paths=get_fs_paths(step_key, output_name))


def construct_type_storage_plugin_registry(pipeline_def, storage_mode):
    return {
        type_obj: type_obj.storage_plugins.get(storage_mode)
        for type_obj in pipeline_def.all_runtime_types()
        if type_obj.storage_plugins.get(storage_mode)
    }
