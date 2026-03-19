from collections.abc import Sequence
from typing import Any

import yaml
from buildkite_shared.step_builders.step_builder import StepConfiguration, is_group_step


def _step_skip(step: StepConfiguration) -> str | None:
    if is_group_step(step):
        return step.get("skip") or step["steps"][0].get("skip")
    return step.get("skip")


def _find_step(steps: Sequence[StepConfiguration], name: str) -> StepConfiguration | None:
    """Find a step by name, searching top-level steps and group sub-steps."""
    all_steps = list(steps)
    for step in steps:
        if is_group_step(step):
            all_steps.extend(step["steps"])

    # Prefer exact key match
    for step in all_steps:
        if step.get("key") == name:
            return step
    # Suffix match on group or label
    for step in all_steps:
        label = step.get("group") or step.get("label") or ""
        if label.endswith(f" {name}"):
            return step
    # Substring match — require surrounding spaces or start/end of string
    for step in all_steps:
        label = step.get("group") or step.get("label") or ""
        if f" {name} " in f" {label} ":
            return step
    return None


def get_step_skip(steps: Sequence[StepConfiguration], name: str) -> str | None:
    """Return the skip value for a step in the pipeline.

    Searches top-level steps and group sub-steps. Matches on `key` first
    (exact), then falls back to matching the `group` or `label` as a distinct
    suffix after a space, then a word-boundary substring check.
    """
    step = _find_step(steps, name)
    if step is None:
        raise KeyError(f"No step matching {name!r} found in pipeline")
    return _step_skip(step)


def assert_valid_pipeline_yaml(captured_out: str) -> dict[str, Any]:
    """Parse captured stdout as YAML and verify basic pipeline structure."""
    pipeline = yaml.safe_load(captured_out)
    assert isinstance(pipeline, dict), "output should be a YAML dict"
    assert "steps" in pipeline, "pipeline should have 'steps' key"
    assert isinstance(pipeline["steps"], list), "'steps' should be a list"
    assert "env" in pipeline, "pipeline should have 'env' key"
    assert "CI_NAME" in pipeline["env"]
    assert "CI_BRANCH" in pipeline["env"]
    return pipeline
