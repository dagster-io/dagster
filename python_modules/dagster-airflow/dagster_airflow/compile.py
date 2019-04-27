import itertools

from collections import defaultdict, OrderedDict


def _coalesce_solid_order(execution_plan):
    solid_order = [s.solid_name for s in execution_plan.topological_steps()]
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

    for solid_name, solid_steps in itertools.groupby(
        execution_plan.topological_steps(), lambda x: x.solid_name
    ):
        steps[solid_name] += list(solid_steps)

    return OrderedDict([(solid_name, steps[solid_name]) for solid_name in solid_order])
