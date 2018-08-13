from toposort import toposort_flatten

from dagster import check

from .definitions import (
    DependencyStructure,
    PipelineDefinition,
    SolidDefinition,
    construct_dependency_structure_from_solids_only,
)


def create_adjacency_lists(solids, dep_structure):
    check.list_param(solids, 'solids', of_type=SolidDefinition)
    check.inst_param(dep_structure, 'dep_structure', DependencyStructure)

    visit_dict = {s.name: False for s in solids}
    forward_edges = {s.name: set() for s in solids}
    backward_edges = {s.name: set() for s in solids}

    def visit(solid_name):
        if visit_dict[solid_name]:
            return

        visit_dict[solid_name] = True

        for dep_target in dep_structure.deps_of_solid(solid_name):
            forward_node = dep_target.solid_name
            backward_node = solid_name
            if forward_node in forward_edges:
                forward_edges[forward_node].add(backward_node)
                backward_edges[backward_node].add(forward_node)
                visit(forward_node)

    for s in solids:
        visit(s.name)

    return (forward_edges, backward_edges)


class SolidGraph:
    def __init__(self, solids, dependency_structure):

        solids = check.list_param(solids, 'solids', of_type=SolidDefinition)

        if dependency_structure is None:
            self.dep_structure = construct_dependency_structure_from_solids_only(solids)
        else:
            self.dep_structure = check.inst_param(
                dependency_structure, 'dependency_structure', DependencyStructure
            )

        self._solid_dict = {solid.name: solid for solid in solids}

        solid_names = set([solid.name for solid in solids])
        check.invariant(len(solid_names) == len(solids), 'must have unique names')

        all_inputs = {}

        for solid in solids:
            for input_def in solid.inputs:
                # if input exists should probably ensure that it is the same
                all_inputs[input_def.name] = input_def

        self._all_inputs = all_inputs
        self.forward_edges, self.backward_edges = create_adjacency_lists(solids, self.dep_structure)
        self.topological_order = toposort_flatten(self.backward_edges, sort=True)

        self._transitive_deps = {}

    @property
    def topological_solids(self):
        return [self._solid_dict[name] for name in self.topological_order]

    @property
    def solids(self):
        return list(self._solid_dict.values())

    def transitive_dependencies_of(self, solid_name):
        check.str_param(solid_name, 'solid_name')

        if solid_name in self._transitive_deps:
            return self._transitive_deps[solid_name]

        trans_deps = set()
        for inp in self._solid_dict[solid_name].inputs:
            if self.dep_structure.has_dep(solid_name, inp.name):
                dep_target = self.dep_structure.get_dep_target(solid_name, inp.name)
                trans_deps.add(dep_target.solid_name)
                trans_deps.union(self.transitive_dependencies_of(dep_target.solid_name))

        self._transitive_deps[solid_name] = trans_deps
        return self._transitive_deps[solid_name]

    def _check_solid_name(self, solid_name):
        check.str_param(solid_name, 'output_name')
        check.param_invariant(
            solid_name in self._solid_dict, 'output_name',
            f'Solid {solid_name} must exist in {list(self._solid_dict.keys())}'
        )

    def _check_input_names(self, input_names):
        check.list_param(input_names, 'input_names', of_type=str)

        for input_name in input_names:
            check.param_invariant(
                input_name in self._all_inputs, 'input_names', 'Input name not found'
            )

    def compute_unprovided_inputs(self, solid_name, input_names):
        '''
        Given a single solid_name and a set of input_names that represent the
        set of inputs provided for a computation, return the inputs that are *missing*.
        This detects the case where an upstream path in the DAG of solids does not
        have enough information to materialize a given output.
        '''

        self._check_solid_name(solid_name)
        self._check_input_names(input_names)

        input_set = set(input_names)

        unprovided_inputs = set()

        visit_dict = {name: False for name in self._solid_dict.keys()}

        output_solid = self._solid_dict[solid_name]

        def visit(solid):
            if visit_dict[solid.name]:
                return
            visit_dict[solid.name] = True

            for inp in solid.inputs:
                if inp.name in input_set:
                    continue

                if self.dep_structure.has_dep(solid.name, inp.name):
                    dep_target = self.dep_structure.get_dep_target(solid.name, inp.name)
                    visit(self._solid_dict[dep_target.solid_name])
                else:
                    unprovided_inputs.add(inp.name)

        visit(output_solid)

        return unprovided_inputs

    def create_execution_subgraph(self, from_solids, to_solids):
        check.list_param(from_solids, 'from_solids', of_type=str)
        check.list_param(to_solids, 'to_solids', of_type=str)

        from_solid_set = set(from_solids)
        involved_solids = from_solid_set

        def visit(solid):
            if solid.name in involved_solids:
                return
            involved_solids.add(solid.name)

            for input_def in solid.inputs:
                if not self.dep_structure.has_dep(solid.name, input_def.name):
                    continue

                from_solid = self.dep_structure.get_dep_target(
                    solid.name, input_def.name
                ).solid_name

                if from_solid in from_solid_set:
                    continue

                visit(self._solid_dict[from_solid])

        for to_solid in to_solids:
            visit(self._solid_dict[to_solid])

        return SolidGraph([self._solid_dict[name] for name in involved_solids], self.dep_structure)


def all_depended_on_solids(pipeline):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    dep_struct = pipeline.dependency_structure
    for solid in pipeline.solids:
        for input_def in solid.inputs:
            if dep_struct.has_dep(solid.name, input_def.name):
                dep_target = dep_struct.get_dep_target(solid.name, input_def.name)
                yield pipeline.solid_named(dep_target.solid_name)


def all_sink_solids(pipeline):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    all_names = set([solid.name for solid in pipeline.solids])
    all_depended_on_names = set([solid.name for solid in all_depended_on_solids(pipeline)])
    return all_names.difference(all_depended_on_names)


def create_subgraph(pipeline, from_solids, through_solids):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.opt_list_param(from_solids, 'from_solids', of_type=str)
    check.opt_list_param(through_solids, 'through_solids', of_type=str)

    solid_graph = SolidGraph(pipeline.solids, pipeline.dependency_structure)

    if not through_solids:
        through_solids = list(all_sink_solids(pipeline))

    if not from_solids:
        all_deps = set()
        for through_solid in through_solids:
            all_deps.union(solid_graph.transitive_dependencies_of(through_solid))

        from_solids = list(all_deps)

    return solid_graph.create_execution_subgraph(from_solids, through_solids)
