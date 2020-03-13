from collections import namedtuple

from dagster.config import Field, Selector
from dagster.config.config_type import ALL_CONFIG_BUILTINS, Array, ConfigType
from dagster.config.field import check_opt_field_param
from dagster.config.field_utils import Shape
from dagster.config.iterate_types import iterate_config_types
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.types.dagster_type import ALL_RUNTIME_BUILTINS, construct_dagster_type_dictionary
from dagster.utils import check, ensure_single_item

from .dependency import DependencyStructure, Solid, SolidHandle, SolidInputHandle
from .logger import LoggerDefinition
from .mode import ModeDefinition
from .resource import ResourceDefinition
from .solid import CompositeSolidDefinition, ISolidDefinition, SolidDefinition


def _is_selector_field_optional(config_type):
    check.inst_param(config_type, 'config_type', ConfigType)
    if len(config_type.fields) > 1:
        return False
    else:
        _name, field = ensure_single_item(config_type.fields)
        return not field.is_required


def define_resource_dictionary_cls(resource_defs):
    check.dict_param(resource_defs, 'resource_defs', key_type=str, value_type=ResourceDefinition)

    fields = {}
    for resource_name, resource_def in resource_defs.items():
        if resource_def.config_field:
            fields[resource_name] = Field(Shape({'config': resource_def.config_field}))

    return Shape(fields=fields)


def remove_none_entries(ddict):
    return {k: v for k, v in ddict.items() if v is not None}


def define_solid_config_cls(config_field, inputs_field, outputs_field):
    check_opt_field_param(config_field, 'config_field')
    check_opt_field_param(inputs_field, 'inputs_field')
    check_opt_field_param(outputs_field, 'outputs_field')

    return Shape(
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
            Shape(remove_none_entries({'config': logger_definition.config_field}),),
            is_required=False,
        )

    return Shape(fields)


def define_environment_cls(creation_data):
    check.inst_param(creation_data, 'creation_data', EnvironmentClassCreationData)

    return Shape(
        fields=remove_none_entries(
            {
                'solids': Field(
                    define_solid_dictionary_cls(
                        creation_data.solids, creation_data.dependency_structure,
                    )
                ),
                'storage': Field(
                    define_storage_config_cls(creation_data.mode_definition), is_required=False,
                ),
                'execution': Field(
                    define_executor_config_cls(creation_data.mode_definition), is_required=False,
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
            Shape(fields={'config': storage_def.config_field} if storage_def.config_field else {},)
        )

    return Selector(fields)


def define_executor_config_cls(mode_definition):
    check.inst_param(mode_definition, 'mode_definition', ModeDefinition)

    fields = {}

    for executor_def in mode_definition.executor_defs:
        fields[executor_def.name] = Field(
            Shape(
                fields={'config': executor_def.config_field} if executor_def.config_field else {},
            )
        )

    return Selector(fields)


def get_inputs_field(solid, handle, dependency_structure):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(handle, 'handle', SolidHandle)
    check.inst_param(dependency_structure, 'dependency_structure', DependencyStructure)

    if not solid.definition.has_configurable_inputs:
        return None

    inputs_field_fields = {}
    for name, inp in solid.definition.input_dict.items():
        if inp.dagster_type.input_hydration_config:
            inp_handle = SolidInputHandle(solid, inp)
            # If this input is not satisfied by a dependency you must
            # provide it via config
            if not dependency_structure.has_deps(inp_handle) and not solid.container_maps_input(
                name
            ):
                inputs_field_fields[name] = Field(
                    inp.dagster_type.input_hydration_config.schema_type
                )

    if not inputs_field_fields:
        return None

    return Field(Shape(inputs_field_fields))


def get_outputs_field(solid, handle):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(handle, 'handle', SolidHandle)

    solid_def = solid.definition

    if not solid_def.has_configurable_outputs:
        return None

    output_dict_fields = {}
    for name, out in solid_def.output_dict.items():
        if out.dagster_type.output_materialization_config:
            output_dict_fields[name] = Field(
                out.dagster_type.output_materialization_config.schema_type, is_required=False
            )

    output_entry_dict = Shape(output_dict_fields)

    return Field(Array(output_entry_dict), is_required=False)


def filtered_system_dict(fields):
    return Field(Shape(remove_none_entries(fields)))


def construct_leaf_solid_config(solid, handle, dependency_structure, config_field):
    return filtered_system_dict(
        {
            'inputs': get_inputs_field(solid, handle, dependency_structure),
            'outputs': get_outputs_field(solid, handle),
            'config': config_field,
        }
    )


def define_isolid_field(solid, handle, dependency_structure):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(handle, 'handle', SolidHandle)

    # All solids regardless of compositing status get the same inputs and outputs
    # config. The only thing the varies is on extra element of configuration
    # 1) Vanilla solid definition: a 'config' key with the config_field as the value
    # 2) Composite with field mapping: a 'config' key with the config_field of
    #    the config mapping
    # 3) Composite without field mapping: a 'solids' key with recursively defined
    #    solids dictionary

    if isinstance(solid.definition, SolidDefinition):
        return construct_leaf_solid_config(
            solid, handle, dependency_structure, solid.definition.config_field
        )

    composite_def = check.inst(solid.definition, CompositeSolidDefinition)

    if composite_def.has_config_mapping:
        return construct_leaf_solid_config(
            solid, handle, dependency_structure, composite_def.config_mapping.config_field
        )
    else:
        return filtered_system_dict(
            {
                'inputs': get_inputs_field(solid, handle, dependency_structure),
                'outputs': get_outputs_field(solid, handle),
                'solids': Field(
                    define_solid_dictionary_cls(
                        composite_def.solids, composite_def.dependency_structure, handle,
                    )
                ),
            }
        )


def define_solid_dictionary_cls(solids, dependency_structure, parent_handle=None):
    check.list_param(solids, 'solids', of_type=Solid)
    check.inst_param(dependency_structure, 'dependency_structure', DependencyStructure)
    check.opt_inst_param(parent_handle, 'parent_handle', SolidHandle)

    fields = {}
    for solid in solids:
        if solid.definition.has_config_entry:
            fields[solid.name] = define_isolid_field(
                solid,
                SolidHandle(solid.name, solid.definition.name, parent_handle),
                dependency_structure,
            )

    return Shape(fields)


def iterate_solid_def_config_types(solid_def):

    if isinstance(solid_def, SolidDefinition):
        if solid_def.config_field:
            for config_type in iterate_config_types(solid_def.config_field.config_type):
                yield config_type
    elif isinstance(solid_def, CompositeSolidDefinition):
        for solid in solid_def.solids:
            for config_type in iterate_solid_def_config_types(solid.definition):
                yield config_type

    else:
        check.invariant('Unexpected ISolidDefinition type {type}'.format(type=type(solid_def)))


def _gather_all_schemas(solid_defs):
    dagster_types = construct_dagster_type_dictionary(solid_defs)
    for dagster_type in list(dagster_types.values()) + list(ALL_RUNTIME_BUILTINS):
        if dagster_type.input_hydration_config:
            for ct in iterate_config_types(dagster_type.input_hydration_config.schema_type):
                yield ct
        if dagster_type.output_materialization_config:
            for ct in iterate_config_types(dagster_type.output_materialization_config.schema_type):
                yield ct


def _gather_all_config_types(solid_defs, environment_type):
    check.list_param(solid_defs, 'solid_defs', ISolidDefinition)
    check.inst_param(environment_type, 'environment_type', ConfigType)

    for solid_def in solid_defs:
        for config_type in iterate_solid_def_config_types(solid_def):
            yield config_type

    for config_type in iterate_config_types(environment_type):
        yield config_type


def construct_config_type_dictionary(solid_defs, environment_type):
    check.list_param(solid_defs, 'solid_defs', ISolidDefinition)
    check.inst_param(environment_type, 'environment_type', ConfigType)

    type_dict_by_name = {t.given_name: t for t in ALL_CONFIG_BUILTINS if t.given_name}
    type_dict_by_key = {t.key: t for t in ALL_CONFIG_BUILTINS}
    all_types = list(_gather_all_config_types(solid_defs, environment_type)) + list(
        _gather_all_schemas(solid_defs)
    )

    for config_type in all_types:
        name = config_type.given_name
        if name and name in type_dict_by_name:
            if type(config_type) is not type(type_dict_by_name[name]):
                raise DagsterInvalidDefinitionError(
                    (
                        'Type names must be unique. You have constructed two different '
                        'instances of types with the same name "{name}".'
                    ).format(name=name)
                )
        elif name:
            type_dict_by_name[name] = config_type

        type_dict_by_key[config_type.key] = config_type

    return type_dict_by_name, type_dict_by_key
