from collections import defaultdict
from typing import DefaultDict, Dict, List, Mapping, NamedTuple, Sequence

import dagster._check as check
from dagster._core.definitions import GraphDefinition
from dagster._core.definitions.dependency import DependencyType, Node, NodeInput
from dagster._serdes import whitelist_for_serdes


def build_node_invocation_snap(graph_def: GraphDefinition, node: Node) -> "NodeInvocationSnap":
    check.inst_param(node, "node", Node)
    check.inst_param(graph_def, "graph_def", GraphDefinition)
    dep_structure = graph_def.dependency_structure

    input_def_snaps = []

    input_to_outputs_map = dep_structure.input_to_upstream_outputs_for_node(node.name)

    for input_def in node.definition.input_defs:
        node_input = NodeInput(node, input_def)
        input_def_snaps.append(
            InputDependencySnap(
                input_def.name,
                upstream_output_snaps=[
                    OutputHandleSnap(node_output.node.name, node_output.output_def.name)
                    for node_output in input_to_outputs_map.get(node_input, [])
                ],
                is_dynamic_collect=dep_structure.get_dependency_type(node_input)
                == DependencyType.DYNAMIC_COLLECT,
            )
        )

    return NodeInvocationSnap(
        node_name=node.name,
        node_def_name=node.definition.name,
        tags=node.tags,
        input_dep_snaps=input_def_snaps,
        is_dynamic_mapped=dep_structure.is_dynamic_mapped(node.name),
    )


def build_dep_structure_snapshot_from_graph_def(
    graph_def: GraphDefinition,
) -> "DependencyStructureSnapshot":
    check.inst_param(graph_def, "graph_def", GraphDefinition)
    return DependencyStructureSnapshot(
        node_invocation_snaps=[
            build_node_invocation_snap(graph_def, node) for node in graph_def.nodes
        ]
    )


@whitelist_for_serdes(storage_field_names={"node_invocation_snaps": "solid_invocation_snaps"})
class DependencyStructureSnapshot(
    NamedTuple(
        "_DependencyStructureSnapshot",
        [("node_invocation_snaps", Sequence["NodeInvocationSnap"])],
    )
):
    def __new__(cls, node_invocation_snaps: Sequence["NodeInvocationSnap"]):
        return super(DependencyStructureSnapshot, cls).__new__(
            cls,
            sorted(
                check.sequence_param(
                    node_invocation_snaps, "node_invocation_snaps", of_type=NodeInvocationSnap
                ),
                key=lambda si: si.node_name,
            ),
        )


# Not actually serialized. Used within the dependency index
class InputHandle(
    NamedTuple("_InputHandle", [("node_def_name", str), ("node_name", str), ("input_name", str)])
):
    def __new__(cls, node_def_name: str, node_name: str, input_name: str):
        return super(InputHandle, cls).__new__(
            cls,
            node_def_name=check.str_param(node_def_name, "node_def_name"),
            node_name=check.str_param(node_name, "node_name"),
            input_name=check.str_param(input_name, "input_name"),
        )


# This class contains all the dependency information
# for a given "level" in a pipeline. So either the pipelines
# or within a graph
class DependencyStructureIndex:
    _invocations_dict: Dict[str, "NodeInvocationSnap"]
    _output_to_upstream_index: Mapping[str, Mapping[str, Sequence[InputHandle]]]

    def __init__(self, dep_structure_snapshot: DependencyStructureSnapshot):
        check.inst_param(
            dep_structure_snapshot, "dep_structure_snapshot", DependencyStructureSnapshot
        )
        self._invocations_dict = {
            si.node_name: si for si in dep_structure_snapshot.node_invocation_snaps
        }
        self._output_to_upstream_index = self._build_index(
            dep_structure_snapshot.node_invocation_snaps
        )

    def _build_index(
        self, node_invocation_snaps: Sequence["NodeInvocationSnap"]
    ) -> Mapping[str, Mapping[str, Sequence[InputHandle]]]:
        output_to_upstream_index: DefaultDict[str, Mapping[str, List[InputHandle]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for invocation in node_invocation_snaps:
            for input_dep_snap in invocation.input_dep_snaps:
                for output_dep_snap in input_dep_snap.upstream_output_snaps:
                    output_to_upstream_index[output_dep_snap.node_name][
                        output_dep_snap.output_name
                    ].append(
                        InputHandle(
                            node_def_name=invocation.node_def_name,
                            node_name=invocation.node_name,
                            input_name=input_dep_snap.input_name,
                        )
                    )

        return output_to_upstream_index

    @property
    def node_invocation_names(self) -> Sequence[str]:
        return list(self._invocations_dict.keys())

    @property
    def node_invocations(self) -> Sequence["NodeInvocationSnap"]:
        return list(self._invocations_dict.values())

    def get_invocation(self, node_name: str) -> "NodeInvocationSnap":
        check.str_param(node_name, "node_name")
        return self._invocations_dict[node_name]

    def has_invocation(self, node_name: str) -> bool:
        return node_name in self._invocations_dict

    def get_upstream_outputs(self, node_name: str, input_name: str) -> Sequence["OutputHandleSnap"]:
        check.str_param(node_name, "node_name")
        check.str_param(input_name, "input_name")

        for input_dep_snap in self.get_invocation(node_name).input_dep_snaps:
            if input_dep_snap.input_name == input_name:
                return input_dep_snap.upstream_output_snaps

        check.failed(
            "Input {input_name} not found for node {node_name}".format(
                input_name=input_name,
                node_name=node_name,
            )
        )

    def get_upstream_output(self, node_name: str, input_name: str) -> "OutputHandleSnap":
        check.str_param(node_name, "node_name")
        check.str_param(input_name, "input_name")

        outputs = self.get_upstream_outputs(node_name, input_name)
        check.invariant(len(outputs) == 1)
        return outputs[0]

    def get_downstream_inputs(self, node_name: str, output_name: str) -> Sequence[InputHandle]:
        check.str_param(node_name, "node_name")
        check.str_param(output_name, "output_name")
        return self._output_to_upstream_index[node_name][output_name]


@whitelist_for_serdes(storage_field_names={"node_name": "solid_name"})
class OutputHandleSnap(NamedTuple("_OutputHandleSnap", [("node_name", str), ("output_name", str)])):
    def __new__(cls, node_name: str, output_name: str):
        return super(OutputHandleSnap, cls).__new__(
            cls,
            node_name=check.str_param(node_name, "node_name"),
            output_name=check.str_param(output_name, "output_name"),
        )


@whitelist_for_serdes
class InputDependencySnap(
    NamedTuple(
        "_InputDependencySnap",
        [
            ("input_name", str),
            ("upstream_output_snaps", Sequence[OutputHandleSnap]),
            ("is_dynamic_collect", bool),
        ],
    )
):
    def __new__(
        cls,
        input_name: str,
        upstream_output_snaps: Sequence[OutputHandleSnap],
        is_dynamic_collect: bool = False,
    ):
        return super(InputDependencySnap, cls).__new__(
            cls,
            input_name=check.str_param(input_name, "input_name"),
            upstream_output_snaps=check.sequence_param(
                upstream_output_snaps, "upstream_output_snaps", of_type=OutputHandleSnap
            ),
            # Could be derived from a dependency type enum as well
            # if we wanted to persist that
            is_dynamic_collect=check.bool_param(is_dynamic_collect, "is_dynamic_collect"),
        )


# Use old names in storage for backcompat
@whitelist_for_serdes(
    storage_name="SolidInvocationSnap",
    storage_field_names={"node_name": "solid_name", "node_def_name": "solid_def_name"},
)
class NodeInvocationSnap(
    NamedTuple(
        "_NodeInvocationSnap",
        [
            ("node_name", str),
            ("node_def_name", str),
            ("tags", Mapping[str, str]),
            ("input_dep_snaps", Sequence[InputDependencySnap]),
            ("is_dynamic_mapped", bool),
        ],
    )
):
    def __new__(
        cls,
        node_name: str,
        node_def_name: str,
        tags: Mapping[str, str],
        input_dep_snaps: Sequence[InputDependencySnap],
        is_dynamic_mapped: bool = False,
    ):
        return super(NodeInvocationSnap, cls).__new__(
            cls,
            node_name=check.str_param(node_name, "node_name"),
            node_def_name=check.str_param(node_def_name, "node_def_name"),
            tags=check.mapping_param(tags, "tags", key_type=str, value_type=str),
            input_dep_snaps=check.sequence_param(
                input_dep_snaps, "input_dep_snaps", of_type=InputDependencySnap
            ),
            is_dynamic_mapped=check.bool_param(is_dynamic_mapped, "is_dynamic_mapped"),
        )

    def input_dep_snap(self, input_name: str) -> InputDependencySnap:
        for inp_snap in self.input_dep_snaps:
            if inp_snap.input_name == input_name:
                return inp_snap

        check.failed(f"No input found named {input_name}")
