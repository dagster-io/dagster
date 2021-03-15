import graphene
from dagster import check
from dagster.core.definitions import SolidHandle
from dagster.core.host_representation import RepresentedPipeline
from dagster.core.snap import CompositeSolidDefSnap, DependencyStructureIndex, SolidDefSnap

from .config_types import GrapheneConfigTypeField
from .dagster_types import GrapheneDagsterType, to_dagster_type
from .metadata import GrapheneMetadataItemDefinition
from .util import non_null_list


class _ArgNotPresentSentinel:
    pass


class GrapheneInputDefinition(graphene.ObjectType):
    solid_definition = graphene.NonNull(lambda: GrapheneSolidDefinition)
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    type = graphene.NonNull(GrapheneDagsterType)

    class Meta:
        name = "InputDefinition"

    def __init__(self, represented_pipeline, solid_def_name, input_def_name):
        self._represented_pipeline = check.inst_param(
            represented_pipeline, "represented_pipeline", RepresentedPipeline
        )
        check.str_param(solid_def_name, "solid_def_name")
        check.str_param(input_def_name, "input_def_name")
        solid_def_snap = self._represented_pipeline.get_solid_def_snap(solid_def_name)
        self._input_def_snap = solid_def_snap.get_input_snap(input_def_name)
        super().__init__(
            name=self._input_def_snap.name,
            description=self._input_def_snap.description,
        )

    def resolve_type(self, _graphene_info):
        return to_dagster_type(
            self._represented_pipeline.pipeline_snapshot, self._input_def_snap.dagster_type_key
        )

    def resolve_solid_definition(self, _graphene_info):
        return build_solid_definition(
            self._represented_pipeline, self._solid_def_snap.name  # pylint: disable=no-member
        )


class GrapheneOutputDefinition(graphene.ObjectType):
    solid_definition = graphene.NonNull(lambda: GrapheneSolidDefinition)
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    is_dynamic = graphene.Boolean()
    type = graphene.NonNull(GrapheneDagsterType)

    class Meta:
        name = "OutputDefinition"

    def __init__(self, represented_pipeline, solid_def_name, output_def_name, is_dynamic):
        self._represented_pipeline = check.inst_param(
            represented_pipeline, "represented_pipeline", RepresentedPipeline
        )
        check.str_param(solid_def_name, "solid_def_name")
        check.str_param(output_def_name, "output_def_name")

        self._solid_def_snap = represented_pipeline.get_solid_def_snap(solid_def_name)
        self._output_def_snap = self._solid_def_snap.get_output_snap(output_def_name)

        super().__init__(
            name=self._output_def_snap.name,
            description=self._output_def_snap.description,
            is_dynamic=is_dynamic,
        )

    def resolve_type(self, _graphene_info):
        return to_dagster_type(
            self._represented_pipeline.pipeline_snapshot,
            self._output_def_snap.dagster_type_key,
        )

    def resolve_solid_definition(self, _graphene_info):
        return build_solid_definition(self._represented_pipeline, self._solid_def_snap.name)


class GrapheneInput(graphene.ObjectType):
    solid = graphene.NonNull(lambda: GrapheneSolid)
    definition = graphene.NonNull(GrapheneInputDefinition)
    depends_on = non_null_list(lambda: GrapheneOutput)
    is_dynamic_collect = graphene.NonNull(graphene.Boolean)

    class Meta:
        name = "Input"

    def __init__(self, represented_pipeline, current_dep_structure, solid_name, input_name):
        self._represented_pipeline = check.inst_param(
            represented_pipeline, "represented_pipeline", RepresentedPipeline
        )
        self._current_dep_structure = check.inst_param(
            current_dep_structure, "current_dep_structure", DependencyStructureIndex
        )
        self._solid_name = check.str_param(solid_name, "solid_name")
        self._input_name = check.str_param(input_name, "input_name")
        self._solid_invocation_snap = current_dep_structure.get_invocation(solid_name)
        self._solid_def_snap = represented_pipeline.get_solid_def_snap(
            self._solid_invocation_snap.solid_def_name
        )
        self._input_def_snap = self._solid_def_snap.get_input_snap(input_name)

        super().__init__()

    def resolve_solid(self, _graphene_info):
        return GrapheneSolid(
            self._represented_pipeline, self._solid_name, self._current_dep_structure
        )

    def resolve_definition(self, _graphene_info):
        return GrapheneInputDefinition(
            self._represented_pipeline,
            self._solid_def_snap.name,
            self._input_def_snap.name,
        )

    def resolve_depends_on(self, _graphene_info):
        return [
            GrapheneOutput(
                self._represented_pipeline,
                self._current_dep_structure,
                output_handle_snap.solid_name,
                output_handle_snap.output_name,
            )
            for output_handle_snap in self._current_dep_structure.get_upstream_outputs(
                self._solid_name, self._input_name
            )
        ]

    def resolve_is_dynamic_collect(self, _graphene_info):
        return self._solid_invocation_snap.input_dep_snap(self._input_name).is_dynamic_collect


class GrapheneOutput(graphene.ObjectType):
    solid = graphene.NonNull(lambda: GrapheneSolid)
    definition = graphene.NonNull(GrapheneOutputDefinition)
    depended_by = non_null_list(GrapheneInput)

    class Meta:
        name = "Output"

    def __init__(self, represented_pipeline, current_dep_structure, solid_name, output_name):
        self._represented_pipeline = check.inst_param(
            represented_pipeline, "represented_pipeline", RepresentedPipeline
        )
        self._current_dep_structure = check.inst_param(
            current_dep_structure, "current_dep_structure", DependencyStructureIndex
        )
        self._solid_name = check.str_param(solid_name, "solid_name")
        self._output_name = check.str_param(output_name, "output_name")
        self._solid_invocation_snap = current_dep_structure.get_invocation(solid_name)
        self._solid_def_snap = represented_pipeline.get_solid_def_snap(
            self._solid_invocation_snap.solid_def_name
        )
        self._output_def_snap = self._solid_def_snap.get_output_snap(output_name)
        super().__init__()

    def resolve_solid(self, _):
        return GrapheneSolid(
            self._represented_pipeline, self._solid_name, self._current_dep_structure
        )

    def resolve_definition(self, _graphene_info):
        return GrapheneOutputDefinition(
            self._represented_pipeline,
            self._solid_def_snap.name,
            self._output_name,
            self._output_def_snap.is_dynamic,
        )

    def resolve_depended_by(self, _graphene_info):
        return [
            GrapheneInput(
                self._represented_pipeline,
                self._current_dep_structure,
                input_handle_snap.solid_name,
                input_handle_snap.input_name,
            )
            for input_handle_snap in self._current_dep_structure.get_downstream_inputs(
                self._solid_name, self._output_def_snap.name
            )
        ]


class GrapheneInputMapping(graphene.ObjectType):
    mapped_input = graphene.NonNull(GrapheneInput)
    definition = graphene.NonNull(GrapheneInputDefinition)

    class Meta:
        name = "InputMapping"

    def __init__(
        self,
        represented_pipeline,
        current_dep_index,
        solid_def_name,
        input_name,
    ):
        self._represented_pipeline = check.inst_param(
            represented_pipeline, "represented_pipeline", RepresentedPipeline
        )
        self._current_dep_index = check.inst_param(
            current_dep_index, "current_dep_index", DependencyStructureIndex
        )
        self._solid_def_snap = represented_pipeline.get_solid_def_snap(solid_def_name)
        self._input_mapping_snap = self._solid_def_snap.get_input_mapping_snap(input_name)
        super().__init__()

    def resolve_mapped_input(self, _graphene_info):
        return GrapheneInput(
            self._represented_pipeline,
            self._current_dep_index,
            self._input_mapping_snap.mapped_solid_name,
            self._input_mapping_snap.mapped_input_name,
        )

    def resolve_definition(self, _graphene_info):
        return GrapheneInputDefinition(
            self._represented_pipeline,
            self._solid_def_snap.name,
            self._input_mapping_snap.external_input_name,
        )


class GrapheneOutputMapping(graphene.ObjectType):
    mapped_output = graphene.NonNull(GrapheneOutput)
    definition = graphene.NonNull(GrapheneOutputDefinition)

    class Meta:
        name = "OutputMapping"

    def __init__(
        self,
        represented_pipeline,
        current_dep_index,
        solid_def_name,
        output_name,
    ):
        self._represented_pipeline = check.inst_param(
            represented_pipeline, "represented_pipeline", RepresentedPipeline
        )
        self._current_dep_index = check.inst_param(
            current_dep_index, "current_dep_index", DependencyStructureIndex
        )
        self._solid_def_snap = represented_pipeline.get_solid_def_snap(solid_def_name)
        self._output_mapping_snap = self._solid_def_snap.get_output_mapping_snap(output_name)
        self._output_def_snap = self._solid_def_snap.get_output_snap(output_name)

        super().__init__()

    def resolve_mapped_output(self, _graphene_info):
        return GrapheneOutput(
            self._represented_pipeline,
            self._current_dep_index,
            self._output_mapping_snap.mapped_solid_name,
            self._output_mapping_snap.mapped_output_name,
        )

    def resolve_definition(self, _graphene_info):
        return GrapheneOutputDefinition(
            self._represented_pipeline,
            self._solid_def_snap.name,
            self._output_mapping_snap.external_output_name,
            self._output_def_snap.is_dynamic,
        )


class GrapheneResourceRequirement(graphene.ObjectType):
    resource_key = graphene.NonNull(graphene.String)

    class Meta:
        name = "ResourceRequirement"

    def __init__(self, resource_key):
        super().__init__()
        self.resource_key = resource_key


def build_solids(represented_pipeline, current_dep_index):
    check.inst_param(represented_pipeline, "represented_pipeline", RepresentedPipeline)
    return sorted(
        [
            GrapheneSolid(represented_pipeline, solid_name, current_dep_index)
            for solid_name in current_dep_index.solid_invocation_names
        ],
        key=lambda solid: solid.name,
    )


def build_solid_handles(represented_pipeline, current_dep_index, parent=None):
    check.inst_param(represented_pipeline, "represented_pipeline", RepresentedPipeline)
    check.opt_inst_param(parent, "parent", GrapheneSolidHandle)
    all_handle = []
    for solid_invocation in current_dep_index.solid_invocations:
        solid_name, solid_def_name = solid_invocation.solid_name, solid_invocation.solid_def_name
        handle = GrapheneSolidHandle(
            solid=GrapheneSolid(represented_pipeline, solid_name, current_dep_index),
            handle=SolidHandle(solid_name, parent.handleID if parent else None),
            parent=parent if parent else None,
        )
        solid_def_snap = represented_pipeline.get_solid_def_snap(solid_def_name)
        if isinstance(solid_def_snap, CompositeSolidDefSnap):
            all_handle += build_solid_handles(
                represented_pipeline,
                represented_pipeline.get_dep_structure_index(solid_def_name),
                handle,
            )

        all_handle.append(handle)

    return all_handle


class GrapheneISolidDefinition(graphene.Interface):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    metadata = non_null_list(GrapheneMetadataItemDefinition)
    input_definitions = non_null_list(GrapheneInputDefinition)
    output_definitions = non_null_list(GrapheneOutputDefinition)
    required_resources = non_null_list(GrapheneResourceRequirement)

    class Meta:
        name = "ISolidDefinition"


class ISolidDefinitionMixin:
    def __init__(self, represented_pipeline, solid_def_name):
        self._represented_pipeline = check.inst_param(
            represented_pipeline, "represented_pipeline", RepresentedPipeline
        )
        check.str_param(solid_def_name, "solid_def_name")
        self._solid_def_snap = represented_pipeline.get_solid_def_snap(solid_def_name)

    def resolve_metadata(self, _graphene_info):
        return [
            GrapheneMetadataItemDefinition(key=item[0], value=item[1])
            for item in self._solid_def_snap.tags.items()
        ]

    @property
    def solid_def_name(self):
        return self._solid_def_snap.name

    def resolve_input_definitions(self, _graphene_info):
        return [
            GrapheneInputDefinition(
                self._represented_pipeline, self.solid_def_name, input_def_snap.name
            )
            for input_def_snap in self._solid_def_snap.input_def_snaps
        ]

    def resolve_output_definitions(self, _graphene_info):
        return [
            GrapheneOutputDefinition(
                self._represented_pipeline,
                self.solid_def_name,
                output_def_snap.name,
                output_def_snap.is_dynamic,
            )
            for output_def_snap in self._solid_def_snap.output_def_snaps
        ]

    def resolve_required_resources(self, _graphene_info):
        return [
            GrapheneResourceRequirement(key) for key in self._solid_def_snap.required_resource_keys
        ]


class GrapheneSolidDefinition(graphene.ObjectType, ISolidDefinitionMixin):
    config_field = graphene.Field(GrapheneConfigTypeField)

    class Meta:
        interfaces = (GrapheneISolidDefinition,)
        name = "SolidDefinition"

    def __init__(self, represented_pipeline, solid_def_name):
        check.inst_param(represented_pipeline, "represented_pipeline", RepresentedPipeline)
        self._solid_def_snap = represented_pipeline.get_solid_def_snap(solid_def_name)
        super().__init__(name=solid_def_name, description=self._solid_def_snap.description)
        ISolidDefinitionMixin.__init__(self, represented_pipeline, solid_def_name)

    def resolve_config_field(self, _graphene_info):
        return (
            GrapheneConfigTypeField(
                config_schema_snapshot=self._represented_pipeline.config_schema_snapshot,
                field_snap=self._solid_def_snap.config_field_snap,
            )
            if self._solid_def_snap.config_field_snap
            else None
        )


class GrapheneSolid(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    definition = graphene.NonNull(lambda: GrapheneISolidDefinition)
    inputs = non_null_list(GrapheneInput)
    outputs = non_null_list(GrapheneOutput)
    is_dynamic_mapped = graphene.NonNull(graphene.Boolean)

    class Meta:
        name = "Solid"

    def __init__(self, represented_pipeline, solid_name, current_dep_structure):
        self._represented_pipeline = check.inst_param(
            represented_pipeline, "represented_pipeline", RepresentedPipeline
        )

        check.str_param(solid_name, "solid_name")
        self._current_dep_structure = check.inst_param(
            current_dep_structure, "current_dep_structure", DependencyStructureIndex
        )
        self._solid_invocation_snap = current_dep_structure.get_invocation(solid_name)
        self._solid_def_snap = represented_pipeline.get_solid_def_snap(
            self._solid_invocation_snap.solid_def_name
        )
        super().__init__(name=solid_name)

    def get_solid_definition_name(self):
        return self._solid_def_snap.name

    def get_solid_definition(self):
        return build_solid_definition(self._represented_pipeline, self._solid_def_snap.name)

    def resolve_definition(self, _graphene_info):
        return self.get_solid_definition()

    def resolve_inputs(self, _graphene_info):
        return [
            GrapheneInput(
                self._represented_pipeline,
                self._current_dep_structure,
                self._solid_invocation_snap.solid_name,
                input_def_snap.name,
            )
            for input_def_snap in self._solid_def_snap.input_def_snaps
        ]

    def resolve_outputs(self, _graphene_info):
        return [
            GrapheneOutput(
                self._represented_pipeline,
                self._current_dep_structure,
                self._solid_invocation_snap.solid_name,
                output_def_snap.name,
            )
            for output_def_snap in self._solid_def_snap.output_def_snaps
        ]

    def resolve_is_dynamic_mapped(self, _graphene_info):
        return self._solid_invocation_snap.is_dynamic_mapped


class GrapheneSolidContainer(graphene.Interface):
    solids = non_null_list(GrapheneSolid)

    class Meta:
        name = "SolidContainer"


class GrapheneCompositeSolidDefinition(graphene.ObjectType, ISolidDefinitionMixin):
    solids = non_null_list(GrapheneSolid)
    input_mappings = non_null_list(GrapheneInputMapping)
    output_mappings = non_null_list(GrapheneOutputMapping)

    class Meta:
        interfaces = (GrapheneISolidDefinition, GrapheneSolidContainer)
        name = "CompositeSolidDefinition"

    def __init__(self, represented_pipeline, solid_def_name):
        self._represented_pipeline = check.inst_param(
            represented_pipeline, "represented_pipeline", RepresentedPipeline
        )
        self._solid_def_snap = represented_pipeline.get_solid_def_snap(solid_def_name)
        self._comp_solid_dep_index = represented_pipeline.get_dep_structure_index(solid_def_name)
        super().__init__(name=solid_def_name, description=self._solid_def_snap.description)
        ISolidDefinitionMixin.__init__(self, represented_pipeline, solid_def_name)

    def resolve_solids(self, _graphene_info):
        return build_solids(self._represented_pipeline, self._comp_solid_dep_index)

    def resolve_output_mappings(self, _graphene_info):
        return [
            GrapheneOutputMapping(
                self._represented_pipeline,
                self._comp_solid_dep_index,
                self._solid_def_snap.name,
                output_def_snap.name,
            )
            for output_def_snap in self._solid_def_snap.output_def_snaps
        ]

    def resolve_input_mappings(self, _graphene_info):
        return [
            GrapheneInputMapping(
                self._represented_pipeline,
                self._comp_solid_dep_index,
                self._solid_def_snap.name,
                input_def_snap.name,
            )
            for input_def_snap in self._solid_def_snap.input_def_snaps
        ]


class GrapheneSolidHandle(graphene.ObjectType):
    handleID = graphene.NonNull(graphene.String)
    solid = graphene.NonNull(GrapheneSolid)
    parent = graphene.Field(lambda: GrapheneSolidHandle)

    class Meta:
        name = "SolidHandle"

    def __init__(self, handle, solid, parent):
        super().__init__()
        # FIXME this really seems wrong
        self.handleID = check.inst_param(handle, "handle", SolidHandle)
        self.solid = check.inst_param(solid, "solid", GrapheneSolid)
        self.parent = check.opt_inst_param(parent, "parent", GrapheneSolidHandle)


def build_solid_definition(represented_pipeline, solid_def_name):
    check.inst_param(represented_pipeline, "represented_pipeline", RepresentedPipeline)
    check.str_param(solid_def_name, "solid_def_name")

    solid_def_snap = represented_pipeline.get_solid_def_snap(solid_def_name)

    if isinstance(solid_def_snap, SolidDefSnap):
        return GrapheneSolidDefinition(represented_pipeline, solid_def_snap.name)

    if isinstance(solid_def_snap, CompositeSolidDefSnap):
        return GrapheneCompositeSolidDefinition(represented_pipeline, solid_def_snap.name)

    check.failed("Unknown solid definition type {type}".format(type=type(solid_def_snap)))


types = [
    GrapheneCompositeSolidDefinition,
    GrapheneInput,
    GrapheneInputDefinition,
    GrapheneInputMapping,
    GrapheneISolidDefinition,
    GrapheneOutput,
    GrapheneOutputDefinition,
    GrapheneOutputMapping,
    GrapheneResourceRequirement,
    GrapheneSolid,
    GrapheneSolidContainer,
    GrapheneSolidDefinition,
    GrapheneSolidHandle,
]
