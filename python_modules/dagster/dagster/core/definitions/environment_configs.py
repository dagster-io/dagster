from collections import namedtuple

from dagster.utils import check
from dagster.core.definitions import SolidHandle
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.types import Bool, Field, List, NamedDict, NamedSelector
from dagster.core.types.config import ALL_CONFIG_BUILTINS, ConfigType, ConfigTypeAttributes
from dagster.core.types.field_utils import FieldImpl, check_opt_field_param, _ConfigComposite
from dagster.core.types.iterate_types import iterate_config_types
from dagster.core.types.runtime import construct_runtime_type_dictionary
from dagster.utils import camelcase, single_item

from .dependency import DependencyStructure, Solid, SolidHandle, SolidInputHandle
from .logger import LoggerDefinition
from .mode import ModeDefinition
from .resource import ResourceDefinition
from .solid import CompositeSolidDefinition, ISolidDefinition, SolidDefinition


def SystemNamedDict(name, fields, description=None):
    '''A SystemNamedDict object is simply a NamedDict intended for internal (dagster) use.
    '''
    return NamedDict(name, fields, description, ConfigTypeAttributes(is_system_config=True))


class _SolidContainerConfigDict(_ConfigComposite):
    def __init__(self, name, fields, description=None, handle=None, child_solids_config_field=None):
        self._handle = check.opt_inst_param(handle, 'handle', SolidHandle)
        self._child_solids_config_field = check.opt_inst_param(
            child_solids_config_field, 'child_solids_config_field', FieldImpl
        )

        super(_SolidContainerConfigDict, self).__init__(
            key=name,
            name=name,
            fields=fields,
            description=description,
            type_attributes=ConfigTypeAttributes(is_system_config=True),
        )

    @property
    def handle(self):
        '''A solid handle ref to the composite solid that is associated with this config schema
        (e.g., this is the top-level config object for a composite solid or pipeline)
        '''
        return self._handle

    @property
    def child_solids_config_field(self):
        '''We stash the config schema for the children of composite solids here so that we can
        continue schema traversal even when masked at the top level of config
        '''
        return self._child_solids_config_field


def SolidContainerConfigDict(
    name, fields, description=None, handle=None, child_solids_config_field=None
):
    class _SolidContainerConfigDictInternal(_SolidContainerConfigDict):
        def __init__(self):
            super(_SolidContainerConfigDictInternal, self).__init__(
                name=name,
                fields=fields,
                description=description,
                handle=handle,
                child_solids_config_field=child_solids_config_field,
            )

    return _SolidContainerConfigDictInternal


def SystemNamedSelector(name, fields, description=None):
    return NamedSelector(name, fields, description, ConfigTypeAttributes(is_system_config=True))


def is_solid_container_config(obj):
    return isinstance(obj, _SolidContainerConfigDict)


def _is_selector_field_optional(config_type):
    check.inst_param(config_type, 'config_type', ConfigType)
    if len(config_type.fields) > 1:
        return False
    else:
        _name, field = single_item(config_type.fields)
        return field.is_optional


def define_resource_cls(parent_name, resource_name, resource_def):
    return SystemNamedDict(
        '{parent_name}.{resource_name}'.format(
            parent_name=parent_name, resource_name=camelcase(resource_name)
        ),
        {'config': resource_def.config_field},
    )


def define_resource_dictionary_cls(name, resource_defs):
    check.str_param(name, 'name')
    check.dict_param(resource_defs, 'resource_defs', key_type=str, value_type=ResourceDefinition)

    fields = {}
    for resource_name, resource_def in resource_defs.items():
        if resource_def.config_field:
            fields[resource_name] = Field(define_resource_cls(name, resource_name, resource_def))

    return SystemNamedDict(name=name, fields=fields)


def remove_none_entries(ddict):
    return {k: v for k, v in ddict.items() if v is not None}


def define_solid_config_cls(name, config_field, inputs_field, outputs_field):
    check.str_param(name, 'name')
    check_opt_field_param(config_field, 'config_field')
    check_opt_field_param(inputs_field, 'inputs_field')
    check_opt_field_param(outputs_field, 'outputs_field')

    return SystemNamedDict(
        name,
        remove_none_entries(
            {'config': config_field, 'inputs': inputs_field, 'outputs': outputs_field}
        ),
    )


class EnvironmentClassCreationData(
    namedtuple(
        'EnvironmentClassCreationData',
        'pipeline_name solids dependency_structure mode_definition logger_defs',
    )
):
    def __new__(cls, pipeline_name, solids, dependency_structure, mode_definition, logger_defs):
        return super(EnvironmentClassCreationData, cls).__new__(
            cls,
            pipeline_name=check.str_param(pipeline_name, 'pipeline_name'),
            solids=check.list_param(solids, 'solids', of_type=Solid),
            dependency_structure=check.inst_param(
                dependency_structure, 'dependency_structure', DependencyStructure
            ),
            mode_definition=check.opt_inst_param(
                mode_definition, 'mode_definition', ModeDefinition
            ),
            logger_defs=check.dict_param(
                logger_defs, 'logger_defs', key_type=str, value_type=LoggerDefinition
            ),
        )


def define_mode_resources_dictionary_cls(pipeline_name, mode_definition):
    check.str_param(pipeline_name, 'pipeline_name')
    check.inst_param(mode_definition, 'mode_definition', ModeDefinition)

    return define_resource_dictionary_cls(
        '{pipeline_name}.Mode.{mode}.Resources'.format(
            pipeline_name=pipeline_name, mode=camelcase(mode_definition.name)
        ),
        mode_definition.resource_defs,
    )


def define_logger_dictionary_cls(name, creation_data):
    check.str_param(name, 'name')
    check.inst_param(creation_data, 'creation_data', EnvironmentClassCreationData)

    fields = {}

    for logger_name, logger_definition in creation_data.logger_defs.items():
        fields[logger_name] = Field(
            SystemNamedDict(
                '{pipeline_name}.LoggerConfig.{logger_name}'.format(
                    pipeline_name=camelcase(creation_data.pipeline_name),
                    logger_name=camelcase(logger_name),
                ),
                remove_none_entries({'config': logger_definition.config_field}),
            ),
            is_optional=True,
        )

    return SystemNamedDict(name, fields)


def define_environment_cls(creation_data):
    check.inst_param(creation_data, 'creation_data', EnvironmentClassCreationData)
    pipeline_name = camelcase(creation_data.pipeline_name)

    return SolidContainerConfigDict(
        name='{pipeline_name}.Mode.{mode_name}.Environment'.format(
            pipeline_name=pipeline_name, mode_name=camelcase(creation_data.mode_definition.name)
        )
        if creation_data.mode_definition
        else '{pipeline_name}.Environment'.format(pipeline_name=pipeline_name),
        fields=remove_none_entries(
            {
                'solids': Field(
                    define_solid_dictionary_cls(
                        '{pipeline_name}.SolidsConfigDictionary'.format(
                            pipeline_name=pipeline_name
                        ),
                        creation_data.solids,
                        creation_data.dependency_structure,
                        creation_data.pipeline_name,
                    )
                ),
                'expectations': Field(
                    define_expectations_config_cls(
                        '{pipeline_name}.ExpectationsConfig'.format(pipeline_name=pipeline_name)
                    )
                ),
                'storage': Field(
                    define_storage_config_cls(
                        '{pipeline_name}.{mode_name}.StorageConfig'.format(
                            pipeline_name=pipeline_name,
                            mode_name=camelcase(creation_data.mode_definition.name),
                        ),
                        creation_data.mode_definition,
                    ),
                    is_optional=True,
                ),
                'execution': Field(
                    define_execution_config_cls(
                        '{pipeline_name}.ExecutionConfig'.format(pipeline_name=pipeline_name)
                    )
                ),
                'loggers': Field(
                    define_logger_dictionary_cls(
                        '{pipeline_name}.LoggerConfig'.format(pipeline_name=pipeline_name),
                        creation_data,
                    )
                ),
                'resources': Field(
                    define_mode_resources_dictionary_cls(
                        pipeline_name, creation_data.mode_definition
                    )
                ),
            }
        ),
    )


def define_expectations_config_cls(name):
    check.str_param(name, 'name')

    return SystemNamedDict(
        name, fields={'evaluate': Field(Bool, is_optional=True, default_value=True)}
    )


def define_storage_config_cls(type_name, mode_definition):
    check.str_param(type_name, 'type_name')
    check.inst_param(mode_definition, 'mode_definition', ModeDefinition)

    fields = {}

    for storage_def in mode_definition.system_storage_defs:
        fields[storage_def.name] = Field(
            SystemNamedDict(
                name='{type_name}.{storage_name}'.format(
                    type_name=type_name, storage_name=camelcase(storage_def.name)
                ),
                fields={'config': storage_def.config_field} if storage_def.config_field else {},
            )
        )

    return SystemNamedSelector(type_name, fields)


def get_inputs_field(solid, handle, dependency_structure, pipeline_name):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(handle, 'handle', SolidHandle)
    check.inst_param(dependency_structure, 'dependency_structure', DependencyStructure)
    check.str_param(pipeline_name, 'pipeline_name')

    if not solid.definition.has_configurable_inputs:
        return None

    inputs_field_fields = {}
    for name, inp in solid.definition.input_dict.items():
        if inp.runtime_type.input_hydration_config:
            inp_handle = SolidInputHandle(solid, inp)
            # If this input is not satisfied by a dependency you must
            # provide it via config
            if not dependency_structure.has_deps(inp_handle) and not solid.container_maps_input(
                name
            ):
                inputs_field_fields[name] = FieldImpl(
                    inp.runtime_type.input_hydration_config.schema_type
                )

    if not inputs_field_fields:
        return None

    return Field(
        SystemNamedDict(
            '{pipeline_name}.{solid_handle}.Inputs'.format(
                pipeline_name=camelcase(pipeline_name), solid_handle=handle.camelcase()
            ),
            inputs_field_fields,
        )
    )


def get_outputs_field(solid, handle, pipeline_name):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(handle, 'handle', SolidHandle)
    check.str_param(pipeline_name, 'pipeline_name')

    solid_def = solid.definition

    if not solid_def.has_configurable_outputs:
        return None

    output_dict_fields = {}
    for name, out in solid_def.output_dict.items():
        if out.runtime_type.output_materialization_config:
            output_dict_fields[name] = Field(
                type(out.runtime_type.output_materialization_config.schema_type), is_optional=True
            )

    output_entry_dict = SystemNamedDict(
        '{pipeline_name}.{solid_handle}.Outputs'.format(
            pipeline_name=camelcase(pipeline_name), solid_handle=handle.camelcase()
        ),
        output_dict_fields,
    )

    return Field(List[output_entry_dict], is_optional=True)


def define_isolid_field(solid, handle, dependency_structure, pipeline_name):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(handle, 'handle', SolidHandle)

    check.str_param(pipeline_name, 'pipeline_name')

    if isinstance(solid.definition, CompositeSolidDefinition):
        composite_def = solid.definition
        child_solids_config_field = Field(
            define_solid_dictionary_cls(
                '{pipeline_name}.CompositeSolidsDict.{solid_handle}'.format(
                    pipeline_name=camelcase(pipeline_name), solid_handle=handle.camelcase()
                ),
                composite_def.solids,
                composite_def.dependency_structure,
                pipeline_name,
                handle,
            )
        )

        composite_config_dict = {
            'inputs': get_inputs_field(solid, handle, dependency_structure, pipeline_name),
            'outputs': get_outputs_field(solid, handle, pipeline_name),
        }

        # Mask solid config for solids beneath this level if config mapping is provided
        if composite_def.has_config_mapping:
            composite_config_dict['config'] = composite_def.config_mapping.config_field
        else:
            composite_config_dict['solids'] = child_solids_config_field

        return Field(
            SolidContainerConfigDict(
                '{name}CompositeSolidConfig'.format(name=str(handle)),
                remove_none_entries(composite_config_dict),
                handle=handle,
                child_solids_config_field=child_solids_config_field,
            )
        )

    elif isinstance(solid.definition, SolidDefinition):
        solid_config_type = define_solid_config_cls(
            '{pipeline_name}.SolidConfig.{solid_handle}'.format(
                pipeline_name=camelcase(pipeline_name), solid_handle=handle.camelcase()
            ),
            solid.definition.config_field,
            inputs_field=get_inputs_field(solid, handle, dependency_structure, pipeline_name),
            outputs_field=get_outputs_field(solid, handle, pipeline_name),
        )
        return Field(solid_config_type)
    else:
        check.invariant(
            'Unexpected ISolidDefinition type {type}'.format(type=type(solid.definition))
        )


def define_solid_dictionary_cls(
    name, solids, dependency_structure, pipeline_name, parent_handle=None
):
    check.str_param(name, 'name')
    check.list_param(solids, 'solids', of_type=Solid)
    check.inst_param(dependency_structure, 'dependency_structure', DependencyStructure)
    check.str_param(pipeline_name, 'pipeline_name')
    check.opt_inst_param(parent_handle, 'parent_handle', SolidHandle)

    fields = {}
    for solid in solids:
        if solid.definition.has_config_entry:
            fields[solid.name] = define_isolid_field(
                solid,
                SolidHandle(solid.name, solid.definition.name, parent_handle),
                dependency_structure,
                pipeline_name,
            )

    return SystemNamedDict(name, fields)


def define_execution_config_cls(name):
    check.str_param(name, 'name')
    return SystemNamedDict(name, {})


def iterate_solid_def_types(solid_def):

    if isinstance(solid_def, SolidDefinition):
        if solid_def.config_field:
            for runtime_type in iterate_config_types(solid_def.config_field.config_type):
                yield runtime_type
    elif isinstance(solid_def, CompositeSolidDefinition):
        for solid in solid_def.solids:
            for def_type in iterate_solid_def_types(solid.definition):
                yield def_type

    else:
        check.invariant('Unexpected ISolidDefinition type {type}'.format(type=type(solid_def)))


def _gather_all_schemas(solid_defs):
    runtime_types = construct_runtime_type_dictionary(solid_defs)
    for rtt in runtime_types.values():
        if rtt.input_hydration_config:
            for ct in iterate_config_types(rtt.input_hydration_config.schema_type):
                yield ct
        if rtt.output_materialization_config:
            for ct in iterate_config_types(rtt.output_materialization_config.schema_type):
                yield ct


def _gather_all_config_types(solid_defs, environment_type):
    check.list_param(solid_defs, 'solid_defs', ISolidDefinition)
    check.inst_param(environment_type, 'environment_type', ConfigType)

    for solid_def in solid_defs:
        for runtime_type in iterate_solid_def_types(solid_def):
            yield runtime_type

    for runtime_type in iterate_config_types(environment_type):
        yield runtime_type


def construct_config_type_dictionary(solid_defs, environment_type):
    check.list_param(solid_defs, 'solid_defs', ISolidDefinition)
    check.inst_param(environment_type, 'environment_type', ConfigType)

    type_dict_by_name = {t.name: t for t in ALL_CONFIG_BUILTINS}
    type_dict_by_key = {t.key: t for t in ALL_CONFIG_BUILTINS}
    all_types = list(_gather_all_config_types(solid_defs, environment_type)) + list(
        _gather_all_schemas(solid_defs)
    )

    for config_type in all_types:
        name = config_type.name
        if name and name in type_dict_by_name:
            if type(config_type) is not type(type_dict_by_name[name]):
                raise DagsterInvalidDefinitionError(
                    (
                        'Type names must be unique. You have constructed two different '
                        'instances of types with the same name "{name}".'
                    ).format(name=name)
                )
        elif name:
            type_dict_by_name[config_type.name] = config_type

        key = config_type.key

        if key in type_dict_by_key:
            if type(config_type) is not type(type_dict_by_key[key]):
                raise DagsterInvalidDefinitionError(
                    (
                        'Type keys must be unique. You have constructed two different '
                        'instances of types with the same key "{key}".'
                    ).format(key=key)
                )

        else:
            type_dict_by_key[config_type.key] = config_type

    return type_dict_by_name, type_dict_by_key
