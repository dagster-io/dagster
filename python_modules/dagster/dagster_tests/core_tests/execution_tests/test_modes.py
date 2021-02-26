import pytest
from dagster import (
    DagsterInvariantViolationError,
    ModeDefinition,
    execute_pipeline,
    pipeline,
    resource,
    solid,
)


@resource
def add_one_resource(_):
    def add_one(num):
        return num + 1

    return add_one


@resource
def add_two_resource(_):
    def add_two(num):
        return num + 2

    return add_two


@solid(required_resource_keys={"adder"})
def solid_that_uses_adder_resource(context, number):
    return context.resources.adder(number)


@pipeline(
    mode_defs=[
        ModeDefinition(name="add_one", resource_defs={"adder": add_one_resource}),
        ModeDefinition(name="add_two", resource_defs={"adder": add_two_resource}),
    ]
)
def pipeline_with_mode():
    solid_that_uses_adder_resource()


def test_execute_pipeline_with_mode():
    pipeline_result = execute_pipeline(
        pipeline_with_mode,
        run_config={
            "solids": {"solid_that_uses_adder_resource": {"inputs": {"number": {"value": 4}}}}
        },
        mode="add_one",
    )
    assert pipeline_result.success
    assert pipeline_result.result_for_solid("solid_that_uses_adder_resource").output_value() == 5

    pipeline_result = execute_pipeline(
        pipeline_with_mode,
        run_config={
            "solids": {"solid_that_uses_adder_resource": {"inputs": {"number": {"value": 4}}}}
        },
        mode="add_two",
    )
    assert pipeline_result.success
    assert pipeline_result.result_for_solid("solid_that_uses_adder_resource").output_value() == 6


def test_execute_pipeline_with_non_existant_mode():
    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(
            pipeline_with_mode,
            mode="BAD",
            run_config={
                "solids": {"solid_that_uses_adder_resource": {"inputs": {"number": {"value": 4}}}}
            },
        )


@solid
def solid_that_gets_tags(context):
    return context.pipeline_run.tags


@pipeline(
    mode_defs=[
        ModeDefinition(name="tags"),
    ],
    tags={"tag_key": "tag_value"},
)
def pipeline_with_one_mode_and_tags():
    solid_that_gets_tags()


def test_execute_pipeline_with_mode_and_tags():
    pipeline_result = execute_pipeline(pipeline_with_one_mode_and_tags)
    assert pipeline_result.success
    assert pipeline_result.result_for_solid("solid_that_gets_tags").output_value() == {
        "tag_key": "tag_value"
    }


@pipeline(
    mode_defs=[
        ModeDefinition(name="tags_1"),
        ModeDefinition(name="tags_2"),
        ModeDefinition(name="tags_3"),
    ],
    tags={"pipeline_tag_key": "pipeline_tag_value"},
)
def pipeline_with_multi_mode_and_tags():
    solid_that_gets_tags()


def test_execute_pipeline_with_multi_mode_and_pipeline_def_tags():
    pipeline_result = execute_pipeline(pipeline_with_multi_mode_and_tags, mode="tags_1")
    assert pipeline_result.success
    assert pipeline_result.result_for_solid("solid_that_gets_tags").output_value() == {
        "pipeline_tag_key": "pipeline_tag_value"
    }


def test_execute_pipeline_with_multi_mode_and_pipeline_def_tags_and_execute_tags():
    pipeline_result = execute_pipeline(
        pipeline_with_multi_mode_and_tags,
        mode="tags_1",
        tags={"run_tag_key": "run_tag_value"},
    )
    assert pipeline_result.success
    assert pipeline_result.result_for_solid("solid_that_gets_tags").output_value() == {
        "pipeline_tag_key": "pipeline_tag_value",
        "run_tag_key": "run_tag_value",
    }
