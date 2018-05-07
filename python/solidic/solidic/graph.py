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
                forward_edges[from_node].add(to_node)
                backward_edges[to_node].add(from_node)
                visit(inp.depends_on)

    for s in solids:
        visit(s)

    return (forward_edges, backward_edges)


class SolidGraph:
    def __init__(self, solids):
        self.solids = check.list_param(solids, 'solids', of_type=Solid)

        solid_names = set([solid.name for solid in solids])

        check.invariant(len(solid_names) == len(solids), 'must have unique names')

        for solid in solids:
            for input_def in solid.inputs:
                if input_def.depends_on:
                    check.invariant(input_def.depends_on.name in solid_names, 'dep must exist')

        self.forward_edges, self.backward_edges = create_adjacency_lists(solids)
        self.topological_order = toposort_flatten(self.backward_edges, sort=True)
