from collections.abc import Sequence
from typing import Any

import yaml
from buildkite_shared.step_builders.step_builder import StepConfiguration, is_group_step


def _step_skip(step: StepConfiguration) -> str | None:
    if is_group_step(step):
        return step.get("skip") or step["steps"][0].get("skip")
    return step.get("skip")


def get_step_skip(steps: Sequence[StepConfiguration], name: str) -> str | None:
    """Return the skip value for a step in the pipeline.

    Matches on `key` first (exact), then falls back to matching the `group` or
    `label` as a distinct suffix after a space to avoid substring collisions
    (e.g. "dagster" matching "dagster-cloud"). Finally, falls back to a
    word-boundary `in` check for cases where the name appears in the middle of
    the label.
    """
    # Prefer exact key match
    for step in steps:
        if step.get("key") == name:
            return _step_skip(step)
    # Suffix match on group or label
    for step in steps:
        label = step.get("group") or step.get("label") or ""
        if label.endswith(f" {name}"):
            return _step_skip(step)
    # Substring match — require surrounding spaces or start/end of string
    for step in steps:
        label = step.get("group") or step.get("label") or ""
        if f" {name} " in f" {label} ":
            return _step_skip(step)
    raise KeyError(f"No step matching {name!r} found in pipeline")


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
