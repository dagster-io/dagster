from toposort import toposort_flatten

import check

from .definitions import Solid


def create_adjacency_lists(solids):
    check.list_param(solids, 'solids', of_type=Solid)

    visit_dict = {s.name: False for s in solids}
    forward_edges = {s.name: set() for s in solids}
    backward_edges = {s.name: set() for s in solids}

    def visit(solid):
        if visit_dict[solid.name]:
            return

        visit_dict[solid.name] = True

        for inp in solid.inputs:
            if inp.depends_on is not None:
                from_node = inp.name
                to_node = solid.name
                if from_node in forward_edges:
                    forward_edges[from_node].add(to_node)
                    backward_edges[to_node].add(from_node)
                    visit(inp.depends_on)

    for s in solids:
        visit(s)

    return (forward_edges, backward_edges)


class SolidGraph:
    def __init__(self, solids):
        check.list_param(solids, 'solids', of_type=Solid)
        self._solid_dict = {solid.name: solid for solid in solids}

        solid_names = set([solid.name for solid in solids])
        check.invariant(len(solid_names) == len(solids), 'must have unique names')

        all_inputs = {}

        for solid in solids:
            for input_def in solid.inputs:
                # if input exists should probably ensure that it is the same
                all_inputs[input_def.name] = input_def

        self._all_inputs = all_inputs
        self.forward_edges, self.backward_edges = create_adjacency_lists(solids)
        self.topological_order = toposort_flatten(self.backward_edges, sort=True)

        self._transitive_deps = {}

    @property
    def topological_solids(self):
        return [self._solid_dict[name] for name in self.topological_order]

    @property
    def solids(self):
        return list(self._solid_dict.values())

    def _create_visit_dict(self):
        return {name: False for name in self._solid_dict.keys()}

    # def transitive_dependencies_of(self, solid_name):
    #     check.str_param(solid_name, 'solid_name')

    #     if solid_name in self._transitive_deps:
    #         return self._transitive_deps[solid_name]

    #     trans_deps = set()
    #     for inp in self._solid_dict[solid_name].inputs:
    #         if inp.depends_on:
    #             trans_deps.add(inp.depends_on.name)
    #             trans_deps.union(self.transitive_dependencies_of(inp.depends_on))

    #     self._transitive_deps[solid_name] = trans_deps
    #     return self._transitive_deps[solid_name]

    def _check_output_name(self, output_name):
        check.str_param(output_name, 'output_name')
        check.param_invariant(
            output_name in self._solid_dict, 'output_name',
            f'Output solid must exist in {list(self._solid_dict.keys())}'
        )

    def _check_input_names(self, input_names):
        check.list_param(input_names, 'input_names', of_type=str)

        for input_name in input_names:
            check.param_invariant(
                input_name in self._all_inputs, 'input_names', 'Input name not found'
            )

    def compute_unprovided_inputs(self, output_name, input_names):
        '''
        Given a single output_name and a set of input_names that represent the
        set of inputs provided for a computation, return the inputs that are *missing*.
        This detects the case where an upstream path in the DAG of solids does not
        have enough information to materialize a given output.
        '''

        self._check_output_name(output_name)
        self._check_input_names(input_names)

        input_set = set(input_names)

        unprovided_inputs = set()

        visit_dict = self._create_visit_dict()

        output_solid = self._solid_dict[output_name]

        def visit(solid):
            if visit_dict[solid.name]:
                return
            visit_dict[solid.name] = True

            for inp in solid.inputs:
                if inp.name in input_set:
                    continue

                if inp.is_external:
                    unprovided_inputs.add(inp.name)
                else:
                    visit(inp.depends_on)

        visit(output_solid)

        return unprovided_inputs

    def create_execution_graph(self, output_names, input_names):
        '''Given a set of outputs that should be completed, and a
        list input names that were provided into order to complete the execution,
        return a copy of the SolidGraph object that represents the minimal set of
        solids necessary to execute to satisfy the computation'''

        check.list_param(output_names, 'output_names', of_type=str)

        for output_name in output_names:
            self._check_output_name(output_name)
            # this might be excessive as we are doing a ton of graph traversals
            # biasing towards strictness for now
            unprovided_inputs = self.compute_unprovided_inputs(output_name, input_names)
            check.invariant(not unprovided_inputs, 'Must provide all inputs')

        self._check_input_names(input_names)

        input_set = set(input_names)

        involved_solids = set()

        def visit(solid):
            if solid.name in involved_solids:
                return
            involved_solids.add(solid.name)

            for inp in solid.inputs:
                if inp.name in input_set:
                    continue

                if not inp.is_external:
                    visit(inp.depends_on)

        for output_name in output_names:
            visit(self._solid_dict[output_name])

        return SolidGraph([self._solid_dict[name] for name in involved_solids])


class SolidPipeline:
    def __init__(self, solids):
        self.solids = check.list_param(solids, 'solids', of_type=Solid)
        solid_names = set([solid.name for solid in self.solids])
        for solid in solids:
            for input_def in solid.inputs:
                if input_def.depends_on:
                    check.invariant(
                        input_def.depends_on.name in solid_names,
                        f'dep must exist got: {input_def.depends_on.name} and set {solid_names}'
                    )

        self.solid_graph = SolidGraph(solids=solids)

    @property
    def solid_names(self):
        return [solid.name for solid in self.solids]

    def solid_named(self, name):
        check.str_param(name, 'name')
        for solid in self.solids:
            if solid.name == name:
                return solid
        check.failed('Could not find solid named ' + name)
