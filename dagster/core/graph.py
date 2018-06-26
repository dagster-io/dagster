from toposort import toposort_flatten

from dagster import check

from .definitions import SolidDefinition


class DagsterPipeline:
    def __init__(self, solids, name=None, description=None):
        self.name = check.opt_str_param(name, 'name')
        self.description = check.opt_str_param(description, 'description')
        self.solids = check.list_param(solids, 'solids', of_type=SolidDefinition)

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

    @property
    def input_names(self):
        return set([input_def.name for input_def in self.all_inputs])

    def get_input(self, solid_name, input_name):
        for solid in self.solids:
            if solid.name != solid_name:
                continue
            for input_def in solid.inputs:
                if input_def.name == input_name:
                    return input_def
        check.failed('not found')

    @property
    def external_inputs(self):
        for input_def in self.all_inputs:
            if input_def.is_external:
                yield input_def

    @property
    def externally_sourced_solids(self):
        for solid in self.solids:
            for input_def in solid.inputs:
                if input_def.is_external:
                    yield solid
                    break

    def has_input(self, name):
        check.str_param(name, 'name')
        return name in [input_def.name for input_def in self.all_inputs]

    @property
    def all_inputs(self):
        for solid in self.solids:
            for input_def in solid.inputs:
                yield input_def

    def solid_named(self, name):
        check.str_param(name, 'name')
        for solid in self.solids:
            if solid.name == name:
                return solid
        check.failed('Could not find solid named ' + name)

    @property
    def all_depended_on_solids(self):
        for input_def in self.all_inputs:
            if input_def.depends_on:
                yield input_def.depends_on

    @property
    def all_sink_solids(self):
        all_names = set([solid.name for solid in self.solids])
        all_depended_on_names = set([solid.name for solid in self.all_depended_on_solids])
        return all_names.difference(all_depended_on_names)


def create_adjacency_lists(solids):
    check.list_param(solids, 'solids', of_type=SolidDefinition)

    visit_dict = {s.name: False for s in solids}
    forward_edges = {s.name: set() for s in solids}
    backward_edges = {s.name: set() for s in solids}

    def visit(solid):
        if visit_dict[solid.name]:
            return

        visit_dict[solid.name] = True

        for inp in solid.inputs:
            if inp.depends_on is not None:
                from_node = inp.depends_on.name
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
        check.list_param(solids, 'solids', of_type=SolidDefinition)
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

    def transitive_dependencies_of(self, solid_name):
        check.str_param(solid_name, 'solid_name')

        if solid_name in self._transitive_deps:
            return self._transitive_deps[solid_name]

        trans_deps = set()
        for inp in self._solid_dict[solid_name].inputs:
            if inp.depends_on:
                trans_deps.add(inp.depends_on.name)
                trans_deps.union(self.transitive_dependencies_of(inp.depends_on.name))

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

                if inp.is_external:
                    unprovided_inputs.add(inp.name)
                else:
                    visit(inp.depends_on)

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
                if input_def.is_external:
                    continue

                if input_def.depends_on.name in from_solid_set:
                    continue

                visit(input_def.depends_on)

        for to_solid in to_solids:
            visit(self._solid_dict[to_solid])

        return SolidGraph([self._solid_dict[name] for name in involved_solids])
