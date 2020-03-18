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
from dagster.core.snap.config_types import snap_from_field
from dagster.core.snap.pipeline_snapshot import PipelineSnapshot

from .config_types import DauphinConfigTypeField
from .runtime_types import to_dauphin_dagster_type


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
    def __init__(self, pipeline_snapshot, solid_def):
        self._solid_def = check.inst_param(solid_def, 'solid_def', ISolidDefinition)
        self._pipeline_snapshot = check.inst_param(
            pipeline_snapshot, 'pipeline_snapshot', PipelineSnapshot
        )

    def resolve_metadata(self, graphene_info):
        return [
            graphene_info.schema.type_named('MetadataItemDefinition')(key=item[0], value=item[1])
            for item in self._solid_def.tags.items()
        ]

    def resolve_input_definitions(self, _):
        return [
            DauphinInputDefinition(self._pipeline_snapshot, input_definition, self)
            for input_definition in self._solid_def.input_defs
        ]

    def resolve_output_definitions(self, _):
        return [
            DauphinOutputDefinition(self._pipeline_snapshot, output_definition, self)
            for output_definition in self._solid_def.output_defs
        ]

    def resolve_required_resources(self, graphene_info):
        return [
            graphene_info.schema.type_named('ResourceRequirement')(key)
            for key in self._solid_def.required_resource_keys
        ]


def build_dauphin_solid_definition(pipeline_snapshot, solid_definition):
    if isinstance(solid_definition, SolidDefinition):
        return DauphinSolidDefinition(pipeline_snapshot, solid_definition)

    if isinstance(solid_definition, CompositeSolidDefinition):
        return DauphinCompositeSolidDefinition(pipeline_snapshot, solid_definition)

    check.failed('Unknown solid definition type {type}'.format(type=type(solid_definition)))


class _ArgNotPresentSentinel:
    pass


class DauphinSolid(dauphin.ObjectType):
    class Meta(object):
        name = 'Solid'

    name = dauphin.NonNull(dauphin.String)
    definition = dauphin.NonNull('ISolidDefinition')
    inputs = dauphin.non_null_list('Input')
    outputs = dauphin.non_null_list('Output')

    # This is an odd class insofar as one can optionally construct it without
    # depends_on and depended_by set which means in turn that in certain context
    # if you went deeply nested in the graphql query the solid would "lie" and
    # say that it has no dependencies.
    def __init__(
        self, pipeline_snapshot, solid, depends_on, depended_by,
    ):
        if depends_on is not _ArgNotPresentSentinel:
            check.dict_param(depends_on, 'depends_on', key_type=SolidInputHandle, value_type=list)

        if depends_on is not _ArgNotPresentSentinel:
            check.dict_param(
                depended_by, 'depended_by', key_type=SolidOutputHandle, value_type=list
            )

        self._solid = check.inst_param(solid, 'solid', Solid)
        self._pipeline_snapshot = check.inst_param(
            pipeline_snapshot, 'pipeline_snapshot', PipelineSnapshot
        )
        self._depends_on = (
            _ArgNotPresentSentinel
            if depends_on is _ArgNotPresentSentinel
            else {
                input_handle: output_handles for input_handle, output_handles in depends_on.items()
            }
        )
        self._depended_by = (
            _ArgNotPresentSentinel
            if depended_by is _ArgNotPresentSentinel
            else {
                output_handle: input_handles for output_handle, input_handles in depended_by.items()
            }
        )

        super(DauphinSolid, self).__init__(name=solid.name)

    @staticmethod
    def construct_without_deps(pipeline_snapshot, solid):
        return DauphinSolid(
            pipeline_snapshot, solid, _ArgNotPresentSentinel, _ArgNotPresentSentinel
        )

    @property
    def depended_by(self):
        check.invariant(
            self._depended_by is not _ArgNotPresentSentinel, 'Cannot access this if not set'
        )
        return self._depended_by

    @property
    def depends_on(self):
        check.invariant(
            self._depends_on is not _ArgNotPresentSentinel, 'Cannot access this if not set'
        )
        return self._depends_on

    def resolve_definition(self, _):
        return build_dauphin_solid_definition(self._pipeline_snapshot, self._solid.definition)

    def resolve_inputs(self, _):
        return [
            DauphinInput(self._pipeline_snapshot, input_handle, self)
            for input_handle in self._solid.input_handles()
        ]

    def resolve_outputs(self, _):
        return [
            DauphinOutput(self._pipeline_snapshot, output_handle, self)
            for output_handle in self._solid.output_handles()
        ]


class DauphinSolidDefinition(dauphin.ObjectType, ISolidDefinitionMixin):
    class Meta(object):
        name = 'SolidDefinition'
        interfaces = [DauphinISolidDefinition]

    config_field = dauphin.Field('ConfigTypeField')

    def __init__(self, pipeline_snapshot, solid_def):
        check.inst_param(solid_def, 'solid_def', SolidDefinition)
        super(DauphinSolidDefinition, self).__init__(
            name=solid_def.name, description=solid_def.description
        )
        ISolidDefinitionMixin.__init__(self, pipeline_snapshot, solid_def)

    def resolve_config_field(self, _):
        return (
            DauphinConfigTypeField(
                config_schema_snapshot=self._pipeline_snapshot.config_schema_snapshot,
                field_meta=snap_from_field('config', self._solid_def.config_field),
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

    def __init__(self, pipeline_snapshot, solid_def):
        check.inst_param(solid_def, 'solid_def', CompositeSolidDefinition)
        super(DauphinCompositeSolidDefinition, self).__init__(
            name=solid_def.name, description=solid_def.description
        )
        ISolidDefinitionMixin.__init__(self, pipeline_snapshot, solid_def)

    def resolve_solids(self, _graphene_info):
        return build_dauphin_solids(self._pipeline_snapshot, self._solid_def)

    def resolve_output_mappings(self, _):
        mappings = []
        for mapping in self._solid_def.output_mappings:
            mapped_solid = self._solid_def.solid_named(mapping.solid_name)
            mappings.append(
                DauphinOutputMapping(
                    DauphinOutputDefinition(
                        self._pipeline_snapshot, mapping.definition, self._solid_def,
                    ),
                    DauphinOutput(
                        self._pipeline_snapshot,
                        mapped_solid.output_handle(mapping.output_name),
                        DauphinSolid.construct_without_deps(self._pipeline_snapshot, mapped_solid),
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
                    DauphinInputDefinition(
                        self._pipeline_snapshot, mapping.definition, self._solid_def,
                    ),
                    DauphinInput(
                        self._pipeline_snapshot,
                        mapped_solid.input_handle(mapping.input_name),
                        DauphinSolid.construct_without_deps(self._pipeline_snapshot, mapped_solid),
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

    def __init__(
        self, pipeline_snapshot, input_definition, solid_def,
    ):
        super(DauphinInputDefinition, self).__init__(
            name=input_definition.name,
            description=input_definition.description,
            solid_definition=solid_def,
        )
        self._input_definition = check.inst_param(
            input_definition, 'input_definition', InputDefinition
        )
        self._pipeline_snapshot = check.inst_param(
            pipeline_snapshot, 'pipeline_snapshot', PipelineSnapshot
        )

    def resolve_type(self, _graphene_info):
        return to_dauphin_dagster_type(
            self._pipeline_snapshot, self._input_definition.dagster_type.key
        )


class DauphinOutputDefinition(dauphin.ObjectType):
    class Meta(object):
        name = 'OutputDefinition'

    solid_definition = dauphin.NonNull('SolidDefinition')
    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    type = dauphin.NonNull('RuntimeType')

    # outputs - ?

    def __init__(
        self, pipeline_snapshot, output_definition, solid_def,
    ):
        self._output_definition = check.inst_param(
            output_definition, 'output_definition', OutputDefinition
        )
        self._pipeline_snapshot = check.inst_param(
            pipeline_snapshot, 'pipeline_snapshot', PipelineSnapshot
        )

        super(DauphinOutputDefinition, self).__init__(
            name=output_definition.name,
            description=output_definition.description,
            solid_definition=solid_def,
        )

    def resolve_type(self, _graphene_info):
        return to_dauphin_dagster_type(
            self._pipeline_snapshot, self._output_definition.dagster_type.key,
        )


class DauphinInput(dauphin.ObjectType):
    class Meta(object):
        name = 'Input'

    solid = dauphin.NonNull('Solid')
    definition = dauphin.NonNull('InputDefinition')
    depends_on = dauphin.non_null_list('Output')

    def __init__(self, pipeline_snapshot, input_handle, solid):
        self._solid = check.inst_param(solid, 'solid', DauphinSolid)
        self._input_handle = check.inst_param(input_handle, 'input_handle', SolidInputHandle)
        self._pipeline_snapshot = check.inst_param(
            pipeline_snapshot, 'pipeline_snapshot', PipelineSnapshot
        )
        super(DauphinInput, self).__init__(solid=solid)

    def resolve_definition(self, graphene_info):
        return DauphinInputDefinition(
            self._pipeline_snapshot,
            self._input_handle.input_def,
            self._solid.resolve_definition(graphene_info),
        )

    def resolve_depends_on(self, _):
        return [
            DauphinOutput(
                self._pipeline_snapshot,
                dep,
                DauphinSolid.construct_without_deps(self._pipeline_snapshot, dep.solid),
            )
            for dep in self._solid.depends_on.get(self._input_handle, [])
        ]


class DauphinOutput(dauphin.ObjectType):
    class Meta(object):
        name = 'Output'

    solid = dauphin.NonNull('Solid')
    definition = dauphin.NonNull('OutputDefinition')
    depended_by = dauphin.non_null_list('Input')

    def __init__(
        self, pipeline_snapshot, output_handle, solid,
    ):
        self._pipeline_snapshot = check.inst_param(
            pipeline_snapshot, 'pipeline_snapshot', PipelineSnapshot
        )
        self._solid = check.inst_param(solid, 'solid', DauphinSolid)
        self._output_handle = check.inst_param(output_handle, 'output_handle', SolidOutputHandle)
        super(DauphinOutput, self).__init__(solid=solid)

    def resolve_definition(self, graphene_info):
        return DauphinOutputDefinition(
            self._pipeline_snapshot,
            self._output_handle.output_def,
            self._solid.resolve_definition(graphene_info),
        )

    def resolve_depended_by(self, _):
        return [
            DauphinInput(
                self._pipeline_snapshot,
                input_handle,
                DauphinSolid.construct_without_deps(self._pipeline_snapshot, input_handle.solid),
            )
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
            input_definition, 'input_definition', DauphinInputDefinition
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


def build_dauphin_solid(pipeline_snapshot, solid, deps):
    return DauphinSolid(
        pipeline_snapshot,
        solid,
        deps.input_to_upstream_outputs_for_solid(solid.name),
        deps.output_to_downstream_inputs_for_solid(solid.name),
    )


def build_dauphin_solids(pipeline_snapshot, container):
    check.inst_param(container, 'container', IContainSolids)
    check.inst_param(pipeline_snapshot, 'pipeline_snapshot', PipelineSnapshot)
    return sorted(
        [
            build_dauphin_solid(pipeline_snapshot, solid, container.dependency_structure)
            for solid in container.solids
        ],
        key=lambda solid: solid.name,
    )


def build_dauphin_solid_handles(pipeline_snapshot, container, parent=None):
    check.inst_param(container, 'container', IContainSolids)
    check.inst_param(pipeline_snapshot, 'pipeline_snapshot', PipelineSnapshot)
    all_handle = []

    for solid in container.solids:
        handle = DauphinSolidHandle(
            solid=build_dauphin_solid(pipeline_snapshot, solid, container.dependency_structure),
            handle=SolidHandle(
                solid.name, solid.definition.name, parent.handleID if parent else None
            ),
            parent=parent if parent else None,
        )
        if isinstance(solid.definition, IContainSolids):
            all_handle += build_dauphin_solid_handles(pipeline_snapshot, solid.definition, handle)

        all_handle.append(handle)

    return all_handle
