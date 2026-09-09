import copy
import logging
import sys
from collections.abc import Callable, Sequence
from typing import Any, cast

logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(message)s")

from buildkite_shared.step_builders.step_builder import (
    GroupStepConfiguration,
    StepConfiguration,
    is_command_step,
    is_group_step,
)

# ########################
# ##### FILTER STEPS
# ########################


def filter_steps(
    steps: Sequence[StepConfiguration], predicate: Callable[[StepConfiguration], bool]
) -> list[StepConfiguration]:

    # First resolve the full set of step keys that need to be included. This
    # includes any step that satisfies the predicate, as well as any steps that
    # they depend on, recursively.
    graph = _build_dependency_graph(steps)
    first_order_keys = _get_selected_step_keys(steps, predicate)

    all_keys = set(first_order_keys)
    while True:
        new_keys = set(k for k in all_keys for k in graph.get(k, [])) - all_keys
        if not new_keys:
            break
        all_keys.update(new_keys)

    # We now have the full set of keys that need to be included to satisfy the
    # predicate and all dependencies. We can filter the steps to only include
    # those with keys in all_keys.

    return [
        step
        for step in (_filter_step(s, lambda s: s.get("key") in all_keys) for s in steps)
        if step
    ]


def _build_dependency_graph(steps: Sequence[StepConfiguration]) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}

    def _visit(step: StepConfiguration):
        if is_command_step(step) and step.get("key"):
            graph[step["key"]] = set(step.get("depends_on", []))
        elif is_group_step(step):
            for substep in step.get("steps", []):
                _visit(substep)

    return graph


def _get_selected_step_keys(
    steps: Sequence[StepConfiguration], predicate: Callable[[StepConfiguration], bool]
) -> set[str]:
    selected_keys = set()

    def _visit(step: StepConfiguration):
        if predicate(step):
            if not step.get("key"):
                raise ValueError(
                    f"Step {step.get('label', '')} must have a key to be selected by the filter"
                )
            selected_keys.add(step["key"])
        elif is_group_step(step):
            for substep in step.get("steps", []):
                _visit(substep)

    for step in steps:
        _visit(step)

    return selected_keys


def _filter_step(
    step: StepConfiguration, predicate: Callable[[StepConfiguration], bool]
) -> StepConfiguration | None:

    # Group steps pass filter if any substep passes.
    if is_group_step(step):
        filtered_substeps = [
            substep
            for substep in (_filter_step(s, predicate) for s in step["steps"])
            if substep  # filter_step returns None if it doesn't satisfy the predicate
        ]
        if filtered_substeps:
            return cast("GroupStepConfiguration", {**step, "steps": filtered_substeps})

    # Other steps pass filter if they satisfy the predicate
    elif predicate(step):
        return {**step, "skip": None}  # Clear skip reason if step is included


# ########################
# ##### REPEAT STEPS
# ########################


def repeat_steps(steps: Sequence[StepConfiguration], n: int) -> Sequence[StepConfiguration]:
    """Emit ``n`` copies of each step, for surfacing flaky tests.

    Copies get a distinct key (``<key>-repeat-<i>``); duplicate keys are rejected
    at upload.

    Steps that something depends on are emitted once instead of copied — a
    repeated suite should reuse the single image build it waits on, not rebuild it
    ``n`` times. That also leaves every ``depends_on`` value pointing at a key
    that still exists.
    """
    return _repeat_steps(steps, n, _get_dependency_target_keys(steps))


def _repeat_steps(
    steps: Sequence[StepConfiguration], n: int, dependency_targets: set[str]
) -> list[StepConfiguration]:
    repeated_steps: list[StepConfiguration] = []
    for step in steps:
        if is_group_step(step):
            repeated_steps.append(
                cast(
                    "GroupStepConfiguration",
                    {**step, "steps": _repeat_steps(step["steps"], n, dependency_targets)},
                )
            )
            continue

        key = step.get("key")
        if key in dependency_targets:
            repeated_steps.append(step)
            continue

        for i in range(n):
            step_copy = copy.deepcopy(step)
            step_copy["label"] = f"{step.get('label', '')} [{i + 1}]"
            if key:
                step_copy["key"] = f"{key}-repeat-{i + 1}"
            repeated_steps.append(step_copy)
    return repeated_steps


def _get_dependency_target_keys(steps: Sequence[StepConfiguration]) -> set[str]:
    targets: set[str] = set()

    def _visit(step: StepConfiguration) -> None:
        if is_group_step(step):
            for substep in step["steps"]:
                _visit(substep)
            return
        # `depends_on` is absent from GroupStepConfiguration in the type, so the
        # union rejects the lookup even though the group case returned above.
        deps = cast("dict[str, Any]", step).get("depends_on")
        if isinstance(deps, str):
            targets.add(deps)
        elif isinstance(deps, list):
            targets.update(d for d in deps if isinstance(d, str))

    for step in steps:
        _visit(step)
    return targets


# ########################
# ##### SIMPLIFY
# ########################


# Buildkite counts every group container as a job toward the organization's per-upload job
# limit (currently 1000). Unwrap groups that contain only a single step so we don't waste job
# slots on trivial wrappers.
def simplify_steps(steps: Sequence[StepConfiguration]) -> Sequence[StepConfiguration]:
    """Unwrap single-step groups."""
    result = []
    for step in steps:
        substeps = step.get("steps", [])
        if "group" in step and len(substeps) == 1:
            result.append(substeps[0])
        else:
            result.append(step)
    return result
