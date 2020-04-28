from dagster_graphql import dauphin

from dagster import check
from dagster.core.definitions import SolidHandle
from dagster.core.snap import (
    CompositeSolidDefSnap,
    DependencyStructureIndex,
    PipelineIndex,
    SolidDefSnap,
)

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


class IDauphinSolidDefinitionMixin(object):
    def __init__(self, pipeline_index, solid_def_name):
        self._pipeline_index = check.inst_param(pipeline_index, 'pipeline_index', PipelineIndex)
        check.str_param(solid_def_name, 'solid_def_name')
        self._solid_def_snap = pipeline_index.get_solid_def_snap(solid_def_name)

    def resolve_metadata(self, graphene_info):
        return [
            graphene_info.schema.type_named('MetadataItemDefinition')(key=item[0], value=item[1])
            for item in self._solid_def_snap.tags.items()
        ]

    @property
    def solid_def_name(self):
        return self._solid_def_snap.name

    def resolve_input_definitions(self, _):
        return [
            DauphinInputDefinition(self._pipeline_index, self.solid_def_name, input_def_snap.name)
            for input_def_snap in self._solid_def_snap.input_def_snaps
        ]

    def resolve_output_definitions(self, _):
        return [
            DauphinOutputDefinition(self._pipeline_index, self.solid_def_name, output_def_snap.name)
            for output_def_snap in self._solid_def_snap.output_def_snaps
        ]

    def resolve_required_resources(self, graphene_info):
        return [
            graphene_info.schema.type_named('ResourceRequirement')(key)
            for key in self._solid_def_snap.required_resource_keys
        ]


def build_dauphin_solid_definition(pipeline_index, solid_def_name):
    check.inst_param(pipeline_index, 'pipeline_index', PipelineIndex)
    check.str_param(solid_def_name, 'solid_def_name')

    solid_def_snap = pipeline_index.get_solid_def_snap(solid_def_name)

    if isinstance(solid_def_snap, SolidDefSnap):
        return DauphinSolidDefinition(pipeline_index, solid_def_snap.name)

    if isinstance(solid_def_snap, CompositeSolidDefSnap):
        return DauphinCompositeSolidDefinition(pipeline_index, solid_def_snap.name)

    check.failed('Unknown solid definition type {type}'.format(type=type(solid_def_snap)))


class _ArgNotPresentSentinel:
    pass


class DauphinSolid(dauphin.ObjectType):
    class Meta(object):
        name = 'Solid'

    name = dauphin.NonNull(dauphin.String)
    definition = dauphin.NonNull('ISolidDefinition')
    inputs = dauphin.non_null_list('Input')
    outputs = dauphin.non_null_list('Output')

    def __init__(self, pipeline_index, solid_name, current_dep_structure):
        self._pipeline_index = check.inst_param(pipeline_index, 'pipeline_index', PipelineIndex)

        check.str_param(solid_name, 'solid_name')
        self._current_dep_structure = check.inst_param(
            current_dep_structure, 'current_dep_structure', DependencyStructureIndex
        )
        self._solid_invocation_snap = current_dep_structure.get_invocation(solid_name)
        self._solid_def_snap = pipeline_index.get_solid_def_snap(
            self._solid_invocation_snap.solid_def_name
        )
        super(DauphinSolid, self).__init__(name=solid_name)

    def get_solid_definition_name(self):
        return self._solid_def_snap.name

    def get_dauphin_solid_definition(self):
        return build_dauphin_solid_definition(self._pipeline_index, self._solid_def_snap.name)

    def resolve_definition(self, _):
        return self.get_dauphin_solid_definition()

    def resolve_inputs(self, _):
        return [
            DauphinInput(
                self._pipeline_index,
                self._current_dep_structure,
                self._solid_invocation_snap.solid_name,
                input_def_snap.name,
            )
            for input_def_snap in self._solid_def_snap.input_def_snaps
        ]

    def resolve_outputs(self, _):
        return [
            DauphinOutput(
                self._pipeline_index,
                self._current_dep_structure,
                self._solid_invocation_snap.solid_name,
                output_def_snap.name,
            )
            for output_def_snap in self._solid_def_snap.output_def_snaps
        ]


class DauphinSolidDefinition(dauphin.ObjectType, IDauphinSolidDefinitionMixin):
    class Meta(object):
        name = 'SolidDefinition'
        interfaces = [DauphinISolidDefinition]

    config_field = dauphin.Field('ConfigTypeField')

    def __init__(self, pipeline_index, solid_def_name):
        check.inst_param(pipeline_index, 'pipeline_index', PipelineIndex)
        self._solid_def_snap = pipeline_index.get_solid_def_snap(solid_def_name)
        super(DauphinSolidDefinition, self).__init__(
            name=solid_def_name, description=self._solid_def_snap.description
        )
        IDauphinSolidDefinitionMixin.__init__(self, pipeline_index, solid_def_name)

    def resolve_config_field(self, _):
        return (
            DauphinConfigTypeField(
                config_schema_snapshot=self._pipeline_index.pipeline_snapshot.config_schema_snapshot,
                field_snap=self._solid_def_snap.config_field_snap,
            )
            if self._solid_def_snap.config_field_snap
            else None
        )


class DauphinCompositeSolidDefinition(dauphin.ObjectType, IDauphinSolidDefinitionMixin):
    class Meta(object):
        name = 'CompositeSolidDefinition'
        interfaces = [DauphinISolidDefinition, DauphinSolidContainer]

    solids = dauphin.non_null_list('Solid')
    input_mappings = dauphin.non_null_list('InputMapping')
    output_mappings = dauphin.non_null_list('OutputMapping')

    def __init__(self, pipeline_index, solid_def_name):
        check.inst_param(pipeline_index, 'pipeline_index', PipelineIndex)
        self._solid_def_snap = pipeline_index.get_solid_def_snap(solid_def_name)
        self._comp_solid_dep_index = pipeline_index.get_dep_structure_index(solid_def_name)
        super(DauphinCompositeSolidDefinition, self).__init__(
            name=solid_def_name, description=self._solid_def_snap.description
        )
        IDauphinSolidDefinitionMixin.__init__(self, pipeline_index, solid_def_name)

    def resolve_solids(self, _graphene_info):
        return build_dauphin_solids(self._pipeline_index, self._comp_solid_dep_index)

    def resolve_output_mappings(self, _):
        return [
            DauphinOutputMapping(
                self._pipeline_index,
                self._comp_solid_dep_index,
                self._solid_def_snap.name,
                output_def_snap.name,
            )
            for output_def_snap in self._solid_def_snap.output_def_snaps
        ]

    def resolve_input_mappings(self, _):
        return [
            DauphinInputMapping(
                self._pipeline_index,
                self._comp_solid_dep_index,
                self._solid_def_snap.name,
                input_def_snap.name,
            )
            for input_def_snap in self._solid_def_snap.input_def_snaps
        ]


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

    def __init__(self, pipeline_index, solid_def_name, input_def_name):
        self._pipeline_index = check.inst_param(pipeline_index, 'pipeline_index', PipelineIndex)
        check.str_param(solid_def_name, 'solid_def_name')
        check.str_param(input_def_name, 'input_def_name')
        solid_def_snap = self._pipeline_index.get_solid_def_snap(solid_def_name)
        self._input_def_snap = solid_def_snap.get_input_snap(input_def_name)
        super(DauphinInputDefinition, self).__init__(
            name=self._input_def_snap.name, description=self._input_def_snap.description,
        )

    def resolve_type(self, _graphene_info):
        return to_dauphin_dagster_type(
            self._pipeline_index.pipeline_snapshot, self._input_def_snap.dagster_type_key
        )

    def resolve_solid_definition(self, _):
        return build_dauphin_solid_definition(self._pipeline_index, self._solid_def_snap.name)


class DauphinOutputDefinition(dauphin.ObjectType):
    class Meta(object):
        name = 'OutputDefinition'

    solid_definition = dauphin.NonNull('SolidDefinition')
    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    type = dauphin.NonNull('RuntimeType')

    def __init__(self, pipeline_index, solid_def_name, output_def_name):
        self._pipeline_index = check.inst_param(pipeline_index, 'pipeline_index', PipelineIndex)
        check.str_param(solid_def_name, 'solid_def_name')
        check.str_param(output_def_name, 'output_def_name')

        self._solid_def_snap = pipeline_index.get_solid_def_snap(solid_def_name)
        self._output_def_snap = self._solid_def_snap.get_output_snap(output_def_name)

        super(DauphinOutputDefinition, self).__init__(
            name=self._output_def_snap.name, description=self._output_def_snap.description,
        )

    def resolve_type(self, _):
        return to_dauphin_dagster_type(
            self._pipeline_index.pipeline_snapshot, self._output_def_snap.dagster_type_key,
        )

    def resolve_solid_definition(self, _):
        return build_dauphin_solid_definition(self._pipeline_index, self._solid_def_snap.name)


class DauphinInput(dauphin.ObjectType):
    class Meta(object):
        name = 'Input'

    solid = dauphin.NonNull('Solid')
    definition = dauphin.NonNull('InputDefinition')
    depends_on = dauphin.non_null_list('Output')

    def __init__(self, pipeline_index, current_dep_structure, solid_name, input_name):
        self._pipeline_index = check.inst_param(pipeline_index, 'pipeline_index', PipelineIndex)
        self._current_dep_structure = check.inst_param(
            current_dep_structure, 'current_dep_structure', DependencyStructureIndex
        )
        self._solid_name = check.str_param(solid_name, 'solid_name')
        self._input_name = check.str_param(input_name, 'input_name')
        self._solid_invocation_snap = current_dep_structure.get_invocation(solid_name)
        self._solid_def_snap = pipeline_index.get_solid_def_snap(
            self._solid_invocation_snap.solid_def_name
        )
        self._input_def_snap = self._solid_def_snap.get_input_snap(input_name)

        # TODO should be able to remove
        self._dauphin_solid = DauphinSolid(pipeline_index, solid_name, current_dep_structure)
        super(DauphinInput, self).__init__(solid=self._dauphin_solid)

    def resolve_definition(self, _):
        return DauphinInputDefinition(
            self._pipeline_index, self._solid_def_snap.name, self._input_def_snap.name,
        )

    def resolve_depends_on(self, _):
        return [
            DauphinOutput(
                self._pipeline_index,
                self._current_dep_structure,
                output_handle_snap.solid_name,
                output_handle_snap.output_name,
            )
            for output_handle_snap in self._current_dep_structure.get_upstream_outputs(
                self._solid_name, self._input_name
            )
        ]


class DauphinOutput(dauphin.ObjectType):
    class Meta(object):
        name = 'Output'

    solid = dauphin.NonNull('Solid')
    definition = dauphin.NonNull('OutputDefinition')
    depended_by = dauphin.non_null_list('Input')

    def __init__(self, pipeline_index, current_dep_structure, solid_name, output_name):
        self._pipeline_index = check.inst_param(pipeline_index, 'pipeline_index', PipelineIndex)
        self._current_dep_structure = check.inst_param(
            current_dep_structure, 'current_dep_structure', DependencyStructureIndex
        )
        self._solid_name = check.str_param(solid_name, 'solid_name')
        self._output_name = check.str_param(output_name, 'output_name')
        self._solid_invocation_snap = current_dep_structure.get_invocation(solid_name)
        self._solid_def_snap = pipeline_index.get_solid_def_snap(
            self._solid_invocation_snap.solid_def_name
        )
        self._output_def_snap = self._solid_def_snap.get_output_snap(output_name)
        # TODO should be able to remove
        self._dauphin_solid = DauphinSolid(pipeline_index, solid_name, current_dep_structure)
        super(DauphinOutput, self).__init__(solid=self._dauphin_solid)

    def resolve_definition(self, _):
        return DauphinOutputDefinition(
            self._pipeline_index, self._solid_def_snap.name, self._output_name
        )

    def resolve_depended_by(self, _):
        return [
            DauphinInput(
                self._pipeline_index,
                self._current_dep_structure,
                input_handle_snap.solid_name,
                input_handle_snap.input_name,
            )
            for input_handle_snap in self._current_dep_structure.get_downstream_inputs(
                self._dauphin_solid.name, self._output_def_snap.name
            )
        ]


class DauphinInputMapping(dauphin.ObjectType):
    class Meta(object):
        name = 'InputMapping'

    mapped_input = dauphin.NonNull('Input')
    definition = dauphin.NonNull('InputDefinition')

    def __init__(
        self, pipeline_index, current_dep_index, solid_def_name, input_name,
    ):
        self._pipeline_index = check.inst_param(pipeline_index, 'pipeline_index', PipelineIndex)
        self._current_dep_index = check.inst_param(
            current_dep_index, 'current_dep_index', DependencyStructureIndex
        )
        self._solid_def_snap = pipeline_index.get_solid_def_snap(solid_def_name)
        self._input_mapping_snap = self._solid_def_snap.get_input_mapping_snap(input_name)
        super(DauphinInputMapping, self).__init__()

    def resolve_mapped_input(self, _):
        return DauphinInput(
            self._pipeline_index,
            self._current_dep_index,
            self._input_mapping_snap.mapped_solid_name,
            self._input_mapping_snap.mapped_input_name,
        )

    def resolve_definition(self, _):
        return DauphinInputDefinition(
            self._pipeline_index,
            self._solid_def_snap.name,
            self._input_mapping_snap.external_input_name,
        )


class DauphinOutputMapping(dauphin.ObjectType):
    class Meta(object):
        name = 'OutputMapping'

    mapped_output = dauphin.NonNull('Output')
    definition = dauphin.NonNull('OutputDefinition')

    def __init__(
        self, pipeline_index, current_dep_index, solid_def_name, output_name,
    ):
        self._pipeline_index = check.inst_param(pipeline_index, 'pipeline_index', PipelineIndex)
        self._current_dep_index = check.inst_param(
            current_dep_index, 'current_dep_index', DependencyStructureIndex
        )
        self._solid_def_snap = pipeline_index.get_solid_def_snap(solid_def_name)
        self._output_mapping_snap = self._solid_def_snap.get_output_mapping_snap(output_name)
        super(DauphinOutputMapping, self).__init__()

    def resolve_mapped_output(self, _):
        return DauphinOutput(
            self._pipeline_index,
            self._current_dep_index,
            self._output_mapping_snap.mapped_solid_name,
            self._output_mapping_snap.mapped_output_name,
        )

    def resolve_definition(self, _):
        return DauphinOutputDefinition(
            self._pipeline_index,
            self._solid_def_snap.name,
            self._output_mapping_snap.external_output_name,
        )


class DauphinResourceRequirement(dauphin.ObjectType):
    class Meta(object):
        name = 'ResourceRequirement'

    resource_key = dauphin.NonNull(dauphin.String)

    def __init__(self, resource_key):
        self.resource_key = resource_key


class DauphinUsedSolid(dauphin.ObjectType):
    class Meta(object):
        name = 'UsedSolid'
        description = '''A solid definition and it's invocations within the repo.'''

    definition = dauphin.NonNull('ISolidDefinition')
    invocations = dauphin.non_null_list('SolidInvocationSite')


class DauphinSolidInvocationSite(dauphin.ObjectType):
    class Meta(object):
        name = 'SolidInvocationSite'
        description = '''An invocation of a solid within a repo.'''

    pipeline = dauphin.NonNull('Pipeline')
    solidHandle = dauphin.NonNull('SolidHandle')


def build_dauphin_solids(pipeline_index, current_dep_index):
    check.inst_param(pipeline_index, 'pipeline_index', PipelineIndex)
    return sorted(
        [
            DauphinSolid(pipeline_index, solid_name, current_dep_index)
            for solid_name in current_dep_index.solid_invocation_names
        ],
        key=lambda solid: solid.name,
    )


def build_dauphin_solid_handles(pipeline_index, current_dep_index, parent=None):
    check.inst_param(pipeline_index, 'pipeline_index', PipelineIndex)
    check.opt_inst_param(parent, 'parent', DauphinSolidHandle)
    all_handle = []
    for solid_invocation in current_dep_index.solid_invocations:
        solid_name, solid_def_name = solid_invocation.solid_name, solid_invocation.solid_def_name
        handle = DauphinSolidHandle(
            solid=DauphinSolid(pipeline_index, solid_name, current_dep_index),
            handle=SolidHandle(solid_name, parent.handleID if parent else None),
            parent=parent if parent else None,
        )
        solid_def_snap = pipeline_index.get_solid_def_snap(solid_def_name)
        if isinstance(solid_def_snap, CompositeSolidDefSnap):
            all_handle += build_dauphin_solid_handles(
                pipeline_index, pipeline_index.get_dep_structure_index(solid_def_name), handle
            )

        all_handle.append(handle)

    return all_handle
