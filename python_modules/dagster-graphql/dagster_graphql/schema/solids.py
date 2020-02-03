from dagster_graphql import dauphin

from dagster import check
from dagster.core.definitions import (
    CompositeSolidDefinition,
    IContainSolids,
    ISolidDefinition,
    InputDefinition,
    OutputDefinition,
    Solid,
    SolidDefinition,
    SolidHandle,
    SolidInputHandle,
    SolidOutputHandle,
)

from .runtime_types import to_dauphin_runtime_type


class DauphinSolidContainer(dauphin.Interface):
    class Meta(object):
        name = 'SolidContainer'

    solids = dauphin.non_null_list('Solid')


class DauphinISolidDefinition(dauphin.Interface):
    class Meta(object):
        name = 'ISolidDefinition'

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    metadata = dauphin.non_null_list('MetadataItemDefinition')
    input_definitions = dauphin.non_null_list('InputDefinition')
    output_definitions = dauphin.non_null_list('OutputDefinition')
    required_resources = dauphin.non_null_list('ResourceRequirement')


class ISolidDefinitionMixin(object):
    def __init__(self, solid_def):
        self._solid_def = check.inst_param(solid_def, 'solid_def', ISolidDefinition)

    def resolve_metadata(self, graphene_info):
        return [
            graphene_info.schema.type_named('MetadataItemDefinition')(key=item[0], value=item[1])
            for item in self._solid_def.tags.items()
        ]

    def resolve_input_definitions(self, graphene_info):
        return [
            graphene_info.schema.type_named('InputDefinition')(input_definition, self)
            for input_definition in self._solid_def.input_defs
        ]

    def resolve_output_definitions(self, graphene_info):
        return [
            graphene_info.schema.type_named('OutputDefinition')(output_definition, self)
            for output_definition in self._solid_def.output_defs
        ]

    def resolve_required_resources(self, graphene_info):
        return [
            graphene_info.schema.type_named('ResourceRequirement')(key)
            for key in self._solid_def.required_resource_keys
        ]


def build_dauphin_solid_definition(graphene_info, solid_definition):
    if isinstance(solid_definition, SolidDefinition):
        return graphene_info.schema.type_named('SolidDefinition')(solid_definition)

    if isinstance(solid_definition, CompositeSolidDefinition):
        return graphene_info.schema.type_named('CompositeSolidDefinition')(solid_definition)

    check.failed('Unknown solid definition type {type}'.format(type=type(solid_definition)))


class DauphinSolid(dauphin.ObjectType):
    class Meta(object):
        name = 'Solid'

    name = dauphin.NonNull(dauphin.String)
    definition = dauphin.NonNull('ISolidDefinition')
    inputs = dauphin.non_null_list('Input')
    outputs = dauphin.non_null_list('Output')

    def __init__(self, solid, depends_on=None, depended_by=None):
        super(DauphinSolid, self).__init__(name=solid.name)
        check.opt_dict_param(depends_on, 'depends_on', key_type=SolidInputHandle, value_type=list)
        check.opt_dict_param(
            depended_by, 'depended_by', key_type=SolidOutputHandle, value_type=list
        )

        self._solid = check.inst_param(solid, 'solid', Solid)

        if depends_on:
            self.depends_on = {
                input_handle: output_handles for input_handle, output_handles in depends_on.items()
            }
        else:
            self.depends_on = {}

        if depended_by:
            self.depended_by = {
                output_handle: input_handles for output_handle, input_handles in depended_by.items()
            }
        else:
            self.depended_by = {}

    def resolve_definition(self, graphene_info):
        return build_dauphin_solid_definition(graphene_info, self._solid.definition)

    def resolve_inputs(self, graphene_info):
        return [
            graphene_info.schema.type_named('Input')(input_handle, self)
            for input_handle in self._solid.input_handles()
        ]

    def resolve_outputs(self, graphene_info):
        return [
            graphene_info.schema.type_named('Output')(output_handle, self)
            for output_handle in self._solid.output_handles()
        ]


class DauphinSolidDefinition(dauphin.ObjectType, ISolidDefinitionMixin):
    class Meta(object):
        name = 'SolidDefinition'
        interfaces = [DauphinISolidDefinition]

    config_field = dauphin.Field('ConfigTypeField')

    def __init__(self, solid_def):
        check.inst_param(solid_def, 'solid_def', SolidDefinition)
        super(DauphinSolidDefinition, self).__init__(
            name=solid_def.name, description=solid_def.description
        )
        ISolidDefinitionMixin.__init__(self, solid_def)

    def resolve_config_field(self, graphene_info):
        return (
            graphene_info.schema.type_named('ConfigTypeField')(
                name="config", field=self._solid_def.config_field
            )
            if self._solid_def.config_field
            else None
        )


class DauphinCompositeSolidDefinition(dauphin.ObjectType, ISolidDefinitionMixin):
    class Meta(object):
        name = 'CompositeSolidDefinition'
        interfaces = [DauphinISolidDefinition, DauphinSolidContainer]

    solids = dauphin.non_null_list('Solid')
    input_mappings = dauphin.non_null_list('InputMapping')
    output_mappings = dauphin.non_null_list('OutputMapping')

    def __init__(self, solid_def):
        check.inst_param(solid_def, 'solid_def', CompositeSolidDefinition)

        super(DauphinCompositeSolidDefinition, self).__init__(
            name=solid_def.name, description=solid_def.description
        )
        ISolidDefinitionMixin.__init__(self, solid_def)

    def resolve_solids(self, _graphene_info):
        return build_dauphin_solids(self._solid_def)

    def resolve_output_mappings(self, graphene_info):
        mappings = []
        for mapping in self._solid_def.output_mappings:
            mapped_solid = self._solid_def.solid_named(mapping.solid_name)
            mappings.append(
                graphene_info.schema.type_named('OutputMapping')(
                    graphene_info.schema.type_named('OutputDefinition')(
                        mapping.definition, self._solid_def
                    ),
                    graphene_info.schema.type_named('Output')(
                        mapped_solid.output_handle(mapping.output_name), DauphinSolid(mapped_solid)
                    ),
                )
            )
        return mappings

    def resolve_input_mappings(self, graphene_info):
        mappings = []
        for mapping in self._solid_def.input_mappings:
            mapped_solid = self._solid_def.solid_named(mapping.solid_name)
            mappings.append(
                graphene_info.schema.type_named('InputMapping')(
                    graphene_info.schema.type_named('InputDefinition')(
                        mapping.definition, self._solid_def
                    ),
                    graphene_info.schema.type_named('Input')(
                        mapped_solid.input_handle(mapping.input_name), DauphinSolid(mapped_solid)
                    ),
                )
            )
        return mappings


class DauphinSolidHandle(dauphin.ObjectType):
    class Meta(object):
        name = 'SolidHandle'

    handleID = dauphin.NonNull(dauphin.String)
    solid = dauphin.NonNull('Solid')
    parent = dauphin.Field('SolidHandle')

    def __init__(self, handle, solid, parent):
        self.handleID = check.inst_param(handle, 'handle', SolidHandle)
        self.solid = check.inst_param(solid, 'solid', DauphinSolid)
        self.parent = check.opt_inst_param(parent, 'parent', DauphinSolidHandle)


class DauphinInputDefinition(dauphin.ObjectType):
    class Meta(object):
        name = 'InputDefinition'

    solid_definition = dauphin.NonNull('SolidDefinition')
    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    type = dauphin.NonNull('RuntimeType')

    # inputs - ?

    def __init__(self, input_definition, solid_def):
        super(DauphinInputDefinition, self).__init__(
            name=input_definition.name,
            description=input_definition.description,
            solid_definition=solid_def,
        )
        self._input_definition = check.inst_param(
            input_definition, 'input_definition', InputDefinition
        )

    def resolve_type(self, _graphene_info):
        return to_dauphin_runtime_type(self._input_definition.runtime_type)


class DauphinOutputDefinition(dauphin.ObjectType):
    class Meta(object):
        name = 'OutputDefinition'

    solid_definition = dauphin.NonNull('SolidDefinition')
    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    type = dauphin.NonNull('RuntimeType')

    # outputs - ?

    def __init__(self, output_definition, solid_def):
        super(DauphinOutputDefinition, self).__init__(
            name=output_definition.name,
            description=output_definition.description,
            solid_definition=solid_def,
        )
        self._output_definition = check.inst_param(
            output_definition, 'output_definition', OutputDefinition
        )

    def resolve_type(self, _graphene_info):
        return to_dauphin_runtime_type(self._output_definition.runtime_type)


class DauphinInput(dauphin.ObjectType):
    class Meta(object):
        name = 'Input'

    solid = dauphin.NonNull('Solid')
    definition = dauphin.NonNull('InputDefinition')
    depends_on = dauphin.non_null_list('Output')

    def __init__(self, input_handle, solid):
        super(DauphinInput, self).__init__(solid=solid)
        self._solid = check.inst_param(solid, 'solid', DauphinSolid)
        self._input_handle = check.inst_param(input_handle, 'input_handle', SolidInputHandle)

    def resolve_definition(self, graphene_info):
        return graphene_info.schema.type_named('InputDefinition')(
            self._input_handle.input_def, self._solid.resolve_definition(graphene_info)
        )

    def resolve_depends_on(self, graphene_info):
        return [
            graphene_info.schema.type_named('Output')(
                dep, graphene_info.schema.type_named('Solid')(dep.solid)
            )
            for dep in self._solid.depends_on.get(self._input_handle, [])
        ]


class DauphinOutput(dauphin.ObjectType):
    class Meta(object):
        name = 'Output'

    solid = dauphin.NonNull('Solid')
    definition = dauphin.NonNull('OutputDefinition')
    depended_by = dauphin.non_null_list('Input')

    def __init__(self, output_handle, solid):
        super(DauphinOutput, self).__init__(solid=solid)
        self._solid = check.inst_param(solid, 'solid', DauphinSolid)
        self._output_handle = check.inst_param(output_handle, 'output_handle', SolidOutputHandle)

    def resolve_definition(self, graphene_info):
        return graphene_info.schema.type_named('OutputDefinition')(
            self._output_handle.output_def, self._solid.resolve_definition(graphene_info)
        )

    def resolve_depended_by(self, graphene_info):
        return [
            graphene_info.schema.type_named('Input')(input_handle, DauphinSolid(input_handle.solid))
            for input_handle in self._solid.depended_by.get(self._output_handle, [])
        ]


class DauphinInputMapping(dauphin.ObjectType):
    class Meta(object):
        name = 'InputMapping'

    mapped_input = dauphin.NonNull('Input')
    definition = dauphin.NonNull('InputDefinition')

    def __init__(self, input_definition, mapped_input):
        super(DauphinInputMapping, self).__init__()
        self.definition = check.inst_param(
            input_definition, 'intput_definition', DauphinInputDefinition
        )
        self.mapped_input = check.inst_param(mapped_input, 'mapped_input', DauphinInput)


class DauphinOutputMapping(dauphin.ObjectType):
    class Meta(object):
        name = 'OutputMapping'

    mapped_output = dauphin.NonNull('Output')
    definition = dauphin.NonNull('OutputDefinition')

    def __init__(self, output_definition, mapped_output):
        super(DauphinOutputMapping, self).__init__()
        self.definition = check.inst_param(
            output_definition, 'output_definition', DauphinOutputDefinition
        )
        self.mapped_output = check.inst_param(mapped_output, 'mapped_output', DauphinOutput)


class DauphinResourceRequirement(dauphin.ObjectType):
    class Meta(object):
        name = 'ResourceRequirement'

    resource_key = dauphin.NonNull(dauphin.String)

    def __init__(self, resource_key):
        self.resource_key = resource_key


def build_dauphin_solid(solid, deps):
    return DauphinSolid(
        solid,
        deps.input_to_upstream_outputs_for_solid(solid.name),
        deps.output_to_downstream_inputs_for_solid(solid.name),
    )


def build_dauphin_solids(container):
    check.inst_param(container, 'container', IContainSolids)
    return sorted(
        [build_dauphin_solid(solid, container.dependency_structure) for solid in container.solids],
        key=lambda solid: solid.name,
    )


def build_dauphin_solid_handles(container, parent=None):
    check.inst_param(container, 'container', IContainSolids)
    all_handle = []

    for solid in container.solids:
        handle = DauphinSolidHandle(
            solid=build_dauphin_solid(solid, container.dependency_structure),
            handle=SolidHandle(
                solid.name, solid.definition.name, parent.handleID if parent else None
            ),
            parent=parent if parent else None,
        )
        if isinstance(solid.definition, IContainSolids):
            all_handle += build_dauphin_solid_handles(solid.definition, handle)

        all_handle.append(handle)

    return all_handle
