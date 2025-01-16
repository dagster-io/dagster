from collections.abc import Mapping, Sequence
from functools import lru_cache
from typing import TYPE_CHECKING, Optional, Union

import dagster._check as check
import graphene
from dagster._core.definitions import NodeHandle
from dagster._core.remote_representation import RepresentedJob
from dagster._core.remote_representation.external import RemoteJob
from dagster._core.remote_representation.historical import HistoricalJob
from dagster._core.snap import DependencyStructureIndex, GraphDefSnap, OpDefSnap
from dagster._core.snap.node import InputMappingSnap, OutputMappingSnap
from dagster._core.storage.dagster_run import RunsFilter
from dagster._core.storage.tags import COMPUTE_KIND_TAG, LEGACY_COMPUTE_KIND_TAG

from dagster_graphql.implementation.events import iterate_metadata_entries
from dagster_graphql.schema.config_types import GrapheneConfigTypeField
from dagster_graphql.schema.dagster_types import (
    GrapheneDagsterType,
    GrapheneDagsterTypeUnion,
    to_dagster_type,
)
from dagster_graphql.schema.errors import GrapheneError
from dagster_graphql.schema.logs.events import GrapheneRunStepStats
from dagster_graphql.schema.metadata import GrapheneMetadataEntry, GrapheneMetadataItemDefinition
from dagster_graphql.schema.util import ResolveInfo, non_null_list

if TYPE_CHECKING:
    from dagster_graphql.schema.asset_graph import GrapheneAssetNode


class _ArgNotPresentSentinel:
    pass


class GrapheneInputDefinition(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    type = graphene.NonNull(GrapheneDagsterType)
    metadata_entries = non_null_list(GrapheneMetadataEntry)

    class Meta:
        name = "InputDefinition"

    def __init__(self, represented_job: RepresentedJob, solid_def_name: str, input_def_name: str):
        self._represented_job = check.inst_param(
            represented_job, "represented_pipeline", RepresentedJob
        )
        check.str_param(solid_def_name, "solid_def_name")
        check.str_param(input_def_name, "input_def_name")
        node_def_snap = self._represented_job.get_node_def_snap(solid_def_name)
        self._input_def_snap = node_def_snap.get_input_snap(input_def_name)
        super().__init__(
            name=self._input_def_snap.name,
            description=self._input_def_snap.description,
        )

    def resolve_type(self, _graphene_info: ResolveInfo) -> GrapheneDagsterTypeUnion:
        return to_dagster_type(
            self._represented_job.job_snapshot.dagster_type_namespace_snapshot.get_dagster_type_snap,
            self._represented_job.job_snapshot.config_schema_snapshot.get_config_snap,
            self._input_def_snap.dagster_type_key,
        )

    def resolve_metadata_entries(self, _graphene_info):
        return list(iterate_metadata_entries(self._input_def_snap.metadata))


class GrapheneOutputDefinition(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    is_dynamic = graphene.Boolean()
    type = graphene.NonNull(GrapheneDagsterType)
    metadata_entries = non_null_list(GrapheneMetadataEntry)

    class Meta:
        name = "OutputDefinition"

    def __init__(
        self,
        represented_job: RepresentedJob,
        solid_def_name: str,
        output_def_name: str,
        is_dynamic: bool,
    ):
        self._represented_job = check.inst_param(represented_job, "represented_job", RepresentedJob)
        check.str_param(solid_def_name, "solid_def_name")
        check.str_param(output_def_name, "output_def_name")

        node_def_snap = represented_job.get_node_def_snap(solid_def_name)
        self._output_def_snap = node_def_snap.get_output_snap(output_def_name)

        super().__init__(
            name=self._output_def_snap.name,
            description=self._output_def_snap.description,
            is_dynamic=is_dynamic,
        )

    def resolve_type(self, _graphene_info) -> GrapheneDagsterTypeUnion:
        return to_dagster_type(
            self._represented_job.job_snapshot.dagster_type_namespace_snapshot.get_dagster_type_snap,
            self._represented_job.job_snapshot.config_schema_snapshot.get_config_snap,
            self._output_def_snap.dagster_type_key,
        )

    def resolve_metadata_entries(self, _graphene_info):
        return list(iterate_metadata_entries(self._output_def_snap.metadata))


class GrapheneInput(graphene.ObjectType):
    solid = graphene.NonNull(lambda: GrapheneSolid)
    definition = graphene.NonNull(GrapheneInputDefinition)
    depends_on = non_null_list(lambda: GrapheneOutput)
    is_dynamic_collect = graphene.NonNull(graphene.Boolean)

    class Meta:
        name = "Input"

    def __init__(
        self,
        represented_pipeline: RepresentedJob,
        current_dep_structure: DependencyStructureIndex,
        solid_name: str,
        input_name: str,
    ):
        self._represented_pipeline = check.inst_param(
            represented_pipeline, "represented_pipeline", RepresentedJob
        )
        self._current_dep_structure = check.inst_param(
            current_dep_structure, "current_dep_structure", DependencyStructureIndex
        )
        self._solid_name = check.str_param(solid_name, "solid_name")
        self._input_name = check.str_param(input_name, "input_name")
        self._solid_invocation_snap = current_dep_structure.get_invocation(solid_name)
        self._solid_def_snap = represented_pipeline.get_node_def_snap(
            self._solid_invocation_snap.node_def_name
        )
        self._input_def_snap = self._solid_def_snap.get_input_snap(input_name)

        super().__init__()

    def resolve_solid(self, _graphene_info: ResolveInfo) -> "GrapheneSolid":
        return GrapheneSolid(
            self._represented_pipeline, self._solid_name, self._current_dep_structure
        )

    def resolve_definition(self, _graphene_info: ResolveInfo) -> GrapheneInputDefinition:
        return GrapheneInputDefinition(
            self._represented_pipeline,
            self._solid_def_snap.name,
            self._input_def_snap.name,
        )

    def resolve_depends_on(self, _graphene_info: ResolveInfo) -> Sequence["GrapheneOutput"]:
        return [
            GrapheneOutput(
                self._represented_pipeline,
                self._current_dep_structure,
                output_handle_snap.node_name,
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
            represented_pipeline, "represented_pipeline", RepresentedJob
        )
        self._current_dep_structure = check.inst_param(
            current_dep_structure, "current_dep_structure", DependencyStructureIndex
        )
        self._solid_name = check.str_param(solid_name, "solid_name")
        self._output_name = check.str_param(output_name, "output_name")
        self._solid_invocation_snap = current_dep_structure.get_invocation(solid_name)
        self._solid_def_snap = represented_pipeline.get_node_def_snap(
            self._solid_invocation_snap.node_def_name
        )
        self._output_def_snap = self._solid_def_snap.get_output_snap(output_name)
        super().__init__()

    def resolve_solid(self, _) -> "GrapheneSolid":
        return GrapheneSolid(
            self._represented_pipeline, self._solid_name, self._current_dep_structure
        )

    def resolve_definition(self, _graphene_info: ResolveInfo) -> GrapheneOutputDefinition:
        return GrapheneOutputDefinition(
            self._represented_pipeline,
            self._solid_def_snap.name,
            self._output_name,
            self._output_def_snap.is_dynamic,
        )

    def resolve_depended_by(self, _graphene_info: ResolveInfo) -> Sequence[GrapheneInput]:
        return [
            GrapheneInput(
                self._represented_pipeline,
                self._current_dep_structure,
                input_handle_snap.node_name,
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
        input_mapping_snap,
    ):
        self._represented_pipeline = check.inst_param(
            represented_pipeline, "represented_pipeline", RepresentedJob
        )
        self._current_dep_index = check.inst_param(
            current_dep_index, "current_dep_index", DependencyStructureIndex
        )
        self._input_mapping_snap = check.inst_param(
            input_mapping_snap, "input_mapping_snap", InputMappingSnap
        )
        self._solid_def_snap = represented_pipeline.get_node_def_snap(solid_def_name)
        super().__init__()

    def resolve_mapped_input(self, _graphene_info):
        return GrapheneInput(
            self._represented_pipeline,
            self._current_dep_index,
            self._input_mapping_snap.mapped_node_name,
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
        self, represented_pipeline, current_dep_index, solid_def_name, output_mapping_snap
    ):
        self._represented_pipeline = check.inst_param(
            represented_pipeline, "represented_pipeline", RepresentedJob
        )
        self._current_dep_index = check.inst_param(
            current_dep_index, "current_dep_index", DependencyStructureIndex
        )
        self._output_mapping_snap = check.inst_param(
            output_mapping_snap, "output_mapping_snap", OutputMappingSnap
        )
        self._solid_def_snap = represented_pipeline.get_node_def_snap(solid_def_name)
        self._output_def_snap = self._solid_def_snap.get_output_snap(
            output_mapping_snap.external_output_name
        )

        super().__init__()

    def resolve_mapped_output(self, _graphene_info):
        return GrapheneOutput(
            self._represented_pipeline,
            self._current_dep_index,
            self._output_mapping_snap.mapped_node_name,
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
    check.inst_param(represented_pipeline, "represented_pipeline", RepresentedJob)
    return sorted(
        [
            GrapheneSolid(represented_pipeline, solid_name, current_dep_index)
            for solid_name in current_dep_index.node_invocation_names
        ],
        key=lambda solid: solid.name,
    )


def _build_solid_handles(
    represented_pipeline: RepresentedJob,
    current_dep_index: DependencyStructureIndex,
    parent: Optional["GrapheneSolidHandle"] = None,
) -> Sequence["GrapheneSolidHandle"]:
    check.inst_param(represented_pipeline, "represented_pipeline", RepresentedJob)
    check.opt_inst_param(parent, "parent", GrapheneSolidHandle)
    all_handle: list[GrapheneSolidHandle] = []
    for solid_invocation in current_dep_index.node_invocations:
        solid_name, solid_def_name = solid_invocation.node_name, solid_invocation.node_def_name
        handle = GrapheneSolidHandle(
            solid=GrapheneSolid(represented_pipeline, solid_name, current_dep_index),
            handle=NodeHandle(solid_name, parent.handleID if parent else None),
            parent=parent if parent else None,
        )
        solid_def_snap = represented_pipeline.get_node_def_snap(solid_def_name)
        if isinstance(solid_def_snap, GraphDefSnap):
            all_handle += _build_solid_handles(
                represented_pipeline,
                represented_pipeline.get_dep_structure_index(solid_def_name),
                handle,
            )

        all_handle.append(handle)

    return all_handle


@lru_cache(maxsize=32)
def build_solid_handles(
    represented_pipeline: RepresentedJob,
) -> Mapping[str, "GrapheneSolidHandle"]:
    check.inst_param(represented_pipeline, "represented_pipeline", RepresentedJob)
    return {
        str(item.handleID): item
        for item in _build_solid_handles(
            represented_pipeline, represented_pipeline.dep_structure_index
        )
    }


class GrapheneISolidDefinition(graphene.Interface):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    metadata = non_null_list(GrapheneMetadataItemDefinition)
    input_definitions = non_null_list(GrapheneInputDefinition)
    output_definitions = non_null_list(GrapheneOutputDefinition)
    assetNodes = non_null_list("dagster_graphql.schema.asset_graph.GrapheneAssetNode")
    pools = non_null_list(graphene.String)

    class Meta:
        name = "ISolidDefinition"


class ISolidDefinitionMixin:
    def __init__(self, represented_pipeline: RepresentedJob, solid_def_name: str):
        self._represented_pipeline = check.inst_param(
            represented_pipeline, "represented_pipeline", RepresentedJob
        )
        check.str_param(solid_def_name, "solid_def_name")
        self._solid_def_snap = represented_pipeline.get_node_def_snap(solid_def_name)

    def resolve_metadata(self, _graphene_info):
        metadata_items = []
        for key, val in self._solid_def_snap.tags.items():
            metadata_items.append(GrapheneMetadataItemDefinition(key=key, value=val))
            # Backcompat for legacy system tags. Older code servers may report the compute kind under
            # the legacy tag. Code servers running versions after deprecation of the legacy tag may
            # have both the legacy and current tag set. We can't patch this at the Snap level
            # because the host process will complain about mismatched snap IDs
            if key == LEGACY_COMPUTE_KIND_TAG and COMPUTE_KIND_TAG not in self._solid_def_snap.tags:
                metadata_items.append(
                    GrapheneMetadataItemDefinition(key=COMPUTE_KIND_TAG, value=val)
                )
        return metadata_items

    @property
    def solid_def_name(self) -> str:
        return self._solid_def_snap.name

    def resolve_input_definitions(self, _graphene_info) -> Sequence[GrapheneInputDefinition]:
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

    def resolve_assetNodes(self, graphene_info: ResolveInfo) -> Sequence["GrapheneAssetNode"]:
        from dagster_graphql.schema.asset_graph import GrapheneAssetNode

        # This is a workaround for the fact that asset info is not persisted in pipeline snapshots.
        if isinstance(self._represented_pipeline, HistoricalJob):
            return []
        else:
            assert isinstance(self._represented_pipeline, RemoteJob)
            job_asset_nodes = graphene_info.context.get_assets_in_job(
                self._represented_pipeline.handle.to_selector()
            )
            remote_nodes = [
                remote_node
                for remote_node in job_asset_nodes
                if (
                    (remote_node.asset_node_snap.node_definition_name == self.solid_def_name)
                    or (
                        remote_node.asset_node_snap.graph_name
                        and remote_node.asset_node_snap.graph_name == self.solid_def_name
                    )
                )
            ]

            return [
                GrapheneAssetNode(
                    remote_node=remote_node,
                )
                for remote_node in remote_nodes
            ]

    def resolve_pools(self, _graphene_info) -> Sequence[str]:
        if isinstance(self._solid_def_snap, OpDefSnap):
            return [self._solid_def_snap.pool] if self._solid_def_snap.pool else []
        if isinstance(self._solid_def_snap, GraphDefSnap):
            return list(self._solid_def_snap.pools)
        return []


class GrapheneSolidDefinition(graphene.ObjectType, ISolidDefinitionMixin):
    config_field = graphene.Field(GrapheneConfigTypeField)
    required_resources = non_null_list(GrapheneResourceRequirement)
    pool = graphene.String()

    class Meta:
        interfaces = (GrapheneISolidDefinition,)
        name = "SolidDefinition"

    def __init__(self, represented_pipeline: RepresentedJob, solid_def_name: str):
        check.inst_param(represented_pipeline, "represented_pipeline", RepresentedJob)
        _solid_def_snap = represented_pipeline.get_node_def_snap(solid_def_name)
        if not isinstance(_solid_def_snap, OpDefSnap):
            check.failed("Expected OpDefSnap")
        self._solid_def_snap = _solid_def_snap
        super().__init__(name=solid_def_name, description=self._solid_def_snap.description)
        ISolidDefinitionMixin.__init__(self, represented_pipeline, solid_def_name)

    def resolve_config_field(
        self, _graphene_info: ResolveInfo
    ) -> Optional[GrapheneConfigTypeField]:
        return (
            GrapheneConfigTypeField(
                get_config_type=self._represented_pipeline.config_schema_snapshot.get_config_snap,
                field_snap=self._solid_def_snap.config_field_snap,
            )
            if self._solid_def_snap.config_field_snap
            else None
        )

    def resolve_required_resources(
        self, _graphene_info: ResolveInfo
    ) -> Sequence[GrapheneResourceRequirement]:
        return [
            GrapheneResourceRequirement(key) for key in self._solid_def_snap.required_resource_keys
        ]

    def resolve_pool(self, _graphene_info: ResolveInfo) -> Optional[str]:
        return self._solid_def_snap.pool


class GrapheneSolidStepStatsUnavailableError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "SolidStepStatusUnavailableError"


class GrapheneSolidStepStatsConnection(graphene.ObjectType):
    nodes = non_null_list(GrapheneRunStepStats)

    class Meta:
        name = "SolidStepStatsConnection"


class GrapheneSolidStepStatsOrError(graphene.Union):
    class Meta:
        types = (GrapheneSolidStepStatsConnection, GrapheneSolidStepStatsUnavailableError)
        name = "SolidStepStatsOrError"


class GrapheneSolid(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    definition = graphene.NonNull(lambda: GrapheneISolidDefinition)
    inputs = non_null_list(GrapheneInput)
    outputs = non_null_list(GrapheneOutput)

    is_dynamic_mapped = graphene.NonNull(graphene.Boolean)

    class Meta:
        name = "Solid"

    def __init__(
        self,
        represented_pipeline: RepresentedJob,
        solid_name: str,
        current_dep_structure: DependencyStructureIndex,
    ):
        self._represented_pipeline = check.inst_param(
            represented_pipeline, "represented_pipeline", RepresentedJob
        )

        check.str_param(solid_name, "solid_name")
        self._current_dep_structure = check.inst_param(
            current_dep_structure, "current_dep_structure", DependencyStructureIndex
        )
        self._solid_invocation_snap = current_dep_structure.get_invocation(solid_name)
        self._solid_def_snap = represented_pipeline.get_node_def_snap(
            self._solid_invocation_snap.node_def_name
        )
        super().__init__(name=solid_name)

    def get_solid_definition_name(self) -> str:
        return self._solid_def_snap.name

    def get_solid_definition(
        self,
    ) -> Union[GrapheneSolidDefinition, "GrapheneCompositeSolidDefinition"]:
        return build_solid_definition(self._represented_pipeline, self._solid_def_snap.name)

    def get_is_dynamic_mapped(self) -> bool:
        return self._solid_invocation_snap.is_dynamic_mapped

    def get_is_composite(self) -> bool:
        return isinstance(self._solid_def_snap, GraphDefSnap)

    def get_pipeline_name(self) -> str:
        return self._represented_pipeline.name

    def resolve_definition(
        self, _graphene_info: ResolveInfo
    ) -> Union[GrapheneSolidDefinition, "GrapheneCompositeSolidDefinition"]:
        return self.get_solid_definition()

    def resolve_inputs(self, _graphene_info: ResolveInfo) -> Sequence[GrapheneInput]:
        return [
            GrapheneInput(
                self._represented_pipeline,
                self._current_dep_structure,
                self._solid_invocation_snap.node_name,
                input_def_snap.name,
            )
            for input_def_snap in self._solid_def_snap.input_def_snaps
        ]

    def resolve_outputs(self, _graphene_info: ResolveInfo) -> Sequence[GrapheneOutput]:
        return [
            GrapheneOutput(
                self._represented_pipeline,
                self._current_dep_structure,
                self._solid_invocation_snap.node_name,
                output_def_snap.name,
            )
            for output_def_snap in self._solid_def_snap.output_def_snaps
        ]

    def resolve_is_dynamic_mapped(self, _graphene_info: ResolveInfo) -> bool:
        return self._solid_invocation_snap.is_dynamic_mapped


class GrapheneSolidHandle(graphene.ObjectType):
    handleID = graphene.NonNull(graphene.String)
    solid = graphene.NonNull(GrapheneSolid)
    parent = graphene.Field(lambda: GrapheneSolidHandle)
    stepStats = graphene.Field(GrapheneSolidStepStatsOrError, limit=graphene.Int())

    class Meta:
        name = "SolidHandle"

    def __init__(
        self,
        handle: NodeHandle,
        solid: GrapheneSolid,
        parent: Optional["GrapheneSolidHandle"] = None,
    ):
        super().__init__(
            handleID=check.inst_param(handle, "handle", NodeHandle),
            solid=check.inst_param(solid, "solid", GrapheneSolid),
            parent=check.opt_inst_param(parent, "parent", GrapheneSolidHandle),
        )
        self._solid = solid

    def resolve_stepStats(self, _graphene_info: ResolveInfo, limit: Optional[int]):
        if self._solid.get_is_dynamic_mapped():
            return GrapheneSolidStepStatsUnavailableError(
                message="Step stats are not available for dynamically-mapped ops"
            )

        if self._solid.get_is_composite():
            return GrapheneSolidStepStatsUnavailableError(
                message="Step stats are not available for composite solids / subgraphs"
            )

        instance = _graphene_info.context.instance
        runs_filter = RunsFilter(job_name=self._solid.get_pipeline_name())
        runs = instance.get_runs(runs_filter, limit=limit)
        nodes = []
        for run in runs:
            stats = instance.get_run_step_stats(run.run_id, [str(self.handleID)])
            if len(stats):
                nodes.append(GrapheneRunStepStats(stats[0]))
        return GrapheneSolidStepStatsConnection(nodes=nodes)


class GrapheneSolidContainer(graphene.Interface):
    id = graphene.NonNull(graphene.ID)
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    solids = non_null_list(GrapheneSolid)
    solid_handle = graphene.Field(
        GrapheneSolidHandle,
        handleID=graphene.Argument(graphene.NonNull(graphene.String)),
    )
    solid_handles = graphene.Field(
        non_null_list(GrapheneSolidHandle), parentHandleID=graphene.String()
    )
    modes = non_null_list("dagster_graphql.schema.pipelines.mode.GrapheneMode")

    class Meta:
        name = "SolidContainer"


class GrapheneCompositeSolidDefinition(graphene.ObjectType, ISolidDefinitionMixin):
    id = graphene.NonNull(graphene.ID)
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    solids = non_null_list(GrapheneSolid)
    input_mappings = non_null_list(GrapheneInputMapping)
    output_mappings = non_null_list(GrapheneOutputMapping)
    solid_handle = graphene.Field(
        GrapheneSolidHandle,
        handleID=graphene.Argument(graphene.NonNull(graphene.String)),
    )
    solid_handles = graphene.Field(
        non_null_list(GrapheneSolidHandle), parentHandleID=graphene.String()
    )
    modes = non_null_list("dagster_graphql.schema.pipelines.mode.GrapheneMode")

    class Meta:
        interfaces = (GrapheneISolidDefinition, GrapheneSolidContainer)
        name = "CompositeSolidDefinition"

    def __init__(self, represented_pipeline: RepresentedJob, solid_def_name: str):
        self._represented_pipeline = check.inst_param(
            represented_pipeline, "represented_pipeline", RepresentedJob
        )
        self._solid_def_snap = represented_pipeline.get_node_def_snap(solid_def_name)
        self._comp_solid_dep_index = represented_pipeline.get_dep_structure_index(solid_def_name)
        super().__init__(name=solid_def_name, description=self._solid_def_snap.description)
        ISolidDefinitionMixin.__init__(self, represented_pipeline, solid_def_name)

    def resolve_id(self, _graphene_info: ResolveInfo) -> str:
        return (
            f"{self._represented_pipeline.identifying_job_snapshot_id}:{self._solid_def_snap.name}"
        )

    def resolve_solids(self, _graphene_info: ResolveInfo) -> Sequence[GrapheneSolid]:
        return build_solids(self._represented_pipeline, self._comp_solid_dep_index)

    def resolve_output_mappings(
        self, _graphene_info: ResolveInfo
    ) -> Sequence[GrapheneOutputMapping]:
        assert isinstance(self._solid_def_snap, GraphDefSnap)
        return [
            GrapheneOutputMapping(
                self._represented_pipeline,
                self._comp_solid_dep_index,
                self._solid_def_snap.name,
                output_mapping_snap,
            )
            for output_mapping_snap in self._solid_def_snap.output_mapping_snaps
        ]

    def resolve_input_mappings(self, _graphene_info: ResolveInfo) -> Sequence[GrapheneInputMapping]:
        assert isinstance(self._solid_def_snap, GraphDefSnap)
        return [
            GrapheneInputMapping(
                self._represented_pipeline,
                self._comp_solid_dep_index,
                self._solid_def_snap.name,
                input_mapping_snap,
            )
            for input_mapping_snap in self._solid_def_snap.input_mapping_snaps
        ]

    def resolve_solid_handle(
        self, _graphene_info: ResolveInfo, handleID: str
    ) -> Optional[GrapheneSolidHandle]:
        return build_solid_handles(self._represented_pipeline).get(handleID)

    def resolve_solid_handles(
        self, _graphene_info: ResolveInfo, parentHandleID: Optional[str] = None
    ) -> Sequence[GrapheneSolidHandle]:
        handles = build_solid_handles(self._represented_pipeline)

        if parentHandleID == "":
            handles = {key: handle for key, handle in handles.items() if not handle.parent}
        elif parentHandleID is not None:
            handles = {
                key: handle
                for key, handle in handles.items()
                if handle.parent and str(handle.parent.handleID) == parentHandleID
            }

        return [handles[key] for key in sorted(handles)]

    def resolve_modes(self, _graphene_info):
        # returns empty list... composite solids don't have modes, this is a vestige of the old
        # pipeline explorer, which expected all solid containers to be pipelines
        return []


def build_solid_definition(
    represented_pipeline: RepresentedJob, solid_def_name: str
) -> Union[GrapheneSolidDefinition, GrapheneCompositeSolidDefinition]:
    check.inst_param(represented_pipeline, "represented_pipeline", RepresentedJob)
    check.str_param(solid_def_name, "solid_def_name")

    solid_def_snap = represented_pipeline.get_node_def_snap(solid_def_name)

    if isinstance(solid_def_snap, OpDefSnap):
        return GrapheneSolidDefinition(represented_pipeline, solid_def_snap.name)

    if isinstance(solid_def_snap, GraphDefSnap):
        return GrapheneCompositeSolidDefinition(represented_pipeline, solid_def_snap.name)

    check.failed(f"Unknown solid definition type {type(solid_def_snap)}")


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
