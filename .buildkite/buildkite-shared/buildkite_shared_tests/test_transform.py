"""Tests for buildkite_shared.transform."""

from typing import Any

from buildkite_shared.transform import repeat_steps, simplify_steps
from buildkite_shared.utils import dump_pipeline_yaml
from dagster_shared.yaml_utils import safe_load_yaml


def test_repeat_steps_rekeys_copies_and_survives_upload_checks() -> None:
    steps = [_leaf("alpha"), _leaf("beta")]

    repeated = repeat_steps(steps, 3)

    assert [s["key"] for s in repeated] == [
        "alpha-repeat-1",
        "alpha-repeat-2",
        "alpha-repeat-3",
        "beta-repeat-1",
        "beta-repeat-2",
        "beta-repeat-3",
    ]
    assert [s["label"] for s in repeated] == [
        "alpha [1]",
        "alpha [2]",
        "alpha [3]",
        "beta [1]",
        "beta [2]",
        "beta [3]",
    ]
    # The original steps are left untouched.
    assert [s["key"] for s in steps] == ["alpha", "beta"]

    # dump_pipeline_yaml rejects missing/duplicate keys, as does Buildkite at upload.
    out = safe_load_yaml(dump_pipeline_yaml({"steps": list(simplify_steps(repeated))}))
    assert len(out["steps"]) == 6


def test_repeat_steps_emits_dependency_targets_once() -> None:
    steps = [
        _leaf("build-image"),
        _leaf("suite", depends_on=["build-image"]),
        _leaf("other-suite", depends_on="build-image"),
    ]

    repeated = repeat_steps(steps, 2)

    # `build-image` is depended on, so it is emitted once with its key intact and
    # every copy's `depends_on` still resolves.
    assert [s["key"] for s in repeated] == [
        "build-image",
        "suite-repeat-1",
        "suite-repeat-2",
        "other-suite-repeat-1",
        "other-suite-repeat-2",
    ]
    assert repeated[0]["label"] == "build-image"
    keys = {s["key"] for s in repeated}
    for step in repeated:
        for dep in _deps(step):
            assert dep in keys

    out = safe_load_yaml(dump_pipeline_yaml({"steps": list(simplify_steps(repeated))}))
    assert len(out["steps"]) == 5


def test_repeat_steps_recurses_into_groups_without_repeating_the_group() -> None:
    steps = [
        {
            "key": "grp",
            "group": "grp",
            "label": "grp",
            "steps": [_leaf("build-image"), _leaf("suite", depends_on=["build-image"])],
        },
        _leaf("standalone"),
    ]

    repeated = repeat_steps(steps, 2)

    assert [s["key"] for s in repeated] == ["grp", "standalone-repeat-1", "standalone-repeat-2"]
    # The group itself is emitted once; its leaves are what get repeated, and the
    # dependency target inside it is still recognized as one.
    assert [s["key"] for s in repeated[0]["steps"]] == [
        "build-image",
        "suite-repeat-1",
        "suite-repeat-2",
    ]

    out = safe_load_yaml(dump_pipeline_yaml({"steps": list(simplify_steps(repeated))}))
    assert len(out["steps"]) == 3


def test_repeat_steps_deep_copies_nested_values() -> None:
    steps = [_leaf("alpha", plugins=[{"docker": {"environment": ["FOO=1"]}}])]

    repeated = repeat_steps(steps, 2)

    first, second = repeated
    assert first["commands"] is not second["commands"]
    assert first["plugins"] is not second["plugins"]

    first["commands"].append("MUTATED")
    first["plugins"][0]["docker"]["environment"].append("BAR=2")
    assert second["commands"] == ["echo alpha"]
    assert second["plugins"] == [{"docker": {"environment": ["FOO=1"]}}]


# ########################
# ##### HELPERS
# ########################


def _leaf(key: str, **extra: Any) -> dict[str, Any]:
    return {"key": key, "label": key, "commands": [f"echo {key}"], **extra}


def _deps(step: dict[str, Any]) -> list[str]:
    deps = step.get("depends_on")
    if deps is None:
        return []
    return [deps] if isinstance(deps, str) else list(deps)
