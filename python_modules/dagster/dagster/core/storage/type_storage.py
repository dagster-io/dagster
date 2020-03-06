from abc import ABCMeta, abstractmethod

import six

from dagster import check


class TypeStoragePlugin(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    '''Base class for storage plugins.

    Extend this class for (system_storage_name, dagster_type) pairs that need special handling.
    '''

    @classmethod
    @abstractmethod
    def compatible_with_storage_def(self, system_storage_def):
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def set_object(cls, intermediate_store, obj, context, dagster_type, paths):
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def get_object(cls, intermediate_store, context, dagster_type, paths):
        raise NotImplementedError()

    @classmethod
    def required_resource_keys(cls):
        return frozenset()


class TypeStoragePluginRegistry(object):
    def __init__(self, types_to_register):
        from dagster.core.types.dagster_type import DagsterType

        types_to_register = check.opt_list_param(types_to_register, 'types_to_register', tuple)

        self._registry = {}
        for type_to_register, type_storage_plugin in types_to_register:
            check.inst(type_to_register, DagsterType)
            check.subclass(type_storage_plugin, TypeStoragePlugin)
            self.register_type(type_to_register, type_storage_plugin)

    def register_type(self, type_to_register, type_storage_plugin):
        from dagster.core.types.dagster_type import DagsterType

        check.inst_param(type_to_register, 'type_to_register', DagsterType)
        check.subclass_param(type_storage_plugin, 'type_storage_plugin', TypeStoragePlugin)
        check.invariant(
            type_to_register.name is not None,
            'Cannot register a type storage plugin for an anonymous type',
        )
        self._registry[type_to_register.name] = type_storage_plugin

    def is_registered(self, dagster_type):
        if dagster_type.name is not None and dagster_type.name in self._registry:
            return True
        return False

    def get(self, name):
        return self._registry.get(name)

    def check_for_unsupported_composite_overrides(self, dagster_type):
        from dagster.core.types.dagster_type import DagsterTypeKind

        composite_overrides = {t.name for t in dagster_type.inner_types if t.name in self._registry}
        if composite_overrides:
            outer_type = 'composite type'
            if dagster_type.kind == DagsterTypeKind.LIST:
                if dagster_type.kind == DagsterTypeKind.NULLABLE:
                    outer_type = 'Optional List'
                else:
                    outer_type = 'List'
            elif dagster_type.kind == DagsterTypeKind.NULLABLE:
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

    type_plugins = []
    for type_obj in pipeline_def.all_dagster_types():
        for auto_plugin in type_obj.auto_plugins:
            if auto_plugin.compatible_with_storage_def(system_storage_def):
                type_plugins.append((type_obj, auto_plugin))

    return TypeStoragePluginRegistry(type_plugins)
