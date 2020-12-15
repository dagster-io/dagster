import re
import sys
from collections import defaultdict

from dagster.core.definitions.dependency import DependencyStructure
from dagster.core.errors import DagsterInvalidSubsetError
from dagster.utils import check

MAX_NUM = sys.maxsize


def generate_dep_graph(pipeline_def):
    """'pipeline to dependency graph. It currently only supports top-level solids.

    Args:
        pipeline (PipelineDefinition): The pipeline to execute.

    Returns:
        graph (Dict[str, Dict[str, Set[str]]]): the input and output dependency graph. e.g.
            ```
            {
                "upstream": {
                    "solid_one_1": set(),
                    "solid_one_2": set(),
                    "solid_two": {"solid_one_1", "solid_one_2"},
                    "solid_three": {"solid_two"},
                },
                "downstream": {
                    "solid_one_1": {"solid_two"},
                    "solid_one_2": {"solid_two"},
                    "solid_two": {"solid_three"},
                    "solid_three": set(),
                },
            }
            ```
    """
    dependency_structure = check.inst_param(
        pipeline_def.dependency_structure, "dependency_structure", DependencyStructure
    )
    item_names = [i.name for i in pipeline_def.solids]

    # defaultdict isn't appropriate because we also want to include items without dependencies
    graph = {"upstream": {}, "downstream": {}}
    for item_name in item_names:
        graph["upstream"][item_name] = set()
        upstream_dep = dependency_structure.input_to_upstream_outputs_for_solid(item_name)
        for upstreams in upstream_dep.values():
            for up in upstreams:
                graph["upstream"][item_name].add(up.solid_name)

        graph["downstream"][item_name] = set()
        downstream_dep = dependency_structure.output_to_downstream_inputs_for_solid(item_name)
        for downstreams in downstream_dep.values():
            for down in downstreams:
                graph["downstream"][item_name].add(down.solid_name)

    return graph


class Traverser:
    def __init__(self, graph):
        self.graph = graph

    def _fetch_items(self, item_name, depth, direction):
        dep_graph = self.graph[direction]
        stack = [item_name]
        result = set()
        curr_depth = 0
        while stack:
            # stop when reach the given depth
            if curr_depth >= depth:
                break
            curr_level_len = len(stack)
            while stack and curr_level_len > 0:
                curr_item = stack.pop()
                for item in dep_graph.get(curr_item, set()):
                    curr_level_len -= 1
                    if item not in result:
                        stack.append(item)
                        result.add(item)
            curr_depth += 1
        return result

    def fetch_upstream(self, item_name, depth):
        # return a set of ancestors of the given item, up to the given depth
        return self._fetch_items(item_name, depth, "upstream")

    def fetch_downstream(self, item_name, depth):
        # return a set of descendants of the given item, down to the given depth
        return self._fetch_items(item_name, depth, "downstream")


def parse_clause(clause):
    def _get_depth(part):
        if part == "":
            return 0
        if "*" in part:
            return MAX_NUM
        if set(part) == set("+"):
            return len(part)
        return None

    token_matching = re.compile(r"^(\*?\+*)?([.\w\d\[\]?_-]+)(\+*\*?)?$").search(clause.strip())
    # return None if query is invalid
    parts = token_matching.groups() if token_matching is not None else []
    if len(parts) != 3:
        return None

    ancestor_part, item_name, descendant_part = parts
    up_depth = _get_depth(ancestor_part)
    down_depth = _get_depth(descendant_part)

    return (up_depth, item_name, down_depth)


def parse_items_from_selection(selection):
    items = []
    for clause in selection:
        parts = parse_clause(clause)
        if parts is None:
            continue
        _u, item, _d = parts
        items.append(item)
    return items


def clause_to_subset(graph, clause):
    """Take a selection query and return a list of the selected and qualified items.

    Args:
        graph (Dict[str, Dict[str, Set[str]]]): the input and output dependency graph.
        clause (str): the subselection query in model selection syntax, e.g. "*some_solid+" will
            select all of some_solid's upstream dependencies and its direct downstream dependecies.

    Returns:
        subset_list (List[str]): a list of selected and qualified solid names, empty if input is
            invalid.
    """
    # parse cluase
    if not isinstance(clause, str):
        return []
    parts = parse_clause(clause)
    if parts is None:
        return []
    up_depth, item_name, down_depth = parts
    # item_name invalid
    if item_name not in graph["upstream"]:
        return []

    subset_list = []
    traverser = Traverser(graph=graph)
    subset_list.append(item_name)
    # traverse graph to get up/downsteam items
    subset_list += traverser.fetch_upstream(item_name, up_depth)
    subset_list += traverser.fetch_downstream(item_name, down_depth)

    return subset_list


def parse_solid_selection(pipeline_def, solid_selection):
    """Take pipeline definition and a list of solid selection queries (inlcuding names of solid
        invocations. See syntax examples below) and return a set of the qualified solid names.

    It currently only supports top-level solids.

    Query syntax examples:
    - "some_solid": select "some_solid" itself
    - "*some_solid": select "some_solid" and all ancestors (upstream dependencies)
    - "some_solid*": select "some_solid" and all descendants (downstream dependencies)
    - "*some_solid*": select "some_solid" and all of its ancestors and descendants
    - "+some_solid": select "some_solid" and its ancestors at 1 level up
    - "some_solid+++": select "some_solid" and its descendants within 3 levels down

    Note:
    - If one of the query clauses is invalid, we will skip that one and continue to parse the valid
        ones.

    Args:
        pipeline_def (PipelineDefinition): the pipeline to execute.
        solid_selection (List[str]): a list of the solid selection queries (including single solid
            names) to execute.

    Returns:
        FrozenSet[str]: a frozenset of qualified deduplicated solid names, empty if no qualified
            subset selected.
    """
    check.list_param(solid_selection, "solid_selection", of_type=str)

    graph = generate_dep_graph(pipeline_def)
    solids_set = set()

    # loop over clauses
    for clause in solid_selection:
        subset = clause_to_subset(graph, clause)
        if len(subset) == 0:
            raise DagsterInvalidSubsetError(
                "No qualified solids to execute found for solid_selection={requested}".format(
                    requested=solid_selection
                )
            )
        solids_set.update(subset)

    return frozenset(solids_set)


def parse_step_selection(step_deps, step_selection):
    """Take the dependency dictionary generated while building execution plan and a list of step key
     selection queries and return a set of the qualified step keys.

    It currently only supports top-level solids.

    Args:
        step_deps (Dict[str, Set[str]]): a dictionary of execution step dependency where the key is
            a step key and the value is a set of direct upstream dependency of the step.
        step_selection (List[str]): a list of the step key selection queries (including single
            step key) to execute.

    Returns:
        FrozenSet[str]: a frozenset of qualified deduplicated solid names, empty if no qualified
            subset selected.
    """
    check.list_param(step_selection, "step_selection", of_type=str)

    # reverse step_deps to get the downstream_deps
    # make sure we have all items as keys, including the ones without downstream dependencies
    downstream_deps = defaultdict(set, {k: set() for k in step_deps.keys()})
    for downstream_key, upstream_keys in step_deps.items():
        for step_key in upstream_keys:
            downstream_deps[step_key].add(downstream_key)

    # generate dep graph
    graph = {"upstream": step_deps, "downstream": downstream_deps}
    steps_set = set()

    # loop over clauses
    for clause in step_selection:
        subset = clause_to_subset(graph, clause)
        if len(subset) == 0:
            raise DagsterInvalidSubsetError(
                "No qualified steps to execute found for step_selection={requested}".format(
                    requested=step_selection
                )
            )
        steps_set.update(subset)

    return frozenset(steps_set)
