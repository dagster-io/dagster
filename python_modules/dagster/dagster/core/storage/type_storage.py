from abc import ABCMeta, abstractmethod

import six

from dagster import check


class TypeStoragePlugin(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    '''Base class for storage plugins.

    Extend this class for (system_storage_name, runtime_type) pairs that need special handling.
    '''

    @classmethod
    @abstractmethod
    def compatible_with_storage_def(self, system_storage_def):
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def set_object(cls, intermediate_store, obj, context, runtime_type, paths):
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def get_object(cls, intermediate_store, context, runtime_type, paths):
        raise NotImplementedError()


class TypeStoragePluginRegistry:
    def __init__(self, types_to_register):
        from dagster import RuntimeType

        types_to_register = check.opt_dict_param(
            types_to_register,
            'types_to_register',
            key_type=RuntimeType,
            value_class=TypeStoragePlugin,
        )

        self._registry = {}
        for type_to_register, type_storage_plugin in types_to_register.items():
            self.register_type(type_to_register, type_storage_plugin)

    def register_type(self, type_to_register, type_storage_plugin):
        from dagster import RuntimeType

        check.inst_param(type_to_register, 'type_to_register', RuntimeType)
        check.subclass_param(type_storage_plugin, 'type_storage_plugin', TypeStoragePlugin)
        check.invariant(
            type_to_register.name is not None,
            'Cannot register a type storage plugin for an anonymous type',
        )
        self._registry[type_to_register.name] = type_storage_plugin

    def is_registered(self, runtime_type):
        if runtime_type.name is not None and runtime_type.name in self._registry:
            return True
        return False

    def get(self, name):
        return self._registry.get(name)

    def check_for_unsupported_composite_overrides(self, runtime_type):
        composite_overrides = {t.name for t in runtime_type.inner_types if t.name in self._registry}
        if composite_overrides:
            outer_type = 'composite type'
            if runtime_type.is_list:
                if runtime_type.is_nullable:
                    outer_type = 'Optional List'
                else:
                    outer_type = 'List'
            elif runtime_type.is_nullable:
                outer_type = 'Optional'

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


def construct_type_storage_plugin_registry(pipeline_def, system_storage_def):
    # Needed to avoid circular dep
    from dagster.core.definitions import PipelineDefinition, SystemStorageDefinition

    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.inst_param(system_storage_def, 'system_storage_def', SystemStorageDefinition)

    type_plugins = {}
    for type_obj in pipeline_def.all_runtime_types():
        for auto_plugin in type_obj.auto_plugins:
            if auto_plugin.compatible_with_storage_def(system_storage_def):
                type_plugins[type_obj] = auto_plugin

    return TypeStoragePluginRegistry(type_plugins)
