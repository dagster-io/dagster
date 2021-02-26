import re

import pytest
from dagster import (
    Bool,
    DagsterInstance,
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
    ModeDefinition,
    PipelineDefinition,
    PresetDefinition,
    check,
    execute_pipeline,
    lambda_solid,
    pipeline,
    solid,
)
from dagster.utils import file_relative_path


def test_presets():
    @solid(config_schema={"error": Bool})
    def can_fail(context):
        if context.solid_config["error"]:
            raise Exception("I did an error")
        return "cool"

    @lambda_solid
    def always_fail():
        raise Exception("I always do this")

    pipe = PipelineDefinition(
        name="simple",
        solid_defs=[can_fail, always_fail],
        preset_defs=[
            PresetDefinition.from_files(
                "passing",
                config_files=[file_relative_path(__file__, "pass_env.yaml")],
                solid_selection=["can_fail"],
            ),
            PresetDefinition.from_files(
                "passing_overide_to_fail",
                config_files=[file_relative_path(__file__, "pass_env.yaml")],
                solid_selection=["can_fail"],
            ).with_additional_config({"solids": {"can_fail": {"config": {"error": True}}}}),
            PresetDefinition(
                "passing_direct_dict",
                run_config={"solids": {"can_fail": {"config": {"error": False}}}},
                solid_selection=["can_fail"],
            ),
            PresetDefinition.from_files(
                "failing_1",
                config_files=[file_relative_path(__file__, "fail_env.yaml")],
                solid_selection=["can_fail"],
            ),
            PresetDefinition.from_files(
                "failing_2", config_files=[file_relative_path(__file__, "pass_env.yaml")]
            ),
            PresetDefinition(
                "subset",
                solid_selection=["can_fail"],
            ),
        ],
    )

    with pytest.raises(DagsterInvariantViolationError):
        PresetDefinition.from_files(
            "invalid_1", config_files=[file_relative_path(__file__, "not_a_file.yaml")]
        )

    with pytest.raises(DagsterInvariantViolationError):
        PresetDefinition.from_files(
            "invalid_2",
            config_files=[file_relative_path(__file__, "test_repository_definition.py")],
        )

    assert execute_pipeline(pipe, preset="passing").success

    assert execute_pipeline(pipe, preset="passing_direct_dict").success
    assert execute_pipeline(pipe, preset="failing_1", raise_on_error=False).success == False

    assert execute_pipeline(pipe, preset="failing_2", raise_on_error=False).success == False

    with pytest.raises(DagsterInvariantViolationError, match="Could not find preset"):
        execute_pipeline(pipe, preset="not_failing", raise_on_error=False)

    assert (
        execute_pipeline(pipe, preset="passing_overide_to_fail", raise_on_error=False).success
        == False
    )

    assert execute_pipeline(
        pipe,
        preset="passing",
        run_config={"solids": {"can_fail": {"config": {"error": False}}}},
    ).success

    with pytest.raises(
        check.CheckError,
        match=re.escape(
            "The environment set in preset 'passing' does not agree with the environment passed "
            "in the `run_config` argument."
        ),
    ):
        execute_pipeline(
            pipe,
            preset="passing",
            run_config={"solids": {"can_fail": {"config": {"error": True}}}},
        )

    assert execute_pipeline(
        pipe,
        preset="subset",
        run_config={"solids": {"can_fail": {"config": {"error": False}}}},
    ).success


def test_invalid_preset():
    @lambda_solid
    def lil_solid():
        return ";)"

    with pytest.raises(DagsterInvalidDefinitionError, match='mode "mode_b" which is not defined'):
        PipelineDefinition(
            name="preset_modes",
            solid_defs=[lil_solid],
            mode_defs=[ModeDefinition(name="mode_a")],
            preset_defs=[PresetDefinition(name="preset_b", mode="mode_b")],
        )


def test_conflicting_preset():
    @lambda_solid
    def lil_solid():
        return ";)"

    with pytest.raises(
        DagsterInvalidDefinitionError, match="Two PresetDefinitions seen with the name"
    ):
        PipelineDefinition(
            name="preset_modes",
            solid_defs=[lil_solid],
            mode_defs=[ModeDefinition(name="mode_a")],
            preset_defs=[
                PresetDefinition(name="preset_a", mode="mode_a"),
                PresetDefinition(name="preset_a", mode="mode_a"),
            ],
        )


def test_from_yaml_strings():
    a = """
foo:
  bar: 1
baz: 3
"""
    b = """
foo:
  one: "one"
other: 4
"""
    c = """
final: "result"
"""
    preset = PresetDefinition.from_yaml_strings("passing", [a, b, c])
    assert preset.run_config == {
        "foo": {"bar": 1, "one": "one"},
        "baz": 3,
        "other": 4,
        "final": "result",
    }
    with pytest.raises(
        DagsterInvariantViolationError, match="Encountered error attempting to parse yaml"
    ):
        PresetDefinition.from_yaml_strings("failing", ["--- `"])

    res = PresetDefinition.from_yaml_strings("empty")
    assert res == PresetDefinition(
        name="empty", run_config={}, solid_selection=None, mode="default"
    )


def test_from_pkg_resources():
    good = ("dagster_tests.core_tests.definitions_tests", "pass_env.yaml")
    res = PresetDefinition.from_pkg_resources("this_should_pass", [good])
    assert res.run_config == {"solids": {"can_fail": {"config": {"error": False}}}}

    bad_defs = [
        ("dagster_tests.core_tests.definitions_tests", "does_not_exist.yaml"),
        ("dagster_tests.core_tests.definitions_tests", "bad_file_binary.yaml"),
        ("dagster_tests.core_tests.does_not_exist", "some_file.yaml"),
    ]

    for bad_def in bad_defs:
        with pytest.raises(
            DagsterInvariantViolationError,
            match="Encountered error attempting to parse yaml",
        ):
            PresetDefinition.from_pkg_resources("bad_def", [bad_def])


def test_tags():
    @lambda_solid
    def a_solid():
        return "solid"

    @pipeline(
        tags={"pipeline_tag": "pipeline_tag", "all": "pipeline", "defs": "pipeline"},
        preset_defs=[
            PresetDefinition(
                name="a_preset",
                tags={"preset_tag": "preset_tag", "all": "preset", "defs": "preset"},
            )
        ],
    )
    def a_pipeline():
        a_solid()

    instance = DagsterInstance.ephemeral()
    result = execute_pipeline(
        a_pipeline,
        instance=instance,
        preset="a_preset",
        tags={"execute_tag": "execute_tag", "all": "execute"},
    )
    assert result.success
    pipeline_run = instance.get_run_by_id(result.run_id)

    assert "pipeline_tag" in pipeline_run.tags
    assert "preset_tag" in pipeline_run.tags
    assert "execute_tag" in pipeline_run.tags

    # execute overwrites preset overwrites pipeline def
    assert "all" in pipeline_run.tags
    assert pipeline_run.tags["all"] == "execute"

    # preset overwrites pipeline def
    assert "defs" in pipeline_run.tags
    assert pipeline_run.tags["defs"] == "preset"
