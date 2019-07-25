import itertools

from collections import defaultdict, OrderedDict


def _coalesce_solid_order(execution_plan):
    solid_order = [s.solid_handle.to_string() for s in execution_plan.topological_steps()]
    reversed_coalesced_solid_order = []
    for solid in reversed(solid_order):
        if solid in reversed_coalesced_solid_order:
            continue
        reversed_coalesced_solid_order.append(solid)
    return [x for x in reversed(reversed_coalesced_solid_order)]


def coalesce_execution_steps(execution_plan):
    '''Groups execution steps by solid, in topological order of the solids.'''

    solid_order = _coalesce_solid_order(execution_plan)

    steps = defaultdict(list)

    for solid_handle, solid_steps in itertools.groupby(
        execution_plan.topological_steps(), lambda x: x.solid_handle.to_string()
    ):
        steps[solid_handle] += list(solid_steps)

    return OrderedDict([(solid_handle, steps[solid_handle]) for solid_handle in solid_order])
