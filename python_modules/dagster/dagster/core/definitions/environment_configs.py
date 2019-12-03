from collections import namedtuple

from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.types import Field, List, NamedDict, Selector
from dagster.core.types.config import (
    ALL_CONFIG_BUILTINS,
    ConfigType,
    ConfigTypeAttributes,
    ConfigTypeKind,
)
from dagster.core.types.field import check_opt_field_param
from dagster.core.types.field_utils import _ConfigHasFields, build_config_dict
from dagster.core.types.iterate_types import iterate_config_types
from dagster.core.types.runtime import construct_runtime_type_dictionary
from dagster.utils import camelcase, check, ensure_single_item

from .dependency import DependencyStructure, Solid, SolidHandle, SolidInputHandle
from .logger import LoggerDefinition
from .mode import ModeDefinition
from .resource import ResourceDefinition
from .solid import CompositeSolidDefinition, ISolidDefinition, SolidDefinition


# Used elsewhere
def SystemNamedDict(_name, fields, description=None):
    '''A SystemNamedDict object is simply a NamedDict intended for internal (dagster) use.
    '''
    return build_config_dict(fields, description, is_system_config=True)


def SystemDict(fields, description=None):
    return build_config_dict(fields, description, is_system_config=True)


class _SolidContainerConfigDict(_ConfigHasFields):
    def __init__(self, name, fields, description=None, handle=None, child_solids_config_field=None):
        self._handle = check.opt_inst_param(handle, 'handle', SolidHandle)
        self._child_solids_config_field = check.opt_inst_param(
            child_solids_config_field, 'child_solids_config_field', Field
        )

        super(_SolidContainerConfigDict, self).__init__(
            key=name,
            name=name,
            kind=ConfigTypeKind.DICT,
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


def SystemSelector(fields, description=None):
    return Selector(fields, description, ConfigTypeAttributes(is_system_config=True))


class _SolidConfigDict(_ConfigHasFields):
    def __init__(self, name, fields, description):

        super(_SolidConfigDict, self).__init__(
            key=name,
            name=name,
            kind=ConfigTypeKind.DICT,
            fields=fields,
            description=description,
            type_attributes=ConfigTypeAttributes(is_system_config=True),
        )


def SolidConfigDict(name, fields, description=None):
    from dagster.core.types.field_utils import check_user_facing_fields_dict

    check_user_facing_fields_dict(fields, 'NamedDict named "{}"'.format(name))

    class _SolidConfigDictInternal(_SolidConfigDict):
        def __init__(self):
            super(_SolidConfigDictInternal, self).__init__(
                name=name, fields=fields, description=description
            )

    return _SolidConfigDictInternal


def is_solid_dict(obj):
    return isinstance(obj, _SolidConfigDict)


def is_solid_container_config(obj):
    return isinstance(obj, _SolidContainerConfigDict)


def _is_selector_field_optional(config_type):
    check.inst_param(config_type, 'config_type', ConfigType)
    if len(config_type.fields) > 1:
        return False
    else:
        _name, field = ensure_single_item(config_type.fields)
        return field.is_optional


def define_resource_dictionary_cls(resource_defs):
    check.dict_param(resource_defs, 'resource_defs', key_type=str, value_type=ResourceDefinition)

    fields = {}
    for resource_name, resource_def in resource_defs.items():
        if resource_def.config_field:
            fields[resource_name] = Field(SystemDict({'config': resource_def.config_field}))

    return SystemDict(fields=fields)


def remove_none_entries(ddict):
    return {k: v for k, v in ddict.items() if v is not None}


def define_solid_config_cls(config_field, inputs_field, outputs_field):
    check_opt_field_param(config_field, 'config_field')
    check_opt_field_param(inputs_field, 'inputs_field')
    check_opt_field_param(outputs_field, 'outputs_field')

    return SystemDict(
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
            mode_definition=check.inst_param(mode_definition, 'mode_definition', ModeDefinition),
            logger_defs=check.dict_param(
                logger_defs, 'logger_defs', key_type=str, value_type=LoggerDefinition
            ),
        )


def define_logger_dictionary_cls(creation_data):
    check.inst_param(creation_data, 'creation_data', EnvironmentClassCreationData)

    fields = {}

    for logger_name, logger_definition in creation_data.logger_defs.items():
        fields[logger_name] = Field(
            SystemDict(remove_none_entries({'config': logger_definition.config_field}),),
            is_optional=True,
        )

    return SystemDict(fields)


def define_environment_cls(creation_data):
    check.inst_param(creation_data, 'creation_data', EnvironmentClassCreationData)
    pipeline_name = camelcase(creation_data.pipeline_name)

    return SolidContainerConfigDict(
        name='{pipeline_name}.Mode.{mode_name}.Environment'.format(
            pipeline_name=pipeline_name, mode_name=camelcase(creation_data.mode_definition.name)
        ),
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
                'storage': Field(
                    define_storage_config_cls(creation_data.mode_definition), is_optional=True,
                ),
                'execution': Field(
                    define_executor_config_cls(creation_data.mode_definition), is_optional=True,
                ),
                'loggers': Field(define_logger_dictionary_cls(creation_data)),
                'resources': Field(
                    define_resource_dictionary_cls(creation_data.mode_definition.resource_defs)
                ),
            }
        ),
    )


def define_storage_config_cls(mode_definition):
    check.inst_param(mode_definition, 'mode_definition', ModeDefinition)

    fields = {}

    for storage_def in mode_definition.system_storage_defs:
        fields[storage_def.name] = Field(
            SystemDict(
                fields={'config': storage_def.config_field} if storage_def.config_field else {},
            )
        )

    return SystemSelector(fields)


def define_executor_config_cls(mode_definition):
    check.inst_param(mode_definition, 'mode_definition', ModeDefinition)

    fields = {}

    for executor_def in mode_definition.executor_defs:
        fields[executor_def.name] = Field(
            SystemDict(
                fields={'config': executor_def.config_field} if executor_def.config_field else {},
            )
        )

    return SystemSelector(fields)


def get_inputs_field(solid, handle, dependency_structure):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(handle, 'handle', SolidHandle)
    check.inst_param(dependency_structure, 'dependency_structure', DependencyStructure)

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
                inputs_field_fields[name] = Field(
                    inp.runtime_type.input_hydration_config.schema_type
                )

    if not inputs_field_fields:
        return None

    return Field(SystemDict(inputs_field_fields))


def get_outputs_field(solid, handle):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(handle, 'handle', SolidHandle)

    solid_def = solid.definition

    if not solid_def.has_configurable_outputs:
        return None

    output_dict_fields = {}
    for name, out in solid_def.output_dict.items():
        if out.runtime_type.output_materialization_config:
            output_dict_fields[name] = Field(
                type(out.runtime_type.output_materialization_config.schema_type), is_optional=True
            )

    output_entry_dict = SystemDict(output_dict_fields)

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
            'inputs': get_inputs_field(solid, handle, dependency_structure),
            'outputs': get_outputs_field(solid, handle),
        }

        # Mask solid config for solids beneath this level if config mapping is provided
        if composite_def.has_config_mapping:
            composite_config_dict['config'] = composite_def.config_mapping.config_field or Field(
                NamedDict(
                    '{pipeline_name}.CompositeSolidsConfig.{solid_handle}'.format(
                        pipeline_name=camelcase(pipeline_name), solid_handle=handle.camelcase()
                    ),
                    {},
                )
            )
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
            solid.definition.config_field,
            inputs_field=get_inputs_field(solid, handle, dependency_structure),
            outputs_field=get_outputs_field(solid, handle),
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

    return SolidConfigDict(name, fields)


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

    for config_type in iterate_config_types(environment_type):
        yield config_type


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

        type_dict_by_key[config_type.key] = config_type

    return type_dict_by_name, type_dict_by_key
