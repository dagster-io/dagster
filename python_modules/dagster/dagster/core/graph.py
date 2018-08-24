from collections import defaultdict
from toposort import toposort_flatten

from dagster import check

from .definitions import (
    DependencyDefinition,
    DependencyStructure,
    InputToOutputHandleDict,
    PipelineDefinition,
    SolidDefinition,
    _build_named_dict,
    create_handle_dict,
)


def _create_adjacency_lists(solids, dep_structure):
    check.list_param(solids, 'solids', of_type=SolidDefinition)
    check.inst_param(dep_structure, 'dep_structure', DependencyStructure)

    visit_dict = {s.name: False for s in solids}
    forward_edges = {s.name: set() for s in solids}
    backward_edges = {s.name: set() for s in solids}

    def visit(solid_name):
        if visit_dict[solid_name]:
            return

        visit_dict[solid_name] = True

        for output_handle in dep_structure.deps_of_solid(solid_name):
            forward_node = output_handle.solid.name
            backward_node = solid_name
            if forward_node in forward_edges:
                forward_edges[forward_node].add(backward_node)
                backward_edges[backward_node].add(forward_node)
                visit(forward_node)

    for s in solids:
        visit(s.name)

    return (forward_edges, backward_edges)


def _dependency_structure_to_dep_dict(dependency_structure):
    dep_dict = defaultdict(dict)
    for input_handle, output_handle in dependency_structure.items():
        dep_dict[input_handle.solid.name][input_handle.input_def.name] = DependencyDefinition(
            solid=output_handle.solid.name,
            output=output_handle.output_def.name,
        )
    return dep_dict


class ExecutionGraph:
    @staticmethod
    def from_pipeline(pipeline):
        check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        return ExecutionGraph(pipeline, pipeline.solids, pipeline.dependency_structure)

    @staticmethod
    def from_pipeline_subset(pipeline, from_solids, through_solids, injected_solids):
        check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        check.list_param(from_solids, 'from_solids', of_type=str)
        check.list_param(through_solids, 'through_solids', of_type=str)
        graph = ExecutionGraph.from_pipeline(pipeline)
        return _create_subgraph(graph, from_solids, through_solids).augment(injected_solids)

    def to_pipeline(self):
        return PipelineDefinition(
            solids=self.solids,
            dependencies=_dependency_structure_to_dep_dict(self.dependency_structure),
            context_definitions=self.pipeline.context_definitions
        )

    def augment(self, injected_solids):

        new_deps = defaultdict(dict)
        new_solids = []

        for from_solid_name, targets_by_input in injected_solids.items():
            for from_input_name, target_solid in targets_by_input.items():
                new_solids.append(target_solid)
                new_deps[from_solid_name][from_input_name] = DependencyDefinition(
                    solid=target_solid.name
                )

        check.list_param(new_solids, 'new_solids', of_type=SolidDefinition)

        solids = self.solids + new_solids

        solid_dict = _build_named_dict(solids)

        handle_dict = InputToOutputHandleDict()
        for input_handle, output_handle in self.dependency_structure.items():
            handle_dict[input_handle] = output_handle

        for input_handle, output_handle in create_handle_dict(solid_dict, new_deps).items():
            handle_dict[input_handle] = output_handle

        return ExecutionGraph(self.pipeline, solids, DependencyStructure(handle_dict))

    def __init__(self, pipeline, solids, dependency_structure):
        self.pipeline = pipeline
        solids = check.list_param(solids, 'solids', of_type=SolidDefinition)

        self.dependency_structure = check.inst_param(
            dependency_structure, 'dependency_structure', DependencyStructure
        )

        self._solid_dict = {solid.name: solid for solid in solids}

        for input_handle in dependency_structure.input_handles():
            check.invariant(input_handle.solid.name in self._solid_dict)

        solid_names = set([solid.name for solid in solids])
        check.invariant(len(solid_names) == len(solids), 'must have unique names')

        self.forward_edges, self.backward_edges = _create_adjacency_lists(
            solids, self.dependency_structure
        )
        self.topological_order = toposort_flatten(self.backward_edges, sort=True)

        self._transitive_deps = {}

    @property
    def topological_solids(self):
        return [self._solid_dict[name] for name in self.topological_order]

    @property
    def solids(self):
        return list(self._solid_dict.values())

    def solid_named(self, name):
        check.str_param(name, 'name')
        return self._solid_dict[name]

    def transitive_dependencies_of(self, solid_name):
        check.str_param(solid_name, 'solid_name')

        if solid_name in self._transitive_deps:
            return self._transitive_deps[solid_name]

        trans_deps = set()
        solid = self._solid_dict[solid_name]
        for input_def in solid.input_defs:
            input_handle = solid.input_handle(input_def.name)
            if self.dependency_structure.has_dep(input_handle):
                output_handle = self.dependency_structure.get_dep(input_handle)
                trans_deps.add(output_handle.solid.name)
                trans_deps.union(self.transitive_dependencies_of(output_handle.solid.name))

        self._transitive_deps[solid_name] = trans_deps
        return self._transitive_deps[solid_name]

    def _check_solid_name(self, solid_name):
        check.str_param(solid_name, 'output_name')
        check.param_invariant(
            solid_name in self._solid_dict, 'output_name',
            f'Solid {solid_name} must exist in {list(self._solid_dict.keys())}'
        )

    def create_execution_subgraph(self, from_solids, to_solids):
        check.list_param(from_solids, 'from_solids', of_type=str)
        check.list_param(to_solids, 'to_solids', of_type=str)

        involved_solid_set = self._compute_involved_solid_set(from_solids, to_solids)

        involved_solids = [self._solid_dict[name] for name in involved_solid_set]

        handle_dict = InputToOutputHandleDict()

        for solid in involved_solids:
            for input_def in solid.input_defs:
                input_handle = solid.input_handle(input_def.name)
                if self.dependency_structure.has_dep(input_handle):
                    handle_dict[input_handle] = self.dependency_structure.get_dep(input_handle)

        return ExecutionGraph(self.pipeline, involved_solids, DependencyStructure(handle_dict))

    def _compute_involved_solid_set(self, from_solids, to_solids):
        from_solid_set = set(from_solids)
        involved_solid_set = from_solid_set

        def visit(solid):
            if solid.name in involved_solid_set:
                return

            involved_solid_set.add(solid.name)

            for input_def in solid.input_defs:
                input_handle = solid.input_handle(input_def.name)
                if not self.dependency_structure.has_dep(input_handle):
                    continue

                output_handle = self.dependency_structure.get_dep(input_handle)

                next_solid = output_handle.solid.name
                if next_solid in from_solid_set:
                    continue

                visit(self._solid_dict[next_solid])

        for to_solid in to_solids:
            visit(self._solid_dict[to_solid])

        return involved_solid_set


def _build_named_dict(things):
    ddict = {}
    for thing in things:
        ddict[thing.name] = thing
    return ddict


def _all_depended_on_solids(execution_graph):
    check.inst_param(execution_graph, 'execution_graph', ExecutionGraph)

    dependency_structure = execution_graph.dependency_structure

    for solid in execution_graph.solids:
        for input_def in solid.input_defs:
            input_handle = solid.input_handle(input_def.name)
            if dependency_structure.has_dep(input_handle):
                output_handle = dependency_structure.get_dep(input_handle)
                yield execution_graph.solid_named(output_handle.solid.name)


def _all_sink_solids(execution_graph):
    check.inst_param(execution_graph, 'execution_graph', ExecutionGraph)
    all_names = set([solid.name for solid in execution_graph.solids])
    all_depended_on_names = set([solid.name for solid in _all_depended_on_solids(execution_graph)])
    return all_names.difference(all_depended_on_names)


def _create_subgraph(execution_graph, from_solids, through_solids):
    check.inst_param(execution_graph, 'execution_graph', ExecutionGraph)
    check.opt_list_param(from_solids, 'from_solids', of_type=str)
    check.opt_list_param(through_solids, 'through_solids', of_type=str)

    if not through_solids:
        through_solids = list(_all_sink_solids(execution_graph))

    if not from_solids:
        all_deps = set()
        for through_solid in through_solids:
            all_deps.union(execution_graph.transitive_dependencies_of(through_solid))

        from_solids = list(all_deps)

    return execution_graph.create_execution_subgraph(from_solids, through_solids)
