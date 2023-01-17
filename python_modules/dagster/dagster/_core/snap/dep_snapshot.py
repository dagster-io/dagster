from collections import defaultdict
from typing import DefaultDict, Dict, List, Mapping, NamedTuple, Sequence

import dagster._check as check
from dagster._core.definitions import GraphDefinition
from dagster._core.definitions.dependency import DependencyType, Node, NodeInput
from dagster._serdes import whitelist_for_serdes


def build_solid_invocation_snap(
    icontains_solids: GraphDefinition, solid: Node
) -> "SolidInvocationSnap":
    check.inst_param(solid, "solid", Node)
    check.inst_param(icontains_solids, "icontains_solids", GraphDefinition)
    dep_structure = icontains_solids.dependency_structure

    input_def_snaps = []

    input_to_outputs_map = dep_structure.input_to_upstream_outputs_for_node(solid.name)

    for input_def in solid.definition.input_defs:
        node_input = NodeInput(solid, input_def)
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

    return SolidInvocationSnap(
        solid_name=solid.name,
        solid_def_name=solid.definition.name,
        tags=solid.tags,
        input_dep_snaps=input_def_snaps,
        is_dynamic_mapped=dep_structure.is_dynamic_mapped(solid.name),
    )


def build_dep_structure_snapshot_from_icontains_solids(
    icontains_solids: GraphDefinition,
) -> "DependencyStructureSnapshot":
    check.inst_param(icontains_solids, "icontains_solids", GraphDefinition)
    return DependencyStructureSnapshot(
        solid_invocation_snaps=[
            build_solid_invocation_snap(icontains_solids, solid)
            for solid in icontains_solids.solids
        ]
    )


@whitelist_for_serdes
class DependencyStructureSnapshot(
    NamedTuple(
        "_DependencyStructureSnapshot",
        [("solid_invocation_snaps", Sequence["SolidInvocationSnap"])],
    )
):
    def __new__(cls, solid_invocation_snaps: Sequence["SolidInvocationSnap"]):
        return super(DependencyStructureSnapshot, cls).__new__(
            cls,
            sorted(
                check.sequence_param(
                    solid_invocation_snaps, "solid_invocation_snaps", of_type=SolidInvocationSnap
                ),
                key=lambda si: si.solid_name,
            ),
        )


# Not actually serialized. Used within the dependency index
class InputHandle(
    NamedTuple("_InputHandle", [("solid_def_name", str), ("solid_name", str), ("input_name", str)])
):
    def __new__(cls, solid_def_name: str, solid_name: str, input_name: str):
        return super(InputHandle, cls).__new__(
            cls,
            solid_def_name=check.str_param(solid_def_name, "solid_def_name"),
            solid_name=check.str_param(solid_name, "solid_name"),
            input_name=check.str_param(input_name, "input_name"),
        )


# This class contains all the dependency information
# for a given "level" in a pipeline. So either the pipelines
# or within a composite solid
class DependencyStructureIndex:
    _invocations_dict: Dict[str, "SolidInvocationSnap"]
    _output_to_upstream_index: Mapping[str, Mapping[str, Sequence[InputHandle]]]

    def __init__(self, dep_structure_snapshot: DependencyStructureSnapshot):
        check.inst_param(
            dep_structure_snapshot, "dep_structure_snapshot", DependencyStructureSnapshot
        )
        self._invocations_dict = {
            si.solid_name: si for si in dep_structure_snapshot.solid_invocation_snaps
        }
        self._output_to_upstream_index = self._build_index(
            dep_structure_snapshot.solid_invocation_snaps
        )

    def _build_index(
        self, solid_invocation_snaps: Sequence["SolidInvocationSnap"]
    ) -> Mapping[str, Mapping[str, Sequence[InputHandle]]]:
        output_to_upstream_index: DefaultDict[str, Mapping[str, List[InputHandle]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for invocation in solid_invocation_snaps:
            for input_dep_snap in invocation.input_dep_snaps:
                for output_dep_snap in input_dep_snap.upstream_output_snaps:
                    output_to_upstream_index[output_dep_snap.solid_name][
                        output_dep_snap.output_name
                    ].append(
                        InputHandle(
                            solid_def_name=invocation.solid_def_name,
                            solid_name=invocation.solid_name,
                            input_name=input_dep_snap.input_name,
                        )
                    )

        return output_to_upstream_index

    @property
    def solid_invocation_names(self) -> Sequence[str]:
        return list(self._invocations_dict.keys())

    @property
    def solid_invocations(self) -> Sequence["SolidInvocationSnap"]:
        return list(self._invocations_dict.values())

    def get_invocation(self, solid_name: str) -> "SolidInvocationSnap":
        check.str_param(solid_name, "solid_name")
        return self._invocations_dict[solid_name]

    def has_invocation(self, solid_name: str) -> bool:
        return solid_name in self._invocations_dict

    def get_upstream_outputs(
        self, solid_name: str, input_name: str
    ) -> Sequence["OutputHandleSnap"]:
        check.str_param(solid_name, "solid_name")
        check.str_param(input_name, "input_name")

        for input_dep_snap in self.get_invocation(solid_name).input_dep_snaps:
            if input_dep_snap.input_name == input_name:
                return input_dep_snap.upstream_output_snaps

        check.failed(
            "Input {input_name} not found for solid {solid_name}".format(
                input_name=input_name,
                solid_name=solid_name,
            )
        )

    def get_upstream_output(self, solid_name: str, input_name: str) -> "OutputHandleSnap":
        check.str_param(solid_name, "solid_name")
        check.str_param(input_name, "input_name")

        outputs = self.get_upstream_outputs(solid_name, input_name)
        check.invariant(len(outputs) == 1)
        return outputs[0]

    def get_downstream_inputs(self, solid_name: str, output_name: str) -> Sequence[InputHandle]:
        check.str_param(solid_name, "solid_name")
        check.str_param(output_name, "output_name")
        return self._output_to_upstream_index[solid_name][output_name]


@whitelist_for_serdes
class OutputHandleSnap(
    NamedTuple("_OutputHandleSnap", [("solid_name", str), ("output_name", str)])
):
    def __new__(cls, solid_name: str, output_name: str):
        return super(OutputHandleSnap, cls).__new__(
            cls,
            solid_name=check.str_param(solid_name, "solid_name"),
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


@whitelist_for_serdes
class SolidInvocationSnap(
    NamedTuple(
        "_SolidInvocationSnap",
        [
            ("solid_name", str),
            ("solid_def_name", str),
            ("tags", Mapping[object, object]),
            ("input_dep_snaps", Sequence[InputDependencySnap]),
            ("is_dynamic_mapped", bool),
        ],
    )
):
    def __new__(
        cls,
        solid_name: str,
        solid_def_name: str,
        tags: Mapping[object, object],
        input_dep_snaps: Sequence[InputDependencySnap],
        is_dynamic_mapped: bool = False,
    ):
        return super(SolidInvocationSnap, cls).__new__(
            cls,
            solid_name=check.str_param(solid_name, "solid_name"),
            solid_def_name=check.str_param(solid_def_name, "solid_def_name"),
            tags=check.mapping_param(tags, "tags"),
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
