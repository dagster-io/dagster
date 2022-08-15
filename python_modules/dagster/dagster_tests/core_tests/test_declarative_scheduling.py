from typing import AbstractSet, FrozenSet, List, NamedTuple, Optional, Union

from dagster import AssetKey, asset, repository


@asset
def a():
    return 1


@asset
def o():
    return 1


@asset
def b(a):
    return a + 1


@asset
def c(a):
    return a + 2


@asset
def d(o, b):
    return o + b


@asset
def e(b, c):
    return b + c


@asset
def f(c):
    return c + 1


@asset
def g(b, c):
    return b + c


class SLA(NamedTuple):
    data_from: float
    data_by: float


class AssetAndSLA(NamedTuple):
    key: str
    sla: SLA
    """still need to nail down exactly what this means.  something like: a re-materialization should
    have completed by this tick since the last tick (which incorporates some root data that arrived
    since the last tick??)
    """

    deps: AbstractSet[str]
    processing_minutes: int  # how many minutes to allocate to materialize the asset


class ScheduledRun:
    keys: AbstractSet[str]
    minutes_from_start: int


class RuntimeSolution(NamedTuple):
    # this represents a run that starts at a certain time
    run_time: int

    @property
    def data_from(self):
        return self.run_time


class DependentRunsSolution(NamedTuple):
    # this represetns a run that will start after a specified set of other runs
    dependent_solutions: FrozenSet[Union[RuntimeSolution, "DependentRunsSolution"]]

    @property
    def data_from(self):
        # the data in this run will be up to date relative to its least up-to-date upstream
        # solution
        return max(soln.data_from for soln in self.dependent_solutions)


EVERY_HOUR = 1
EVERY_TWO_HOURS = 2
EVERY_THREE_HOURS = 3
EVERY_DAY_8AM = 4
EVERY_DAY_9AM = 5

# placeholder
def sla_to_constraints(assets_def):
    processing_time = assets_def._processing_time or 0
    if assets_def._sla is None:
        return set()
    # just hardcoding for now
    elif assets_def._sla == EVERY_HOUR:
        # computation must start after the hour, and end before the hour
        return {(i * 60, (i + 1) * 60 - processing_time) for i in range(24)}
    elif assets_def._sla == EVERY_TWO_HOURS:
        return {(i * 60, (i + 2) * 60 - processing_time) for i in range(0, 24, 2)}
    elif assets_def._sla == EVERY_THREE_HOURS:
        return {(i * 60, (i + 3) * 60 - processing_time) for i in range(0, 24, 3)}
    elif assets_def._sla == EVERY_DAY_8AM:
        # computation must start after midnight, and end before 8AM
        return {(0, 8 * 60 - processing_time)}
    elif assets_def._sla == EVERY_DAY_9AM:
        # computation must start after midnight, and end before 8AM
        return {(0, 9 * 60 - processing_time)}


def plan_runs_for_day(asset_layer):
    from collections import defaultdict

    import toposort

    from dagster._core.selector.subset_selector import generate_asset_dep_graph

    graph = generate_asset_dep_graph(
        assets_defs=asset_layer.assets_defs_by_key.values(),
        source_assets=asset_layer.source_assets_by_key.values(),
    )
    # convert strings to actual keys for convenience
    key_graph = {
        "upstream": {
            AssetKey.from_user_string(k): {AssetKey.from_user_string(vi) for vi in v}
            for k, v in graph["upstream"].items()
        },
        "downstream": {
            AssetKey.from_user_string(k): {AssetKey.from_user_string(vi) for vi in v}
            for k, v in graph["downstream"].items()
        },
    }

    # map of asset key to the constraints that need to be satisfied
    constraints_by_key = defaultdict(set)

    # go level by level, starting from the bottom, propogating constraints upwards
    levels = list(toposort.toposort(key_graph["upstream"]))
    for level in reversed(levels):
        for key in level:
            assets_def = asset_layer.assets_def_for_asset(key)
            # figure out what "computation start time window" constraints correspond to this SLA
            constraints = sla_to_constraints(assets_def)
            # add these constraints to this node
            constraints_by_key[key] |= constraints

            # propogate these constraints upwards, taking into account the processing time of the
            # upstream node
            for upstream_key in key_graph["upstream"][key]:
                upstream_proc_time = (
                    asset_layer.assets_def_for_asset(upstream_key)._processing_time or 0
                )
                # the latest we can start the upstream computation is equal to the latest
                # we can start this computation minus how long the upstream computation will take
                constraints_by_key[upstream_key] |= {
                    (c[0], c[1] - upstream_proc_time) for c in constraints_by_key[key]
                }

    # at the end of this process, we only need to optimize the root constraints
    root_keys = levels[0]

    # a dictionary mapping asset key to a set of solutions that will include this asset
    solutions_by_key = defaultdict(set)

    # this is the heart of the optimization process -- we only try to deduplicate constraints at
    # the root level. right now, we isolate this optimization by root key, and I haven't thought
    # about if it makes a difference if we try to optimize over all roots at once.
    #
    # this also is a greedy algorithm (it just tries to merge any constraints it can), so it's
    # possible we can swap this out with something a little smarter if necessary
    for root_key in root_keys:
        merged_constraint = None
        for constraint in sorted(constraints_by_key[root_key]):
            if not merged_constraint:
                # convert to list to allow item assignment
                merged_constraint = list(constraint)
                continue
            # if this constraint starts after the current window ends, then it cannot be merged, so
            # we'll need to create a run to solve the merged constraint.
            #
            # add a run that starts at the beginning of this time window (any time between the start
            # and end of the time window will work, so we somewhat arbitrarily choose the earliest
            # possible)
            if constraint[0] > merged_constraint[1]:
                solutions_by_key[root_key].add(RuntimeSolution(merged_constraint[0]))
                # start trying to merge into the new constraint
                merged_constraint = list(constraint)
            # if this window starts before the current window ends, then we can satisfy this
            # constraint at the same time as all other merged constraints
            else:
                merged_constraint[0] = constraint[0]
                # update end time to make sure all constraints remain satisfied
                merged_constraint[1] = min(merged_constraint[1], constraint[1])

        # add in a run for the leftover merged constraint
        if merged_constraint:
            solutions_by_key[root_key].add(RuntimeSolution(merged_constraint[0]))

    for key, constraints in constraints_by_key.items():
        print(key, sorted(constraints))

    # now that we have a set of runs that will start at each root node, we can propogate these
    # downwards to satisfy all downstream constraints
    #
    # quadruple-nested for loops look bad but in practice I think this could be optimized down to
    # near-linear time. just wrote it this way for simplicity
    #
    # we already got solutions for all the root nodes (level 0), so we skip this one
    for level in levels[1:]:
        for key in level:
            upstream_keys = key_graph["upstream"][key]
            solutions = set()
            constraint_index = 0
            constraints = sorted(constraints_by_key[key])
            while constraint_index < len(constraints):
                constraint = constraints[constraint_index]
                constraint_solutions = set()
                # need to come up with a solution that satisfies all upstream
                for upstream_key in upstream_keys:
                    for solution in solutions_by_key[upstream_key]:
                        if (
                            solution.data_from >= constraint[0]
                            and solution.data_from <= constraint[1]
                        ):
                            # this constraint gets solved with this solution
                            constraint_solutions.add(solution)
                            break
                if len(constraint_solutions) == 1:
                    solutions.add(next(iter(constraint_solutions)))
                elif len(constraint_solutions) > 1:
                    solutions.add(DependentRunsSolution(frozenset(constraint_solutions)))
                else:
                    raise Exception("Should always find a solution for constraint")
                constraint_index += 1
            solutions_by_key[key] = solutions

    keys_by_solutions = defaultdict(set)
    for key, solutions in solutions_by_key.items():
        for solution in solutions:
            keys_by_solutions[solution].add(key)
    return keys_by_solutions


def test_simple():
    import pprint

    pp = pprint.PrettyPrinter(indent=4)
    assets = [
        a.with_processing_time(10),
        b.with_processing_time(20).with_sla(EVERY_HOUR),
        c.with_processing_time(30).with_sla(EVERY_TWO_HOURS),
    ]
    from dagster._legacy import build_assets_job

    assets_job = build_assets_job("test", assets)

    planned_runs = plan_runs_for_day(assets_job._asset_layer)
    pp.pprint(planned_runs)
    assert False


def test_complex():
    import pprint

    pp = pprint.PrettyPrinter(indent=4)
    assets = [
        a.with_processing_time(20),
        b.with_processing_time(5),
        c.with_processing_time(30),
        d.with_processing_time(15).with_sla(EVERY_TWO_HOURS),
        e.with_processing_time(10).with_sla(EVERY_THREE_HOURS),
        f.with_processing_time(25).with_sla(EVERY_DAY_8AM),
        o.with_processing_time(30),
        g.with_processing_time(15).with_sla(EVERY_THREE_HOURS),
    ]
    from dagster._legacy import build_assets_job

    assets_job = build_assets_job("test", assets)

    planned_runs = plan_runs_for_day(assets_job._asset_layer)
    pp.pprint(planned_runs)
    assert False


def test_other():
    import pprint

    pp = pprint.PrettyPrinter(indent=4)
    assets = [
        a.with_processing_time(20),
        b.with_processing_time(5),
        c.with_processing_time(30),
        d.with_processing_time(15).with_sla(EVERY_DAY_9AM),
        e.with_processing_time(10).with_sla(EVERY_DAY_9AM),
        f.with_processing_time(25).with_sla(EVERY_DAY_8AM),
        o.with_processing_time(30),
        g.with_processing_time(15).with_sla(EVERY_DAY_8AM),
    ]
    from dagster._legacy import build_assets_job

    assets_job = build_assets_job("test", assets)

    planned_runs = plan_runs_for_day(assets_job._asset_layer)
    pp.pprint(planned_runs)
    assert False
