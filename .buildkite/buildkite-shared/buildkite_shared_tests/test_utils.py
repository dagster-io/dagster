"""Tests for buildkite_shared.utils."""

import logging

import pytest
from buildkite_shared.utils import dump_pipeline_yaml
from dagster_shared.yaml_utils import safe_load_yaml


def test_dump_pipeline_yaml_drops_skipped_steps(caplog: pytest.LogCaptureFixture) -> None:
    pipeline = {
        "steps": [
            {"key": "a", "label": "a", "commands": ["echo a"]},
            {
                "key": "b",
                "label": "b",
                "commands": ["echo b"],
                "skip": "no relevant changes",
            },
            {"key": "c", "label": "c", "commands": ["echo c"], "depends_on": ["a", "b"]},
        ]
    }
    with caplog.at_level(logging.INFO):
        out = safe_load_yaml(dump_pipeline_yaml(pipeline))

    keys = [s["key"] for s in out["steps"]]
    assert keys == ["a", "c"]
    # depends_on entries pointing at dropped keys are scrubbed
    c = next(s for s in out["steps"] if s["key"] == "c")
    assert c["depends_on"] == ["a"]
    # The skipped step is logged with its reason
    assert any("Dropping skipped step b" in r.message for r in caplog.records)
    assert any("no relevant changes" in r.message for r in caplog.records)


def test_dump_pipeline_yaml_drops_skipped_substeps_and_empty_groups(
    caplog: pytest.LogCaptureFixture,
) -> None:
    pipeline = {
        "steps": [
            {
                "key": "g1",
                "group": "g1",
                "label": "g1",
                "steps": [
                    {"key": "g1-a", "label": "g1-a", "commands": ["echo"]},
                    {
                        "key": "g1-b",
                        "label": "g1-b",
                        "commands": ["echo"],
                        "skip": "skipped substep",
                    },
                ],
            },
            {
                "key": "g2",
                "group": "g2",
                "label": "g2",
                "steps": [
                    {
                        "key": "g2-a",
                        "label": "g2-a",
                        "commands": ["echo"],
                        "skip": "no changes",
                    },
                ],
            },
            {
                "key": "downstream",
                "label": "downstream",
                "commands": ["echo"],
                "depends_on": ["g2-a", "g1-a"],
            },
        ]
    }
    with caplog.at_level(logging.INFO):
        out = safe_load_yaml(dump_pipeline_yaml(pipeline))

    # g2 had only a skipped substep -> drop the whole group.
    top_keys = [s["key"] for s in out["steps"]]
    assert top_keys == ["g1", "downstream"]

    # g1 lost g1-b but keeps g1-a
    g1 = next(s for s in out["steps"] if s["key"] == "g1")
    assert [s["key"] for s in g1["steps"]] == ["g1-a"]

    # downstream's depends_on no longer references dropped keys
    downstream = next(s for s in out["steps"] if s["key"] == "downstream")
    assert downstream["depends_on"] == ["g1-a"]

    # All drops were logged
    messages = [r.message for r in caplog.records]
    assert any("Dropping skipped step g1-b" in m for m in messages)
    assert any("Dropping skipped step g2-a" in m for m in messages)
    assert any("Dropping empty group g2" in m for m in messages)


def test_dump_pipeline_yaml_passes_through_when_nothing_skipped() -> None:
    pipeline = {
        "steps": [
            {"key": "a", "label": "a", "commands": ["echo a"]},
            {"key": "b", "label": "b", "commands": ["echo b"], "depends_on": ["a"]},
        ]
    }
    out = safe_load_yaml(dump_pipeline_yaml(pipeline))
    assert [s["key"] for s in out["steps"]] == ["a", "b"]
    assert out["steps"][1]["depends_on"] == ["a"]
